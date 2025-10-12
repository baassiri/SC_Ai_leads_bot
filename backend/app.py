"""
SC AI Lead Generation System - FULLY INTEGRATED Flask Application
Complete workflow: Upload Targets → Start Bot → Scrape Leads → AI Score → Display in UI
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from datetime import datetime
import os
import sys
import threading
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import Config, get_config
from backend.database.db_manager import db_manager

# Initialize Flask app
app = Flask(__name__,
           template_folder='../frontend/templates',
           static_folder='../frontend/static')

# Load configuration
app.config.from_object(get_config())
CORS(app, origins=Config.CORS_ORIGINS)

# Global bot status
bot_status = {
    'running': False,
    'current_activity': 'Stopped',
    'leads_scraped': 0,
    'messages_sent': 0,
    'progress': 0
}

# Background scraper thread
scraper_thread = None


# ==========================================
# HTML ROUTES (Serve Frontend Pages)
# ==========================================

@app.route('/')
def index():
    """Serve login/settings page"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Serve main dashboard"""
    return render_template('dashboard.html')


@app.route('/leads')
def leads_page():
    """Serve leads page"""
    return render_template('leads.html')


@app.route('/messages')
def messages_page():
    """Serve messages page"""
    return render_template('messages.html')


@app.route('/analytics')
def analytics_page():
    """Serve analytics page"""
    return render_template('analytics.html')


# ==========================================
# API ROUTES - AUTHENTICATION
# ==========================================

@app.route('/api/auth/save-credentials', methods=['POST'])
def save_credentials():
    """Save user credentials"""
    try:
        data = request.json
        
        linkedin_email = data.get('linkedin_email')
        linkedin_password = data.get('linkedin_password')
        openai_api_key = data.get('openai_api_key')
        
        if not all([linkedin_email, linkedin_password, openai_api_key]):
            return jsonify({
                'success': False,
                'message': 'All credentials are required'
            }), 400
        
        # Check if user exists
        user = db_manager.get_user_by_email('default@sc-leads.com')
        
        if user:
            # Update existing user
            db_manager.update_user_credentials(
                user['id'],
                linkedin_email=linkedin_email,
                linkedin_password=linkedin_password,
                openai_api_key=openai_api_key
            )
        else:
            # Create new user
            db_manager.create_user(
                email='default@sc-leads.com',
                linkedin_email=linkedin_email,
                linkedin_password=linkedin_password,
                openai_api_key=openai_api_key
            )
        
        # Log activity
        db_manager.log_activity(
            activity_type='credentials_saved',
            description='User credentials updated successfully',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': 'Credentials saved successfully!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving credentials: {str(e)}'
        }), 500


@app.route('/api/auth/test-connection', methods=['POST'])
def test_connection():
    """Test LinkedIn and OpenAI connection"""
    try:
        data = request.json
        service = data.get('service')
        
        if service == 'linkedin':
            # TODO: Implement actual LinkedIn test
            return jsonify({
                'success': True,
                'message': 'LinkedIn credentials saved! Will test on first scrape.'
            })
        elif service == 'openai':
            # TODO: Implement actual OpenAI test
            return jsonify({
                'success': True,
                'message': 'OpenAI API key saved!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid service specified'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Connection test failed: {str(e)}'
        }), 500


# ==========================================
# API ROUTES - FILE UPLOAD & PERSONA PARSING
# ==========================================

