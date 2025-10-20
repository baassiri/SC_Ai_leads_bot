"""
SC AI Lead Generation System - Clean Dynamic Backend
Works only with uploaded documents - no hardcoded personas
FIXED: Clean AB test routes, no duplicates, cooldown manager integrated
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import threading
import time
import random
from pathlib import Path
import sys
# Fix import paths - add project root to path FIRST
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai_engine.message_generator_abc import ABCMessageGenerator
from backend.automation.scheduler import scheduler as message_scheduler
from backend.config import Config, get_config
from backend.api.missing_endpoints import register_missing_endpoints
from backend.database.db_manager import db_manager
from backend.credentials_manager import credentials_manager
from backend.scraping_cooldown_manager import get_cooldown_manager
from backend.linkedin.linkedin_sender import LinkedInSender
app = Flask(__name__,
           template_folder='../frontend/templates',
           static_folder='../frontend/static')

app.config.from_object(get_config())
CORS(app, origins=Config.CORS_ORIGINS)

bot_status = {
    'running': False,
    'current_activity': 'Stopped',
    'leads_scraped': 0,
    'progress': 0
}
# Register missing endpoints to fix frontend integration
register_missing_endpoints(app, db_manager, credentials_manager)

current_personas = []
scraper_thread = None

# ============================================================================
# HTML ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/leads')
def leads_page():
    return render_template('leads.html')

@app.route('/messages')
def messages_page():
    return render_template('messages.html')

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')

@app.route('/settings')
def settings_page():
    """Render settings page"""
    return render_template('settings.html')

@app.route('/ab-analytics')
def ab_analytics_page():
    """Render AB test analytics page"""
    return render_template('ab_test_analytics.html')

# ============================================================================
# API ROUTES - AUTHENTICATION
# ============================================================================

@app.route('/api/auth/save-credentials', methods=['POST'])
def save_credentials():
    try:
        data = request.json
        
        linkedin_email = data.get('linkedin_email', '').strip()
        linkedin_password = data.get('linkedin_password', '').strip()
        openai_api_key = data.get('openai_api_key', '').strip()
        sales_nav_enabled = data.get('sales_nav_enabled', False)
        
        if not all([linkedin_email, linkedin_password, openai_api_key]):
            return jsonify({
                'success': False,
                'message': 'All credentials are required'
            }), 400
        
        success = credentials_manager.save_all_credentials(
            linkedin_email=linkedin_email,
            linkedin_password=linkedin_password,
            openai_api_key=openai_api_key,
            sales_nav_enabled=sales_nav_enabled
        )
        
        if success:
            nav_type = "Sales Navigator" if sales_nav_enabled else "Regular LinkedIn"
            db_manager.log_activity(
                activity_type='credentials_saved',
                description=f'User credentials updated successfully (Using: {nav_type})',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': f'Credentials saved successfully! Using {nav_type}'
            })
        
        return jsonify({
            'success': False,
            'message': 'Failed to save credentials'
        }), 500
        
    except Exception as e:
        print(f"Error saving credentials: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/settings/save', methods=['POST'])
def save_settings_alias():
    """Alias route for settings page compatibility"""
    return save_credentials()

@app.route('/api/settings/test', methods=['POST'])
def test_settings_alias():
    """Alias for test connection"""
    return test_connection()

@app.route('/api/auth/test-connection', methods=['POST'])
def test_connection():
    try:
        data = request.json
        service = data.get('service')
        
        if service == 'linkedin':
            linkedin_creds = credentials_manager.get_linkedin_credentials()
            
            if not linkedin_creds:
                return jsonify({
                    'success': False,
                    'message': 'No LinkedIn credentials found.'
                }), 400
            
            return jsonify({
                'success': True,
                'message': f'LinkedIn credentials configured for {linkedin_creds["email"]}'
            })
            
        elif service == 'openai':
            api_key = credentials_manager.get_openai_key()
            
            if not api_key:
                return jsonify({
                    'success': False,
                    'message': 'No OpenAI API key found.'
                }), 400
            
            return jsonify({
                'success': True,
                'message': f'OpenAI API key configured'
            })
            
        return jsonify({
            'success': False,
            'message': 'Invalid service'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# NOTE: /api/auth/check-credentials is registered by register_missing_endpoints()
# No duplicate definition needed here

# ============================================================================
# API ROUTES - FILE UPLOAD
# ============================================================================

@app.route('/api/upload-targets', methods=['POST'])
def upload_targets():
    """Upload and parse target document with AI"""
    global current_personas
    
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
        
        upload_path = Config.UPLOAD_DIR / file.filename
        file.save(str(upload_path))
        
        api_key = credentials_manager.get_openai_key()
        
        from backend.ai_engine.persona_analyzer import create_analyzer
        
        analyzer = create_analyzer(api_key=api_key)
        analysis = analyzer.analyze_document(str(upload_path))
        
        current_personas = []
        personas_from_ai = analysis.get('personas', [])
        personas_saved = 0
        
        for persona_data in personas_from_ai:
            try:
                # ✅ Convert lists to strings for database storage
                goals_str = '\n'.join(persona_data.get('goals', [])) if isinstance(persona_data.get('goals'), list) else str(persona_data.get('goals', ''))
                pain_points_str = '\n'.join(persona_data.get('pain_points', [])) if isinstance(persona_data.get('pain_points'), list) else str(persona_data.get('pain_points', ''))
                
                # ✅ NEW: Extract enhanced fields
                job_titles_str = '\n'.join(persona_data.get('job_titles', [])) if isinstance(persona_data.get('job_titles'), list) else ''
                decision_makers_str = '\n'.join(persona_data.get('decision_maker_roles', [])) if isinstance(persona_data.get('decision_maker_roles'), list) else ''
                company_types_str = '\n'.join(persona_data.get('company_types', [])) if isinstance(persona_data.get('company_types'), list) else ''
                solutions_str = '\n'.join(persona_data.get('solutions', [])) if isinstance(persona_data.get('solutions'), list) else ''
                linkedin_keywords_str = '\n'.join(persona_data.get('linkedin_keywords', [])) if isinstance(persona_data.get('linkedin_keywords'), list) else ''
                message_hooks_str = '\n'.join(persona_data.get('message_hooks', [])) if isinstance(persona_data.get('message_hooks'), list) else ''
                
                existing = db_manager.get_persona_by_name(persona_data.get('name', 'Unknown'))
                
                if not existing:
                    persona_id = db_manager.create_persona(
                        name=persona_data.get('name', 'Unknown'),
                        description=persona_data.get('description', ''),
                        goals=goals_str,
                        pain_points=pain_points_str,
                        key_message=persona_data.get('key_message'),
                        message_tone=persona_data.get('message_tone'),
                        # ✅ NEW: Enhanced fields
                        job_titles=job_titles_str,
                        decision_maker_roles=decision_makers_str,
                        company_types=company_types_str,
                        solutions=solutions_str,
                        linkedin_keywords=linkedin_keywords_str,
                        smart_search_query=persona_data.get('smart_search_query'),
                        message_hooks=message_hooks_str,
                        seniority_level=persona_data.get('seniority_level'),
                        industry_focus=analysis.get('industry_focus')
                    )
                    
                    if persona_id:
                        current_personas.append(persona_data)
                        personas_saved += 1
                        
                        db_manager.log_activity(
                            activity_type='file_upload',
                            description=f"✅ Extracted persona: {persona_data.get('name')}",
                            status='success'
                        )
                else:
                    print(f"Persona '{persona_data.get('name')}' already exists, skipping")
                    
            except Exception as e:
                print(f"Error saving persona: {str(e)}")
                continue
        
        personas_list = db_manager.get_all_personas()
        
        db_manager.log_activity(
            activity_type='file_upload',
            description=f'🎯 AI analyzed {file.filename} and extracted {personas_saved} new personas',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'✅ AI extracted {personas_saved} personas! Ready to generate leads.',
            'personas_count': len(personas_list),
            'personas': personas_list,
            'personas_saved': personas_saved,
            'ai_analysis': analysis
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in upload_targets: {error_details}")
        
        db_manager.log_activity(
            activity_type='file_upload',
            description=f'❌ Error analyzing document: {str(e)}',
            status='failed',
            error_message=str(e)
        )
        
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    
# ============================================================================
# API ROUTES - BOT CONTROL
# ============================================================================

def generate_lead_from_persona(persona):
    """Generate a realistic lead from a persona"""
    first_names = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn', 'Sam', 'Drew']
    last_names = ['Chen', 'Patel', 'Kim', 'Martinez', 'Johnson', 'Williams', 'Lee', 'Garcia', 'Brown', 'Davis']
    
    job_titles = persona.get('job_titles', [])
    if not job_titles:
        job_titles = [persona.get('name', 'Professional')]
    
    title = random.choice(job_titles)
    
    industries = persona.get('industries', ['Business Services'])
    industry = random.choice(industries)
    
    company_prefixes = ['Global', 'Prime', 'Elite', 'Next', 'Pro', 'Bright']
    company_suffixes = ['Solutions', 'Group', 'Partners', 'Labs', 'Inc', 'Co']
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    company = f"{random.choice(company_prefixes)} {random.choice(company_suffixes)}"
    
    locations = ['New York, NY', 'San Francisco, CA', 'Austin, TX', 'Chicago, IL', 'Boston, MA']
    
    return {
        'name': f"{first} {last}",
        'title': title,
        'company': company,
        'industry': industry,
        'location': random.choice(locations),
        'profile_url': f'https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(100,999)}',
        'headline': f"{title} at {company}",
        'company_size': random.choice(['1-10', '11-50', '51-200', '201-500']) + ' employees',
        'score': random.randint(70, 98)
    }

# ============================================================================
# CHANGE 2: REPLACE start_bot() WITH COOLDOWN-ENABLED VERSION
# ============================================================================


@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the REAL lead scraping bot with cooldown enforcement"""
    global bot_status, scraper_thread
    
    try:
        if bot_status['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is already running'
            }), 400
        
        # Check scraping cooldown
        cooldown_manager = get_cooldown_manager()
        can_scrape, cooldown_message, details = cooldown_manager.check_can_scrape()
        
        if not can_scrape:
            return jsonify({
                'success': False,
                'message': cooldown_message,
                'cooldown_active': True,
                'details': details
            }), 429
        
        personas = db_manager.get_all_personas()
        
        if not personas:
            return jsonify({
                'success': False,
                'message': 'No personas found! Please upload a document first.'
            }), 400
        
        linkedin_creds = credentials_manager.get_linkedin_credentials()
        
        if not linkedin_creds:
            return jsonify({
                'success': False,
                'message': 'Please configure LinkedIn credentials first!'
            }), 400
        
        bot_status['running'] = True
        bot_status['current_activity'] = 'Initializing...'
        bot_status['leads_scraped'] = 0
        bot_status['progress'] = 0
        
        db_manager.log_activity(
            activity_type='bot_started',
            description='REAL LinkedIn scraping started',
            status='success'
        )
        
        # GET REQUEST DATA BEFORE THREAD STARTS
        request_data = request.json or {}
        target_profile_from_ui = request_data.get('target_profile', '').strip()
        
        def scrape_leads_background():
            """REAL LINKEDIN SCRAPING with cooldown recording"""
            global bot_status
            
            try:
                from backend.scrapers.linkedin_scraper import LinkedInScraper
                from backend.ai_engine.lead_scorer import score_lead
                
                linkedin_creds = credentials_manager.get_linkedin_credentials()
                api_key = credentials_manager.get_openai_key()
                personas = db_manager.get_all_personas()
                
                # ✅ FIX: Verify credentials exist
                if not linkedin_creds:
                    raise Exception("LinkedIn credentials not found. Please configure in Settings.")
                
                bot_status['current_activity'] = 'Connecting to LinkedIn...'
                bot_status['progress'] = 10
                
                # ✅ FIX: Use credentials from credentials_manager
                scraper = LinkedInScraper(
                    email=linkedin_creds['email'],
                    password=linkedin_creds['password'],
                    headless=False,
                    sales_nav_preference=False  # Prevents hanging
                )
                
                bot_status['current_activity'] = 'Setting up Chrome...'
                bot_status['progress'] = 20
                
                if not scraper.setup_driver():
                    raise Exception("Failed to setup Chrome")
                
                bot_status['current_activity'] = 'Logging into LinkedIn...'
                bot_status['progress'] = 30
                
                if not scraper.login():
                    raise Exception("Login failed")
                
                bot_status['current_activity'] = 'Login successful!'
                bot_status['progress'] = 40
                
                # Use target profile from UI if provided
                # ✅ Use target profile from UI if provided
                if target_profile_from_ui:
                    search_keyword = target_profile_from_ui
                    print(f"🎯 Using target profile from UI: {target_profile_from_ui}")
                elif personas and len(personas) > 0:
                    # ✅ NEW: Use smart_search_query from persona analyzer
                    persona = personas[0]
                    
                    # Try to get smart_search_query first (enhanced field)
                    search_keyword = persona.get('smart_search_query')
                    
                    if search_keyword:
                        print(f"🤖 Using AI-generated search: {search_keyword}")
                    else:
                        # Fallback to old logic if smart_search_query not available
                        persona_name = persona.get('name', '').lower()
                        
                        if 'founder' in persona_name or 'sme' in persona_name:
                            search_keyword = 'CEO founder'
                        elif 'consultant' in persona_name or 'coach' in persona_name:
                            search_keyword = 'consultant coach advisor'
                        elif 'marketing' in persona_name:
                            search_keyword = 'marketing director'
                        else:
                            search_keyword = 'CEO founder director'
                        
                        print(f"📋 Using persona fallback: {search_keyword}")
                else:
                    search_keyword = 'CEO founder'
                    print(f"⚠️ Using default: {search_keyword}")
                
                bot_status['current_activity'] = f'Searching: {search_keyword}'
                bot_status['progress'] = 50
                
                # REAL SCRAPING
                scraped_leads = scraper.scrape_leads(
                    filters={'keywords': search_keyword},
                    max_pages=10
                )
                
                if not scraped_leads:
                    raise Exception("No leads found")
                
                bot_status['current_activity'] = f'Found {len(scraped_leads)} leads!'
                bot_status['progress'] = 70
                
                # Process each lead
                successfully_imported = 0
                
                for i, lead_data in enumerate(scraped_leads, 1):
                    if not bot_status['running']:
                        break
                    
                    bot_status['current_activity'] = f'Processing {i}/{len(scraped_leads)}: {lead_data["name"]}'
                    
                    lead_id = db_manager.create_lead(
                        name=lead_data['name'],
                        profile_url=lead_data['profile_url'],
                        title=lead_data.get('title'),
                        company=lead_data.get('company'),
                        industry=lead_data.get('industry'),
                        location=lead_data.get('location'),
                        headline=lead_data.get('headline'),
                        company_size=lead_data.get('company_size')
                    )
                    
                    if lead_id:
                        try:
                            best_persona = personas[0]
                            scoring_result = score_lead(
                                lead_data=lead_data,
                                persona_data=best_persona,
                                api_key=api_key
                            )
                            
                            db_manager.update_lead_score(
                                lead_id,
                                scoring_result['score'],
                                persona_id=best_persona.get('id'),
                                score_reasoning=scoring_result['reasoning']
                            )
                            
                            successfully_imported += 1
                            bot_status['leads_scraped'] = successfully_imported
                            
                        except Exception as e:
                            print(f"AI scoring failed: {str(e)}")
                            db_manager.update_lead_score(lead_id, 75, persona_id=best_persona.get('id'))
                            successfully_imported += 1
                    
                    bot_status['progress'] = 70 + int((i / len(scraped_leads)) * 25)
                    time.sleep(0.5)
                
                # Close browser
                if scraper.driver:
                    scraper.driver.quit()
                
                # Record the scrape
                cooldown_manager = get_cooldown_manager()
                cooldown_manager.record_scrape(user_id=1, leads_scraped=successfully_imported)
                
                bot_status['current_activity'] = f'Complete! {successfully_imported} real leads scraped'
                bot_status['progress'] = 100
                
                db_manager.log_activity(
                    activity_type='scrape',
                    description=f'Scraped {successfully_imported} REAL leads',
                    status='success'
                )
                
                time.sleep(2)
                bot_status['running'] = False
                
            except Exception as e:
                bot_status['current_activity'] = f'Error: {str(e)}'
                bot_status['running'] = False
                
                db_manager.log_activity(
                    activity_type='scrape',
                    description=f'Error: {str(e)}',
                    status='failed',
                    error_message=str(e)
                )
                
                print(f"SCRAPING ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
        
        scraper_thread = threading.Thread(target=scrape_leads_background, daemon=True)
        scraper_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Bot started! {details["scrapes_remaining"]} scrapes remaining this week.',
            'status': bot_status,
            'cooldown_details': details
        })
        
    except Exception as e:
        bot_status['running'] = False
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    global bot_status
    
    bot_status['running'] = False
    bot_status['current_activity'] = 'Stopped by user'
    
    db_manager.log_activity(
        activity_type='bot_stopped',
        description='ℹ️ Lead scraping bot stopped',
        status='success'
    )
    
    return jsonify({
        'success': True,
        'message': 'Bot stopped successfully!'
    })

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    return jsonify({
        'success': True,
        'status': bot_status
    })

# ============================================================================
# API ROUTES - LEADS
# ============================================================================

@app.route('/api/leads', methods=['GET'])
def get_leads():
    try:
        status_filter = request.args.get('status')
        persona_id = request.args.get('persona_id')
        min_score = request.args.get('min_score', type=int)
        
        leads = db_manager.get_all_leads(
            status=status_filter,
            persona_id=persona_id,
            min_score=min_score,
            limit=200
        )
        
        return jsonify({
            'success': True,
            'leads': leads,
            'total': len(leads)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get a single lead by ID"""
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
            'message': f'Error: {str(e)}'
        }), 500

# ============================================================================
# API ROUTES - PERSONAS
# ============================================================================

@app.route('/api/personas', methods=['GET'])
def get_personas():
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
            'message': f'Error: {str(e)}'
        }), 500

# ============================================================================
# API ROUTES - MESSAGES
# ============================================================================

# ============================================================================
# ADD THIS TO app.py - UPDATE THE /api/messages/generate ROUTE
# Replace the existing route (around line 850) with this enhanced version
# ============================================================================

@app.route('/api/messages/generate', methods=['POST'])
def generate_messages():
    """Generate A/B/C message variants for leads (with optional template)"""
    try:
        data = request.json or {}
        lead_ids = data.get('lead_ids', [])
        template_id = data.get('template_id')  # 🎨 NEW: Optional template ID
        
        if not lead_ids:
            leads = db_manager.get_all_leads(min_score=70, limit=20)
            lead_ids = [lead['id'] for lead in leads]
        
        if not lead_ids:
            return jsonify({
                'success': False,
                'message': 'No leads found to generate messages for'
            }), 400
        
        api_key = credentials_manager.get_openai_key()
        
        if not api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key not configured'
            }), 400
        
        generator = ABCMessageGenerator(api_key=api_key)
        
        # 🎨 Pass template_id to batch_generate
        results = generator.batch_generate(
            lead_ids, 
            max_leads=20,
            template_id=template_id
        )
        
        # Enhanced logging
        log_message = f'🎨 Generated {results["messages_created"]} A/B/C message variants for {results["successful"]} leads'
        if template_id:
            template = db_manager.get_message_template(template_id)
            if template:
                log_message += f' using template: "{template["template"][:40]}..."'
        
        db_manager.log_activity(
            activity_type='message_generation',
            description=log_message,
            status='success'
        )
        
        response_message = f'Generated {results["messages_created"]} message variants'
        if results.get('template_used'):
            response_message += ' using your template!'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'results': results
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating messages: {error_details}")
        
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get messages with lead info"""
    try:
        status = request.args.get('status')
        lead_id = request.args.get('lead_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        messages = db_manager.get_messages_by_status_with_lead_info(
            status=status,
            lead_id=lead_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'messages': messages,
            'total': len(messages)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
@app.route('/api/messages/stats', methods=['GET'])
def get_message_stats():
    """Get message statistics"""
    try:
        stats = db_manager.get_message_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/leads/top', methods=['GET'])
def get_top_leads():
    """Get top qualified leads"""
    try:
        limit = request.args.get('limit', 20, type=int)
        min_score = request.args.get('min_score', 70, type=int)
        
        leads = db_manager.get_all_leads(
            min_score=min_score,
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
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/scrape/start', methods=['POST'])
def start_scrape():
    """Start scraping with smart keywords"""
    return start_bot()

@app.route('/api/messages/<int:message_id>/approve', methods=['POST'])
def approve_message(message_id):
    try:
        success = db_manager.update_message_status(message_id, 'approved')
        
        if success:
            db_manager.log_activity(
                activity_type='message_approved',
                description=f'Message {message_id} approved',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': 'Message approved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Message not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ============================================================================
# MESSAGE SCHEDULER API
# ============================================================================

@app.route('/api/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Get scheduler status"""
    try:
        status = message_scheduler.get_status()
        return jsonify({'success': True, 'scheduler': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the message scheduler"""
    try:
        message_scheduler.start()
        return jsonify({'success': True, 'message': 'Scheduler started'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the message scheduler"""
    try:
        message_scheduler.stop()
        return jsonify({'success': True, 'message': 'Scheduler stopped'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# ANALYTICS
# ============================================================================

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_stats():
    try:
        stats = db_manager.get_dashboard_stats()
        
        if stats.get('messages_sent', 0) > 0:
            stats['reply_rate'] = round((stats.get('replies_received', 0) / stats['messages_sent']) * 100, 1)
        else:
            stats['reply_rate'] = 0
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/messages/<int:message_id>/send', methods=['POST'])
def send_single_message(message_id):
    """Send a single message immediately to LinkedIn"""
    global linkedin_sender
    
    try:
        # Check if logged in
        if not linkedin_sender or not linkedin_sender.driver:
            return jsonify({
                'success': False,
                'message': 'Please login to LinkedIn first'
            }), 400
        
        # Get the message
        message = db_manager.get_message_by_id(message_id)
        
        if not message:
            return jsonify({
                'success': False,
                'message': 'Message not found'
            }), 404
        
        # Get lead info
        lead = db_manager.get_lead_by_id(message['lead_id'])
        
        if not lead:
            return jsonify({
                'success': False,
                'message': 'Lead not found'
            }), 404
        
        lead_name = lead['name']
        profile_url = lead['profile_url']
        content = message['content']
        
        print(f"\n📤 Sending to: {lead_name}")
        print(f"💬 Message: {content}")
        
        # Send the message NOW via LinkedIn
        result = linkedin_sender.send_connection_request(profile_url, content)
        
        if result["success"]:
            # Update message status to 'sent'
            db_manager.update_message_status(message_id, 'sent')
            
            # Update lead status
            db_manager.update_lead_status(lead['id'], 'contacted', 'pending')
            
            db_manager.log_activity(
                activity_type='message_sent',
                description=f'✅ Sent message to {lead_name}',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': f'Message sent to {lead_name}!'
            })
        else:
            # Mark as failed
            db_manager.update_message_status(message_id, 'failed')
            
            db_manager.log_activity(
                activity_type='message_failed',
                description=f'❌ Failed to send to {lead_name}: {result.get("error")}',
                status='failed',
                error_message=result.get("error")
            )
            
            return jsonify({
                'success': False,
                'message': f'Failed to send: {result.get("error")}'
            }), 500
        
    except Exception as e:
        import traceback
        print(f"Error sending message: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/messages/schedule-batch', methods=['POST'])
def schedule_batch_messages():
    """Schedule multiple messages with rate limiting"""
    try:
        from backend.automation.scheduler import scheduler
        
        data = request.json
        message_ids = data.get('message_ids', [])
        start_time = data.get('start_time')
        spread_hours = data.get('spread_hours', 4)
        
        if not message_ids:
            return jsonify({
                'success': False,
                'message': 'No message IDs provided'
            }), 400
        
        schedule_ids = scheduler.schedule_batch(
            message_ids=message_ids,
            start_time=start_time,
            spread_hours=spread_hours
        )
        
        db_manager.log_activity(
            activity_type='batch_scheduled',
            description=f'Scheduled {len(schedule_ids)} messages over {spread_hours} hours',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'Scheduled {len(schedule_ids)} messages',
            'schedule_ids': schedule_ids,
            'count': len(schedule_ids)
        })
        
    except Exception as e:
        import traceback
        print(f"Error scheduling batch: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a draft message"""
    try:
        success = db_manager.delete_message(message_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Message deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Message not found or cannot be deleted'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/activity-logs', methods=['GET'])
def get_activity_logs():
    try:
        limit = request.args.get('limit', 50, type=int)
        logs_data = db_manager.get_recent_activities(limit=limit)
        
        return jsonify({
            'success': True,
            'logs': logs_data
        })
        
    except Exception as e:
        import traceback
        print(f"Error in activity logs: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ============================================================================
# API ROUTES - A/B TEST ANALYTICS
# ============================================================================

@app.route('/api/ab-tests/<int:test_id>/analyze', methods=['GET'])
def analyze_ab_test(test_id):
    """Analyze A/B test and detect winner"""
    try:
        from backend.ai_engine.ab_test_analyzer import ab_analyzer
        
        result = ab_analyzer.analyze_test(test_id)
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/auto-analyze', methods=['POST'])
def auto_analyze_tests():
    """Auto-analyze all active tests and declare winners"""
    try:
        from backend.ai_engine.ab_test_analyzer import ab_analyzer
        
        results = ab_analyzer.auto_analyze_all_active_tests()
        
        for result in results:
            db_manager.log_activity(
                activity_type='ab_test_winner',
                description=f"🏆 Variant {result['winning_variant']} won with {result['confidence']:.1f}% confidence",
                status='success'
            )
        
        return jsonify({
            'success': True,
            'winners_declared': len(results),
            'results': results,
            'message': f'Analyzed tests, declared {len(results)} winner(s)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/best-practices', methods=['GET'])
def get_best_practices():
    """Get best practices from all completed tests"""
    try:
        from backend.ai_engine.ab_test_analyzer import ab_analyzer
        
        practices = ab_analyzer.get_best_practices()
        
        return jsonify({
            'success': True,
            'best_practices': practices
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/winners', methods=['GET'])
def get_all_winners():
    """Get all tests with declared winners"""
    try:
        from backend.ai_engine.ab_test_analyzer import ab_analyzer
        
        winners = ab_analyzer.get_all_winners()
        
        return jsonify({
            'success': True,
            'count': len(winners),
            'winners': winners
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/<int:test_id>/comparison', methods=['GET'])
def get_variant_comparison(test_id):
    """Get detailed comparison of all variants"""
    try:
        from backend.ai_engine.ab_test_analyzer import ab_analyzer
        
        comparison = ab_analyzer.compare_variants(test_id)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ============================================================================
# COOLDOWN API ENDPOINTS
# ============================================================================

@app.route('/api/scraping/cooldown-status', methods=['GET'])
def get_cooldown_status():
    """Get current scraping cooldown status"""
    try:
        cooldown_manager = get_cooldown_manager()
        can_scrape, message, details = cooldown_manager.check_can_scrape()
        stats = cooldown_manager.get_scraping_stats()
        
        return jsonify({
            'success': True,
            'can_scrape': can_scrape,
            'message': message,
            'details': details,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/scraping/update-limit', methods=['POST'])
def update_scraping_limit():
    """Update weekly scraping limit"""
    try:
        data = request.json
        new_limit = data.get('weekly_limit', 10)
        
        cooldown_manager = get_cooldown_manager()
        success = cooldown_manager.update_weekly_limit(new_limit)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Weekly limit updated to {new_limit} scrapes/week'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid limit (must be 0-7)'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
# LinkedIn Automation Routes
linkedin_sender = None

@app.route('/api/linkedin/login', methods=['POST'])
def linkedin_login():
    """Initiate LinkedIn login"""
    global linkedin_sender
    try:
        linkedin_sender = LinkedInSender()
        linkedin_sender.init_driver()
        
        # Try loading saved cookies first
        if linkedin_sender.load_cookies():
            return jsonify({"success": True, "message": "Logged in using saved session"})
        
        # If cookies don't work, do manual login
        success = linkedin_sender.login_manual()
        if success:
            return jsonify({"success": True, "message": "Login successful"})
        else:
            return jsonify({"success": False, "error": "Login failed"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/linkedin/send-messages', methods=['POST'])
def send_linkedin_messages():
    """Send approved messages to LinkedIn"""
    global linkedin_sender
    
    if not linkedin_sender:
        return jsonify({"success": False, "error": "Please login to LinkedIn first"}), 400
    
    try:
        # Get approved messages that haven't been sent yet
        messages_to_send = db_manager.get_messages_to_send()
        
        if not messages_to_send:
            return jsonify({"success": False, "error": "No approved messages to send"}), 400
        
        results = []
        sent_count = 0
        failed_count = 0
        
        for msg in messages_to_send:
            msg_id = msg['id']
            lead_id = msg['lead_id']
            content = msg['content']
            lead_name = msg['name']
            profile_url = msg['profile_url']
            
            # Check daily limit
            if linkedin_sender.sent_today >= linkedin_sender.daily_limit:
                results.append({
                    "lead": lead_name,
                    "status": "skipped",
                    "reason": "Daily limit reached (100 messages)"
                })
                continue
            
            print(f"\n📤 Sending to: {lead_name}")
            print(f"💬 Message: {content}")
            # Skip the pre-check - let LinkedIn automation handle connection status naturally
            # Check if already connected
            # if linkedin_sender.check_if_connected(profile_url):
            #     print(f"⚠️ Already connected to {lead_name}, skipping...")
            #     results.append({
            #         "lead": lead_name,
            #         "status": "skipped",
            #         "reason": "Already connected"
            #     })
                
            #     # Update lead status
            #     db_manager.update_lead_status(lead_id, 'contacted', 'connected')
            #     continue
            
            # Send connection request
            result = linkedin_sender.send_connection_request(profile_url, content)
            
            if result["success"]:
                # Update message status to 'sent'
                db_manager.update_message_status(msg_id, 'sent')
                
                # Update lead status to 'pending'
                db_manager.update_lead_status(lead_id, 'contacted', 'pending')
                
                sent_count += 1
                
                results.append({
                    "lead": lead_name,
                    "status": "sent",
                    "message": result["message"]
                })
                
            else:
                # Mark as failed
                db_manager.update_message_status(msg_id, 'failed')
                failed_count += 1
                
                results.append({
                    "lead": lead_name,
                    "status": "failed",
                    "error": result["error"]
                })
            
            # Random delay between sends (2-5 minutes)
            if sent_count < len(messages_to_send) - 1:
                delay = random.randint(120, 300)
                print(f"⏳ Waiting {delay//60} minutes before next message...")
                time.sleep(delay)
        
        return jsonify({
            "success": True,
            "sent": sent_count,
            "failed": failed_count,
            "skipped": len(messages_to_send) - sent_count - failed_count,
            "results": results
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/linkedin/close', methods=['POST'])
def linkedin_close():
    """Close LinkedIn browser"""
    global linkedin_sender
    if linkedin_sender:
        linkedin_sender.close()
        linkedin_sender = None
    return jsonify({"success": True, "message": "LinkedIn browser closed"})
# ============================================================================
# RUN APPLICATION
# ============================================================================
"""
Additional Flask Routes for LinkedIn Integration
Add these routes to your app.py file
"""

# ============================================================================
# LINKEDIN STATUS ROUTE (ADD THIS TO APP.PY)
# ============================================================================
# Add these routes to your app.py file

# ============================================================================
# MESSAGE TEMPLATES ROUTES (ADD TO APP.PY)
# ============================================================================

@app.route('/api/templates/save', methods=['POST'])
def save_template():
    """Save a message template"""
    try:
        data = request.json
        template_text = data.get('template', '').strip()
        
        if not template_text:
            return jsonify({
                'success': False,
                'message': 'Template text is required'
            }), 400
        
        # Save to database
        template_id = db_manager.save_message_template(template_text)
        
        if template_id:
            db_manager.log_activity(
                activity_type='template_saved',
                description=f'Message template saved (ID: {template_id})',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': 'Template saved successfully',
                'template_id': template_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save template'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get all message templates"""
    try:
        templates = db_manager.get_all_message_templates()
        
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """Get a single template"""
    try:
        template = db_manager.get_message_template(template_id)
        
        if template:
            return jsonify({
                'success': True,
                'template': template
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Template not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a message template"""
    try:
        success = db_manager.delete_message_template(template_id)
        
        if success:
            db_manager.log_activity(
                activity_type='template_deleted',
                description=f'Message template deleted (ID: {template_id})',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': 'Template deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Template not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================================
# EDIT MESSAGE ROUTE (ADD TO APP.PY)
# ============================================================================


# ============================================================================
# ADD THESE 2 ROUTES TO YOUR app.py (after the existing LinkedIn routes)
# ============================================================================

@app.route('/api/linkedin/status', methods=['GET'])
def get_linkedin_status():
    """Check if user is logged into LinkedIn"""
    global linkedin_sender
    
    try:
        if linkedin_sender and linkedin_sender.driver:
            try:
                # Check if we're still on LinkedIn
                current_url = linkedin_sender.driver.current_url
                
                if 'linkedin.com' in current_url:
                    # Try to get user name
                    try:
                        linkedin_sender.driver.get('https://www.linkedin.com/in/me/')
                        time.sleep(1)
                        
                        page_title = linkedin_sender.driver.title
                        user_name = page_title.split('|')[0].strip() if '|' in page_title else 'LinkedIn User'
                        
                        return jsonify({
                            'success': True,
                            'logged_in': True,
                            'user_name': user_name
                        })
                    except:
                        return jsonify({
                            'success': True,
                            'logged_in': True,
                            'user_name': 'LinkedIn User'
                        })
                else:
                    return jsonify({'success': True, 'logged_in': False})
            except:
                linkedin_sender = None
                return jsonify({'success': True, 'logged_in': False})
        else:
            return jsonify({'success': True, 'logged_in': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'logged_in': False}), 500


@app.route('/api/messages/<int:message_id>/status', methods=['PATCH'])
def update_message_status_route(message_id):
    """Update message status"""
    try:
        data = request.json
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'message': 'Status is required'}), 400
        
        success = db_manager.update_message_status(message_id, new_status)
        
        if success:
            return jsonify({'success': True, 'message': f'Message status updated to {new_status}'})
        else:
            return jsonify({'success': False, 'message': 'Message not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/messages/<int:message_id>/edit', methods=['PUT'])
def edit_message(message_id):
    """Edit a message content"""
    try:
        data = request.json
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return jsonify({
                'success': False,
                'message': 'Message content is required'
            }), 400
        
        # Update message content
        success = db_manager.update_message_content(message_id, new_content)
        
        if success:
            db_manager.log_activity(
                activity_type='message_edited',
                description=f'Message {message_id} content updated',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': 'Message updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Message not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SC AI Lead Generation System - COOLDOWN ENABLED")
    print("=" * 60)
    print("\n✅ Scraping cooldown manager integrated!")
    print("\n📋 Quick Start:")
    print("1. Visit: http://localhost:5000/settings")
    print("2. Save LinkedIn + OpenAI credentials")
    print("3. Test connection")
    print("4. Upload target document")
    print("5. Start scraping!")
    print("\n⏰ Cooldown: 1 scrape/week by default (configurable)")
    print("\n" + "=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )