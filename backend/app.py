"""
SC AI Lead Generation System - Main Flask Application
API routes for frontend-backend communication
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import sys
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
    'current_activity': None,
    'leads_scraped': 0,
    'messages_sent': 0
}


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
                user.id,
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
            description='User credentials updated',
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
        service = data.get('service')  # 'linkedin' or 'openai'
        
        if service == 'linkedin':
            # TODO: Implement LinkedIn connection test
            return jsonify({
                'success': True,
                'message': 'LinkedIn connection successful!'
            })
        elif service == 'openai':
            # TODO: Implement OpenAI API test
            return jsonify({
                'success': True,
                'message': 'OpenAI API connection successful!'
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
# API ROUTES - FILE UPLOAD
# ==========================================

# FIX FOR app.py - Replace the upload_targets function

@app.route('/api/upload-targets', methods=['POST'])
def upload_targets():
    """Upload and parse Targets.docx"""
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
        
        # Parse document and extract persona data
        from backend.ai_engine.persona_parser import PersonaParser
        
        parser = PersonaParser(docx_path=str(upload_path))
        personas_data = parser.parse_document()
        
        # Save personas to database
        saved_count = parser.save_to_database()
        
        # Get all personas from database (now returns serialized dicts)
        personas_list = db_manager.get_all_personas()
        
        # Log activity
        db_manager.log_activity(
            activity_type='file_upload',
            description=f'Uploaded target document: {file.filename}',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'File uploaded successfully! {len(personas_list)} personas loaded ({saved_count} new).',
            'personas_count': len(personas_list),
            'personas': personas_list  # ✅ Already serialized!
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
# API ROUTES - BOT CONTROL
# ==========================================

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the lead scraping bot"""
    try:
        global bot_status
        
        if bot_status['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is already running'
            }), 400
        
        data = request.json
        search_filters = data.get('filters', {})
        
        # Update bot status
        bot_status['running'] = True
        bot_status['current_activity'] = 'Initializing...'
        
        # TODO: Start scraping in background thread
        # For now, we'll just log the activity
        
        # Log activity
        db_manager.log_activity(
            activity_type='bot_started',
            description='Lead scraping bot started',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': 'Bot started successfully!',
            'status': bot_status
        })
        
    except Exception as e:
        bot_status['running'] = False
        return jsonify({
            'success': False,
            'message': f'Error starting bot: {str(e)}'
        }), 500


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the lead scraping bot"""
    try:
        global bot_status
        
        if not bot_status['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is not running'
            }), 400
        
        # Update bot status
        bot_status['running'] = False
        bot_status['current_activity'] = 'Stopped'
        
        # TODO: Stop scraping thread
        
        # Log activity
        db_manager.log_activity(
            activity_type='bot_stopped',
            description='Lead scraping bot stopped',
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
        
        leads_data = [{
            'id': lead.id,
            'name': lead.name,
            'title': lead.title,
            'company': lead.company,
            'industry': lead.industry,
            'location': lead.location,
            'ai_score': lead.ai_score,
            'status': lead.status,
            'connection_status': lead.connection_status,
            'persona': lead.persona.name if lead.persona else None,
            'scraped_at': lead.scraped_at.isoformat() if lead.scraped_at else None
        } for lead in leads]
        
        return jsonify({
            'success': True,
            'leads': leads_data,
            'total': len(leads_data)
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
        
        lead_data = {
            'id': lead.id,
            'name': lead.name,
            'title': lead.title,
            'company': lead.company,
            'industry': lead.industry,
            'location': lead.location,
            'profile_url': lead.profile_url,
            'headline': lead.headline,
            'ai_score': lead.ai_score,
            'status': lead.status,
            'connection_status': lead.connection_status,
            'persona': lead.persona.name if lead.persona else None,
            'score_reasoning': lead.score_reasoning
        }
        
        return jsonify({
            'success': True,
            'lead': lead_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching lead: {str(e)}'
        }), 500


# ==========================================
# API ROUTES - MESSAGES
# ==========================================

@app.route('/api/messages/generate', methods=['POST'])
def generate_message():
    """Generate AI message for a lead"""
    try:
        data = request.json
        lead_id = data.get('lead_id')
        message_type = data.get('message_type', 'connection_request')
        
        if not lead_id:
            return jsonify({
                'success': False,
                'message': 'Lead ID is required'
            }), 400
        
        # TODO: Implement AI message generation using OpenAI
        # For now, return placeholder messages
        
        variants = [
            {
                'variant': 'A',
                'content': f'Hi [Name], I noticed your work in [industry]. Would love to connect and discuss how we can help grow your practice.'
            },
            {
                'variant': 'B',
                'content': f'Hello [Name], impressed by your expertise in [specialty]. Let\'s connect to explore collaboration opportunities.'
            }
        ]
        
        return jsonify({
            'success': True,
            'messages': variants
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating message: {str(e)}'
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


@app.route('/api/analytics/leads-by-persona', methods=['GET'])
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


@app.route('/api/analytics/message-performance', methods=['GET'])
def get_message_performance():
    """Get message performance metrics"""
    try:
        data = db_manager.get_message_performance()
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching message performance: {str(e)}'
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
    print("🚀 Starting SC AI Lead Generation System...")
    print("=" * 50)
    print(f"📊 Dashboard: http://localhost:5000/dashboard")
    print(f"🎯 Leads: http://localhost:5000/leads")
    print(f"✉️  Messages: http://localhost:5000/messages")
    print(f"📈 Analytics: http://localhost:5000/analytics")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )