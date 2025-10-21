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

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai_engine.message_generator_abc import ABCMessageGenerator
from backend.automation.scheduler import scheduler as message_scheduler
from backend.config import Config, get_config
from backend.database.db_manager import db_manager
from backend.credentials_manager import credentials_manager
from backend.scraping_cooldown_manager import get_cooldown_manager
from backend.linkedin.linkedin_sender import LinkedInSender

from backend.api.missing_endpoints import register_missing_endpoints
from backend.api.schedule_routes import register_scheduling_routes
from backend.api.timeline_routes import register_timeline_routes
from backend.api.message_routes import register_message_routes
from backend.api.template_routes import register_template_routes
from backend.api.persona_routes import register_persona_routes

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

current_personas = []
scraper_thread = None
linkedin_sender = None
bot_lock = threading.Lock()

register_missing_endpoints(app, db_manager, credentials_manager)
register_scheduling_routes(app, db_manager)
register_timeline_routes(app, db_manager)
register_message_routes(app, db_manager)
register_template_routes(app, db_manager)
register_persona_routes(app, db_manager)

print("✅ All routes registered successfully")

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
    return render_template('settings.html')

@app.route('/ab-analytics')
def ab_analytics_page():
    return render_template('ab_test_analytics.html')

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
    return save_credentials()

@app.route('/api/settings/test', methods=['POST'])
def test_settings_alias():
    return test_connection()

@app.route('/api/auth/test-connection', methods=['POST'])
def test_connection():
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        service = data.get('service')
        print(f"🧪 Testing connection for service: {service}")
        
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service parameter is required (linkedin, openai, or all)'
            }), 400
        
        if service == 'all':
            results = []
            all_success = True
            
            linkedin_creds = credentials_manager.get_linkedin_credentials()
            if linkedin_creds and linkedin_creds.get('email'):
                results.append(f"✅ LinkedIn: {linkedin_creds['email']}")
            else:
                results.append("❌ LinkedIn: Not configured")
                all_success = False
            
            api_key = credentials_manager.get_openai_key()
            if api_key:
                try:
                    import openai
                    openai.api_key = api_key
                    openai.models.list()
                    results.append("✅ OpenAI: Valid API key")
                except Exception as e:
                    results.append(f"❌ OpenAI: Invalid ({str(e)[:50]})")
                    all_success = False
            else:
                results.append("❌ OpenAI: Not configured")
                all_success = False
            
            message = "\n".join(results)
            print(message)
            
            return jsonify({
                'success': all_success,
                'message': message
            })
        
        elif service == 'linkedin':
            linkedin_creds = credentials_manager.get_linkedin_credentials()
            
            if not linkedin_creds:
                return jsonify({
                    'success': False,
                    'message': 'No LinkedIn credentials found. Please save credentials first.'
                }), 400
            
            if not linkedin_creds.get('email') or not linkedin_creds.get('password'):
                return jsonify({
                    'success': False,
                    'message': 'LinkedIn credentials incomplete.'
                }), 400
            
            print(f"✅ LinkedIn credentials found for: {linkedin_creds['email']}")
            return jsonify({
                'success': True,
                'message': f'LinkedIn: {linkedin_creds["email"]}'
            })
        
        elif service == 'openai':
            api_key = credentials_manager.get_openai_key()
            
            if not api_key:
                return jsonify({
                    'success': False,
                    'message': 'No OpenAI API key found.'
                }), 400
            
            try:
                import openai
                openai.api_key = api_key
                openai.models.list()
                
                print(f"✅ OpenAI API key is valid!")
                return jsonify({
                    'success': True,
                    'message': 'OpenAI API key is valid!'
                })
                
            except Exception as api_error:
                print(f"❌ OpenAI API key test failed: {str(api_error)}")
                return jsonify({
                    'success': False,
                    'message': f'Invalid API key: {str(api_error)}'
                }), 400
        
        else:
            print(f"❌ Invalid service: {service}")
            return jsonify({
                'success': False,
                'message': f'Invalid service: {service}'
            }), 400
        
    except Exception as e:
        print(f"❌ Test connection error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/upload-targets', methods=['POST'])
def upload_targets():
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
                goals_str = '\n'.join(persona_data.get('goals', [])) if isinstance(persona_data.get('goals'), list) else str(persona_data.get('goals', ''))
                pain_points_str = '\n'.join(persona_data.get('pain_points', [])) if isinstance(persona_data.get('pain_points'), list) else str(persona_data.get('pain_points', ''))
                
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
            'message': f'Document analyzed! Extracted {personas_saved} personas.',
            'personas': personas_list,
            'total_personas': len(personas_list)
        })
        
    except Exception as e:
        print(f"Error uploading targets: {str(e)}")
        import traceback
        traceback.print_exc()
        
        db_manager.log_activity(
            activity_type='file_upload',
            description=f'Failed to analyze document: {str(e)}',
            status='failed',
            error_message=str(e)
        )
        
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

def generate_lead_from_persona(persona):
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

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    global bot_status, scraper_thread
    
    try:
        if bot_status['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is already running'
            }), 400
        
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
        
        request_data = request.json or {}
        target_profile_from_ui = request_data.get('target_profile', '').strip()
        
        def scrape_leads_background():
            
            def build_search_query_from_persona(persona):
                
                if persona.get('smart_search_query'):
                    query = persona['smart_search_query'].strip()
                    if query:
                        return query
                
                if persona.get('job_titles'):
                    job_titles = [t.strip() for t in persona['job_titles'].split('\n') if t.strip()]
                    if job_titles:
                        return ' OR '.join(f'"{title}"' for title in job_titles[:3])
                
                if persona.get('linkedin_keywords'):
                    keywords = [k.strip() for k in persona['linkedin_keywords'].split('\n') if k.strip()]
                    if keywords:
                        return ' '.join(keywords[:5])
                
                persona_name = persona.get('name', '').lower()
                if 'founder' in persona_name or 'sme' in persona_name:
                    return 'CEO founder'
                elif 'consultant' in persona_name or 'coach' in persona_name:
                    return 'consultant coach advisor'
                elif 'director' in persona_name or 'managing' in persona_name:
                    return 'Managing Director Senior Partner'
                elif 'analyst' in persona_name or 'associate' in persona_name:
                    return 'Analyst Associate VP'
                else:
                    return 'CEO founder director'
            
            try:
                from backend.scrapers.linkedin_scraper import LinkedInScraper
                from backend.ai_engine.lead_scorer import score_lead
                
                with bot_lock:
                    scraper = LinkedInScraper(
                        email=linkedin_creds['email'],
                        password=linkedin_creds['password'],
                        headless=False,
                        sales_nav_preference=False
                    )
                    
                    bot_status['current_activity'] = 'Logging into LinkedIn...'
                    bot_status['progress'] = 10
                    
                    if not scraper.login():
                        raise Exception("Failed to login to LinkedIn")
                    
                    bot_status['current_activity'] = 'Login successful!'
                    bot_status['progress'] = 30
                    time.sleep(2)
                    
                    if target_profile_from_ui:
                        search_keyword = target_profile_from_ui
                        print(f"🎯 Using target profile from UI: {target_profile_from_ui}")
                    elif personas and len(personas) > 0:
                        persona = personas[0]
                        search_keyword = build_search_query_from_persona(persona)
                        
                        print(f"🤖 Using persona-based search: {search_keyword}")
                        print(f"   📋 Persona: {persona.get('name')}")
                        
                        if persona.get('smart_search_query'):
                            print(f"   ⚡ Source: Smart Search Query")
                        elif persona.get('job_titles'):
                            print(f"   💼 Source: Job Titles")
                        elif persona.get('linkedin_keywords'):
                            print(f"   🔍 Source: LinkedIn Keywords")
                        else:
                            print(f"   📝 Source: Persona Name Fallback")
                    else:
                        search_keyword = 'CEO founder'
                        print(f"⚠️ Using default: {search_keyword}")
                    
                    bot_status['current_activity'] = f'Searching: {search_keyword}'
                    bot_status['progress'] = 50
                    
                    scraped_leads = scraper.scrape_leads(
                        filters={'keywords': search_keyword},
                        max_pages=10
                    )
                    
                    if not scraped_leads:
                        raise Exception("No leads found")
                    
                    bot_status['current_activity'] = f'Found {len(scraped_leads)} leads!'
                    bot_status['progress'] = 70
                    
                    successfully_imported = 0
                    api_key = credentials_manager.get_openai_api_key()
                    
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
                    
                    if scraper.driver:
                        scraper.driver.quit()
                    
                    cooldown_manager = get_cooldown_manager()
                    cooldown_manager.record_scrape(user_id=1, leads_scraped=successfully_imported)
                    
                    bot_status['current_activity'] = f'Complete! {successfully_imported} leads scraped'
                    bot_status['progress'] = 100
                    
                    db_manager.log_activity(
                        activity_type='scrape',
                        description=f'Scraped {successfully_imported} leads',
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
    global linkedin_sender
    
    linkedin_logged_in = False
    if linkedin_sender is not None:
        try:
            if hasattr(linkedin_sender, 'driver') and linkedin_sender.driver is not None:
                current_url = linkedin_sender.driver.current_url
                if 'linkedin.com' in current_url:
                    linkedin_logged_in = True
                    print(f"✅ LinkedIn session active: {current_url}")
        except Exception as e:
            print(f"❌ LinkedIn session check failed: {str(e)}")
            linkedin_logged_in = False
    
    return jsonify({
        'success': True,
        'status': bot_status,
        'linkedin_logged_in': linkedin_logged_in
    })

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

@app.route('/api/leads/bulk-update', methods=['POST'])
def bulk_update_leads():
    try:
        data = request.json
        lead_ids = data.get('lead_ids', [])
        status = data.get('status', 'qualified')
        
        if not lead_ids:
            return jsonify({
                'success': False,
                'message': 'No leads selected'
            }), 400
        
        updated_count = 0
        
        for lead_id in lead_ids:
            success = db_manager.update_lead_status(lead_id, status, 'pending')
            if success:
                updated_count += 1
        
        db_manager.log_activity(
            activity_type='bulk_update',
            description=f'Bulk updated {updated_count} leads to {status}',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} leads',
            'count': updated_count
        })
        
    except Exception as e:
        print(f"❌ Error bulk updating leads: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/leads/top', methods=['GET'])
def get_top_leads():
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
    return start_bot()

@app.route('/api/scheduler/status', methods=['GET'])
def get_scheduler_status():
    try:
        status = message_scheduler.get_status()
        return jsonify({'success': True, 'scheduler': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    try:
        message_scheduler.start()
        return jsonify({'success': True, 'message': 'Scheduler started'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    try:
        message_scheduler.stop()
        return jsonify({'success': True, 'message': 'Scheduler stopped'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

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

@app.route('/api/ab-tests/<int:test_id>/analyze', methods=['GET'])
def analyze_ab_test(test_id):
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

@app.route('/api/scraping/cooldown-status', methods=['GET'])
def get_cooldown_status():
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

linkedin_sender = None

@app.route('/api/linkedin/login', methods=['POST'])
def linkedin_login():
    global linkedin_sender
    
    try:
        print("🔄 LinkedIn login requested...")
        
        if linkedin_sender is None:
            print("📦 Creating new LinkedInSender instance...")
            linkedin_sender = LinkedInSender()
        
        if not hasattr(linkedin_sender, 'driver') or linkedin_sender.driver is None:
            print("🚗 Initializing Chrome driver...")
            linkedin_sender.init_driver()
            print("✅ Chrome driver initialized")
        
        print("🍪 Attempting to load saved session...")
        if linkedin_sender.load_cookies():
            print("✅ Logged in using saved session")
            
            db_manager.log_activity(
                activity_type='linkedin_login',
                description='LinkedIn login successful (saved session)',
                status='success'
            )
            
            return jsonify({
                "success": True, 
                "message": "Logged in using saved session"
            })
        
        print("🌐 Opening LinkedIn login page...")
        try:
            linkedin_sender.driver.get('https://www.linkedin.com/login')
            
            import time
            time.sleep(2)
            
            print("✅ LinkedIn login page opened - waiting for user to login...")
            
            return jsonify({
                "success": True,
                "message": "LinkedIn login page opened. Please complete login in the browser window.",
                "manual_login": True
            })
            
        except Exception as login_error:
            print(f"❌ Error opening login page: {str(login_error)}")
            return jsonify({
                "success": False,
                "message": f"Error opening LinkedIn login page: {str(login_error)}"
            }), 500
            
    except Exception as e:
        print(f"❌ LinkedIn login error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        db_manager.log_activity(
            activity_type='linkedin_login',
            description=f'LinkedIn login failed: {str(e)}',
            status='error',
            error_message=str(e)
        )
        
        return jsonify({
            "success": False,
            "message": f"Login error: {str(e)}"
        }), 500

@app.route('/api/linkedin/send-messages', methods=['POST'])
def send_linkedin_messages():
    global linkedin_sender
    
    if not linkedin_sender:
        return jsonify({"success": False, "error": "Please login to LinkedIn first"}), 400
    
    try:
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
            
            if linkedin_sender.sent_today >= linkedin_sender.daily_limit:
                results.append({
                    "lead": lead_name,
                    "status": "skipped",
                    "reason": "Daily limit reached (100 messages)"
                })
                continue
            
            print(f"\n📤 Sending to: {lead_name}")
            print(f"💬 Message: {content}")
            
            result = linkedin_sender.send_connection_request(profile_url, content)
            
            if result["success"]:
                db_manager.update_message_status(msg_id, 'sent')
                
                db_manager.update_lead_status(lead_id, 'contacted', 'pending')
                
                sent_count += 1
                
                results.append({
                    "lead": lead_name,
                    "status": "sent",
                    "message": result["message"]
                })
                
            else:
                db_manager.update_message_status(msg_id, 'failed')
                failed_count += 1
                
                results.append({
                    "lead": lead_name,
                    "status": "failed",
                    "error": result["error"]
                })
            
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
    global linkedin_sender
    if linkedin_sender:
        linkedin_sender.close()
        linkedin_sender = None
    return jsonify({"success": True, "message": "LinkedIn browser closed"})

@app.route('/api/linkedin/status', methods=['GET'])
def linkedin_status():
    global linkedin_sender
    
    try:
        if linkedin_sender is None:
            return jsonify({
                'success': True,
                'connected': False,
                'message': 'Not logged in'
            })
        
        if not hasattr(linkedin_sender, 'driver') or linkedin_sender.driver is None:
            return jsonify({
                'success': True,
                'connected': False,
                'message': 'Driver not initialized'
            })
        
        try:
            current_url = linkedin_sender.driver.current_url
            is_linkedin = 'linkedin.com' in current_url
            
            return jsonify({
                'success': True,
                'connected': is_linkedin,
                'message': 'Connected' if is_linkedin else 'Browser open but not on LinkedIn'
            })
        except:
            return jsonify({
                'success': True,
                'connected': False,
                'message': 'Browser session expired'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'connected': False,
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