@app.route('/api/upload-targets', methods=['POST'])
def upload_targets():
    """Upload and parse Targets.docx using AI analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        if not file.filename.endswith('.docx'):
            return jsonify({
                'success': False,
                'message': 'Only .docx files are allowed'
            }), 400
        
        # Save file
        upload_path = Config.UPLOAD_DIR / file.filename
        file.save(str(upload_path))
        
        print(f"\n🤖 Using AI to analyze document: {file.filename}")
        
        # Use AI Persona Analyzer (NEW!)
        from backend.ai_engine.persona_analyzer import create_analyzer
        
        analyzer = create_analyzer()
        analysis = analyzer.analyze_document(str(upload_path))
        
        # Save personas to database
        saved_count = 0
        personas_from_ai = analysis.get('personas', [])
        
        for persona_data in personas_from_ai:
            try:
                # Create persona in database
                persona_id = db_manager.create_persona(
                    name=persona_data.get('name', 'Unknown'),
                    description=persona_data.get('description', ''),
                    goals='\n'.join(persona_data.get('goals', [])),
                    pain_points='\n'.join(persona_data.get('pain_points', [])),
                    message_tone=', '.join(persona_data.get('keywords', [])[:5])
                )
                
                if persona_id:
                    saved_count += 1
                    print(f"  ✅ Saved persona: {persona_data.get('name')}")
                    
            except Exception as e:
                print(f"  ⚠️  Error saving persona: {str(e)}")
                continue
        
        # Get all personas from database
        personas_list = db_manager.get_all_personas()
        
        # Store the LinkedIn search query for later use
        linkedin_query = analysis.get('linkedin_search_query', '')
        primary_titles = analysis.get('primary_titles', [])
        
        # Log activity
        db_manager.log_activity(
            activity_type='file_upload',
            description=f'AI analyzed document: {file.filename} - Found {len(personas_from_ai)} personas',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'AI analyzed successfully! {len(personas_list)} personas loaded ({saved_count} new).',
            'personas_count': len(personas_list),
            'personas': personas_list,
            'ai_analysis': {
                'linkedin_query': linkedin_query,
                'primary_titles': primary_titles,
                'found_personas': len(personas_from_ai)
            }
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in upload_targets: {error_details}")
        
        return jsonify({
            'success': False,
            'message': f'Error uploading file: {str(e)}'
        }), 500

# ==========================================
# API ROUTES - BOT CONTROL (THE MAGIC HAPPENS HERE!)
# ==========================================

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the lead scraping bot - FULLY INTEGRATED"""
    global bot_status, scraper_thread
    
    try:
        if bot_status['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is already running'
            }), 400
        
        # Get user credentials
        user = db_manager.get_user_by_email('default@sc-leads.com')
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Please configure your LinkedIn credentials in Settings first!'
            }), 400
        
        # Get credentials from database
        from backend.database.db_manager import DatabaseManager
        db = DatabaseManager()
        with db.session_scope() as session:
            from backend.database.models import User
            user_obj = session.query(User).filter(User.email == 'default@sc-leads.com').first()
            
            if not user_obj or not user_obj.linkedin_email or not user_obj.linkedin_password:
                return jsonify({
                    'success': False,
                    'message': 'LinkedIn credentials not found. Please configure in Settings!'
                }), 400
            
            linkedin_email = user_obj.linkedin_email
            linkedin_password = user_obj.linkedin_password
        
        # Update bot status
        bot_status['running'] = True
        bot_status['current_activity'] = 'Initializing...'
        bot_status['leads_scraped'] = 0
        bot_status['progress'] = 0
        
        # Log start
        db_manager.log_activity(
            activity_type='bot_started',
            description='Lead scraping bot started',
            status='success'
        )
        
        # Define the background scraping function
        def scrape_leads_background():
            global bot_status
            
            try:
                # Import scraper
                from backend.scrapers.linkedin_scraper import LinkedInScraper
                
                bot_status['current_activity'] = 'Setting up Chrome browser...'
                bot_status['progress'] = 10
                
                # Create scraper instance
                scraper = LinkedInScraper(
                    email=linkedin_email,
                    password=linkedin_password,
                    headless=True  # Run in background
                )
                
                bot_status['current_activity'] = 'Logging into LinkedIn...'
                bot_status['progress'] = 20
                
                # Define search filters
                filters = {
                    'keywords': 'plastic surgeon dermatologist med spa owner aesthetic nurse',
                    'locations': ['United States']
                }
                
                bot_status['current_activity'] = 'Searching for leads...'
                bot_status['progress'] = 40
                
                # Scrape leads (1 page = ~25 leads)
                leads = scraper.scrape_leads(filters, max_pages=1)
                
                bot_status['current_activity'] = f'Found {len(leads)} leads! Saving to database...'
                bot_status['progress'] = 70
                bot_status['leads_scraped'] = len(leads)
                
                # Leads are automatically saved by the scraper
                
                bot_status['current_activity'] = f'Complete! {len(leads)} leads ready for review'
                bot_status['progress'] = 100
                
                # Log success
                db_manager.log_activity(
                    activity_type='scrape',
                    description=f'Successfully scraped {len(leads)} leads from LinkedIn',
                    status='success'
                )
                
                # Wait a bit before stopping
                time.sleep(3)
                bot_status['running'] = False
                
            except Exception as e:
                bot_status['current_activity'] = f'Error: {str(e)}'
                bot_status['running'] = False
                bot_status['progress'] = 0
                
                db_manager.log_activity(
                    activity_type='scrape',
                    description=f'Error during scraping: {str(e)}',
                    status='failed',
                    error_message=str(e)
                )
        
        # Start scraping in background thread
        scraper_thread = threading.Thread(target=scrape_leads_background, daemon=True)
        scraper_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Bot started! Scraping leads...',
            'status': bot_status
        })
        
    except Exception as e:
        bot_status['running'] = False
        bot_status['current_activity'] = 'Stopped'
        
        import traceback
        error_details = traceback.format_exc()
        print(f"Error starting bot: {error_details}")
        
        return jsonify({
            'success': False,
            'message': f'Error starting bot: {str(e)}'
        }), 500


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the lead scraping bot"""
    global bot_status
    
    try:
        if not bot_status['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is not running'
            }), 400
        
        # Update status
        bot_status['running'] = False
        bot_status['current_activity'] = 'Stopped by user'
        bot_status['progress'] = 0
        
        # Log stop
        db_manager.log_activity(
            activity_type='bot_stopped',
            description='Lead scraping bot stopped by user',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': 'Bot stopped successfully!',
            'status': bot_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping bot: {str(e)}'
        }), 500


@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Get current bot status"""
    return jsonify({
        'success': True,
        'status': bot_status
    })


# ==========================================
# API ROUTES - LEADS
# ==========================================

@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads with optional filters"""
    try:
        status = request.args.get('status')
        min_score = request.args.get('min_score', type=float)
        persona_id = request.args.get('persona_id', type=int)
        limit = request.args.get('limit', type=int)
        
        leads = db_manager.get_all_leads(
            status=status,
            min_score=min_score,
            persona_id=persona_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'leads': leads,
            'total': len(leads)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching leads: {str(e)}'
        }), 500


@app.route('/api/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get single lead by ID"""
    try:
        lead = db_manager.get_lead_by_id(lead_id)
        
        if not lead:
            return jsonify({
                'success': False,
                'message': 'Lead not found'
            }), 404
        
        return jsonify({
            'success': True,
            'lead': lead
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching lead: {str(e)}'
        }), 500


@app.route('/api/leads/<int:lead_id>/archive', methods=['POST'])
def archive_lead(lead_id):
    """Archive a lead"""
    try:
        success = db_manager.update_lead_status(lead_id, status='archived')
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Lead archived successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Lead not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error archiving lead: {str(e)}'
        }), 500


# ==========================================
# API ROUTES - PERSONAS
# ==========================================

@app.route('/api/personas', methods=['GET'])
def get_personas():
    """Get all personas"""
    try:
        personas = db_manager.get_all_personas()
        
        return jsonify({
            'success': True,
            'personas': personas,
            'total': len(personas)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching personas: {str(e)}'
        }), 500


# ==========================================
# API ROUTES - ANALYTICS
# ==========================================

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = db_manager.get_dashboard_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching analytics: {str(e)}'
        }), 500


@app.route('/api/leads-by-persona', methods=['GET'])
def get_leads_by_persona():
    """Get lead distribution by persona"""
    try:
        data = db_manager.get_leads_by_persona()
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching persona data: {str(e)}'
        }), 500


# ==========================================
# API ROUTES - ACTIVITY LOGS
# ==========================================

@app.route('/api/activity-logs', methods=['GET'])
def get_activity_logs():
    """Get recent activity logs"""
    try:
        limit = request.args.get('limit', 50, type=int)
        logs = db_manager.get_recent_activities(limit=limit)
        
        logs_data = [{
            'id': log.id,
            'activity_type': log.activity_type,
            'description': log.description,
            'status': log.status,
            'created_at': log.created_at.isoformat()
        } for log in logs]
        
        return jsonify({
            'success': True,
            'logs': logs_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching activity logs: {str(e)}'
        }), 500


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SC AI Lead Generation System - FULLY INTEGRATED")
    print("=" * 60)
    print("\n📋 WORKFLOW:")
    print("1. Visit http://localhost:5000 → Configure LinkedIn credentials")
    print("2. Upload Targets.docx → AI analyzes personas")
    print("3. Click 'Start' → Bot scrapes LinkedIn for leads")
    print("4. View leads at http://localhost:5000/leads")
    print("5. Generate AI messages (coming next)")
    print("\n" + "=" * 60)
    print("🌐 Server URLs:")
    print("=" * 60)
    print(f"📊 Dashboard: http://localhost:5000/dashboard")
    print(f"🎯 Leads: http://localhost:5000/leads")
    print(f"✉️  Messages: http://localhost:5000/messages")
    print(f"📈 Analytics: http://localhost:5000/analytics")
    print(f"⚙️  Settings: http://localhost:5000/")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )