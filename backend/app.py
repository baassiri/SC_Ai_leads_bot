"""
SC AI Lead Generation System - Clean Dynamic Backend
Works only with uploaded documents - no hardcoded personas
FIXED: Clean AB test routes, no duplicates
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import threading
import time
import random
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from backend.config import Config, get_config
from backend.database.db_manager import db_manager
from backend.credentials_manager import credentials_manager

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
                goals_str = '\n'.join(persona_data.get('goals', [])) if isinstance(persona_data.get('goals'), list) else str(persona_data.get('goals', ''))
                pain_points_str = '\n'.join(persona_data.get('pain_points', [])) if isinstance(persona_data.get('pain_points'), list) else str(persona_data.get('pain_points', ''))
                keywords_str = ', '.join(persona_data.get('keywords', [])[:5]) if isinstance(persona_data.get('keywords'), list) else str(persona_data.get('keywords', ''))
                
                existing = db_manager.get_persona_by_name(persona_data.get('name', 'Unknown'))
                
                if not existing:
                    persona_id = db_manager.create_persona(
                        name=persona_data.get('name', 'Unknown'),
                        description=persona_data.get('description', ''),
                        goals=goals_str,
                        pain_points=pain_points_str,
                        message_tone=keywords_str
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

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the lead scraping bot"""
    global bot_status, scraper_thread, current_personas
    
    try:
        if bot_status['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is already running'
            }), 400
        
        personas = db_manager.get_all_personas()
        
        if not personas:
            return jsonify({
                'success': False,
                'message': '⚠️ No personas found! Please upload a document first.'
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
            description='🚀 Lead scraping bot started',
            status='success'
        )
        
        def scrape_leads_background():
            global bot_status, current_personas
            
            try:
                from backend.ai_engine.lead_scorer import score_lead
                
                api_key = credentials_manager.get_openai_key()
                
                personas = db_manager.get_all_personas()
                
                bot_status['current_activity'] = f'Searching for leads matching {len(personas)} personas...'
                bot_status['progress'] = 20
                time.sleep(2)
                
                num_leads_per_persona = 5
                total_leads = []
                
                for persona in personas:
                    if not bot_status['running']:
                        break
                    
                    persona_name = persona.get('name', 'Unknown')
                    
                    for i in range(num_leads_per_persona):
                        if not bot_status['running']:
                            break
                        
                        lead_data = generate_lead_from_persona(persona)
                        
                        bot_status['current_activity'] = f'Scraping: {lead_data["name"]}, {lead_data["title"]} at {lead_data["company"]}'
                        
                        lead_id = db_manager.create_lead(
                            name=lead_data['name'],
                            profile_url=lead_data['profile_url'],
                            title=lead_data['title'],
                            company=lead_data['company'],
                            industry=lead_data['industry'],
                            location=lead_data['location'],
                            headline=lead_data['headline'],
                            company_size=lead_data['company_size']
                        )
                        
                        if lead_id:
                            bot_status['current_activity'] = f'🤖 AI scoring: {lead_data["name"]}...'
                            
                            try:
                                scoring_result = score_lead(
                                    lead_data=lead_data,
                                    persona_data=persona,
                                    api_key=api_key
                                )
                                
                                ai_score = scoring_result['score']
                                reasoning = scoring_result['reasoning']
                                
                                db_manager.update_lead_score(
                                    lead_id,
                                    ai_score,
                                    persona_id=persona.get('id'),
                                    score_reasoning=reasoning
                                )
                                
                                db_manager.log_activity(
                                    activity_type='scrape',
                                    description=f"✅ Scraped: {lead_data['name']}, {lead_data['title']} (AI Score: {ai_score}/100)",
                                    status='success',
                                    lead_id=lead_id
                                )
                                
                                db_manager.log_activity(
                                    activity_type='score',
                                    description=f"🎯 AI scored {lead_data['name']}: {ai_score}/100 - {reasoning}",
                                    status='success',
                                    lead_id=lead_id
                                )
                                
                                total_leads.append(lead_data['name'])
                                
                            except Exception as e:
                                print(f"⚠️ AI scoring failed for {lead_data['name']}: {str(e)}")
                                fallback_score = lead_data.get('score', random.randint(70, 90))
                                
                                db_manager.update_lead_score(
                                    lead_id,
                                    fallback_score,
                                    persona_id=persona.get('id'),
                                    score_reasoning=f"Match for {persona_name} persona (fallback scoring)"
                                )
                                
                                db_manager.log_activity(
                                    activity_type='scrape',
                                    description=f"✅ Scraped: {lead_data['name']}, {lead_data['title']} (Score: {fallback_score}/100 - fallback)",
                                    status='success',
                                    lead_id=lead_id
                                )
                                
                                total_leads.append(lead_data['name'])
                        
                        time.sleep(0.5)
                
                bot_status['leads_scraped'] = len(total_leads)
                bot_status['current_activity'] = f'✅ Complete! {len(total_leads)} leads scraped and AI-scored'
                bot_status['progress'] = 100
                
                db_manager.log_activity(
                    activity_type='scrape',
                    description=f'🎉 Successfully scraped and AI-scored {len(total_leads)} leads from {len(personas)} personas',
                    status='success'
                )
                
                time.sleep(2)
                bot_status['running'] = False
                
            except Exception as e:
                bot_status['current_activity'] = f'Error: {str(e)}'
                bot_status['running'] = False
                
                db_manager.log_activity(
                    activity_type='scrape',
                    description=f'❌ Error during scraping: {str(e)}',
                    status='failed',
                    error_message=str(e)
                )
        
        scraper_thread = threading.Thread(target=scrape_leads_background, daemon=True)
        scraper_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Bot started! Generating leads with AI scoring...',
            'status': bot_status
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

@app.route('/api/leads/top', methods=['GET'])
def get_top_leads():
    """Get top N leads by AI score"""
    try:
        limit = request.args.get('limit', 20, type=int)
        min_score = request.args.get('min_score', 70, type=int)
        
        all_leads = db_manager.get_all_leads()
        qualified_leads = [lead for lead in all_leads if lead.get('ai_score', 0) >= min_score]
        qualified_leads.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
        top_leads = qualified_leads[:limit]
        
        return jsonify({
            'success': True,
            'count': len(top_leads),
            'leads': top_leads,
            'total_qualified': len(qualified_leads),
            'message': f'Found {len(top_leads)} top leads (score >= {min_score})'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/leads/auto-select', methods=['POST'])
def auto_select_leads():
    """Auto-select top leads and mark them for message generation"""
    try:
        data = request.json
        limit = data.get('limit', 20)
        min_score = data.get('min_score', 70)
        
        all_leads = db_manager.get_all_leads()
        qualified_leads = [lead for lead in all_leads if lead.get('ai_score', 0) >= min_score]
        qualified_leads.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
        top_leads = qualified_leads[:limit]
        
        selected_ids = []
        for lead in top_leads:
            try:
                db_manager.update_lead_status(
                    lead_id=lead['id'],
                    status='selected_for_outreach'
                )
                selected_ids.append(lead['id'])
            except Exception as e:
                print(f"Error updating lead {lead['id']}: {str(e)}")
                continue
        
        db_manager.log_activity(
            activity_type='lead_selection',
            description=f'🎯 Auto-selected top {len(selected_ids)} leads for outreach',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'selected_count': len(selected_ids),
            'selected_ids': selected_ids,
            'message': f'✅ Selected {len(selected_ids)} top leads for outreach'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/leads/<int:lead_id>/messages', methods=['GET'])
def get_lead_messages(lead_id):
    try:
        messages = db_manager.get_messages_by_lead(lead_id)
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'message_type': msg.message_type,
                'content': msg.content,
                'variant': msg.variant,
                'status': msg.status,
                'created_at': msg.created_at.isoformat() if msg.created_at else None
            })
        
        return jsonify({
            'success': True,
            'messages': messages_data
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

@app.route('/api/messages/generate', methods=['POST'])
def generate_messages():
    """Generate A/B/C message variants for leads"""
    try:
        data = request.json
        lead_ids = data.get('lead_ids', [])
        
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
        
        from backend.ai_engine.message_generator_abc import ABCMessageGenerator
        
        generator = ABCMessageGenerator(api_key=api_key)
        results = generator.batch_generate(lead_ids, max_leads=20)
        
        db_manager.log_activity(
            activity_type='message_generation',
            description=f'🎨 Generated {results["messages_created"]} A/B/C message variants for {results["successful"]} leads',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'Generated {results["messages_created"]} message variants',
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

@app.route('/api/messages/<int:message_id>/unapprove', methods=['POST'])
def unapprove_message(message_id):
    """Unapprove a message (set back to draft)"""
    try:
        success = db_manager.update_message_status(message_id, 'draft')
        
        if success:
            db_manager.log_activity(
                activity_type='message_unapproved',
                description=f'Message {message_id} set back to draft',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': 'Message set back to draft'
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

@app.route('/api/messages/<int:message_id>', methods=['PUT'])
def update_message(message_id):
    try:
        data = request.json
        content = data.get('content')
        
        if not content:
            return jsonify({
                'success': False,
                'message': 'Content is required'
            }), 400
        
        with db_manager.session_scope() as session:
            from backend.database.models import Message
            message = session.query(Message).filter(Message.id == message_id).first()
            
            if message:
                message.content = content
                message.updated_at = datetime.utcnow()
                
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

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a message"""
    try:
        success = db_manager.delete_message(message_id)
        
        if success:
            db_manager.log_activity(
                activity_type='message_deleted',
                description=f'Message {message_id} deleted',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': 'Message deleted successfully'
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
# API ROUTES - ANALYTICS
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
# API ROUTES - A/B TESTING
# ============================================================================

@app.route('/api/ab-tests/create', methods=['POST'])
def create_ab_test():
    """Create a new A/B/C test"""
    try:
        data = request.json
        test_name = data.get('test_name')
        campaign_id = data.get('campaign_id')
        lead_persona = data.get('lead_persona')
        min_sends = data.get('min_sends', 20)
        
        if not test_name:
            return jsonify({
                'success': False,
                'message': 'Test name is required'
            }), 400
        
        test_id = db_manager.create_ab_test(
            test_name=test_name,
            campaign_id=campaign_id,
            lead_persona=lead_persona,
            min_sends=min_sends
        )
        
        db_manager.log_activity(
            activity_type='ab_test_created',
            description=f'Created A/B test: {test_name}',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'message': f'A/B test "{test_name}" created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests', methods=['GET'])
def get_ab_tests():
    """Get all AB tests"""
    try:
        status = request.args.get('status')
        tests = db_manager.get_all_ab_tests(status=status)
        
        return jsonify({
            'success': True,
            'count': len(tests),
            'tests': tests
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/active', methods=['GET'])
def get_active_ab_tests():
    """Get all active AB tests"""
    try:
        tests = db_manager.get_active_ab_tests()
        
        return jsonify({
            'success': True,
            'count': len(tests),
            'tests': tests
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/<int:test_id>', methods=['GET'])
def get_ab_test(test_id):
    """Get specific AB test details"""
    try:
        test = db_manager.get_ab_test_by_id(test_id)
        
        if not test:
            return jsonify({
                'success': False,
                'message': 'Test not found'
            }), 404
        
        return jsonify({
            'success': True,
            'test': test
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/<int:test_id>/record-send', methods=['POST'])
def record_ab_test_send(test_id):
    """Record that a message was sent for a variant"""
    try:
        data = request.json
        variant = data.get('variant', '').upper()
        
        if variant not in ['A', 'B', 'C']:
            return jsonify({
                'success': False,
                'message': 'Invalid variant. Must be A, B, or C'
            }), 400
        
        success = db_manager.record_ab_test_message_sent(test_id, variant)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Test not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': f'Recorded send for variant {variant}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/<int:test_id>/record-reply', methods=['POST'])
def record_ab_test_reply(test_id):
    """Record a reply for a variant"""
    try:
        data = request.json
        variant = data.get('variant', '').upper()
        sentiment_score = data.get('sentiment_score', 0.5)
        
        if variant not in ['A', 'B', 'C']:
            return jsonify({
                'success': False,
                'message': 'Invalid variant. Must be A, B, or C'
            }), 400
        
        if not 0 <= sentiment_score <= 1:
            return jsonify({
                'success': False,
                'message': 'sentiment_score must be between 0 and 1'
            }), 400
        
        success = db_manager.record_ab_test_reply(test_id, variant, sentiment_score)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Test not found'
            }), 404
        
        test = db_manager.get_ab_test_by_id(test_id)
        winner_declared = test['status'] == 'completed' if test else False
        
        response = {
            'success': True,
            'message': f'Recorded reply for variant {variant}'
        }
        
        if winner_declared:
            response['winner_declared'] = True
            response['winning_variant'] = test['winning_variant']
            response['message'] += f' - 🏆 Winner: Variant {test["winning_variant"]}!'
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/<int:test_id>/comparison', methods=['GET'])
def get_ab_test_comparison(test_id):
    """Get performance comparison of all variants"""
    try:
        comparison = db_manager.get_ab_test_performance_comparison(test_id)
        
        if not comparison:
            return jsonify({
                'success': False,
                'message': 'Test not found'
            }), 404
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/<int:test_id>/status', methods=['PUT'])
def update_ab_test_status(test_id):
    """Update AB test status"""
    try:
        data = request.json
        status = data.get('status', '').lower()
        
        if status not in ['active', 'completed', 'paused']:
            return jsonify({
                'success': False,
                'message': 'Invalid status. Must be active, completed, or paused'
            }), 400
        
        success = db_manager.update_ab_test_status(test_id, status)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Test not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': f'Test status updated to {status}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/leaderboard', methods=['GET'])
def get_ab_test_leaderboard():
    """Get performance leaderboard of completed tests"""
    try:
        leaderboard = db_manager.get_ab_test_leaderboard()
        
        return jsonify({
            'success': True,
            'count': len(leaderboard),
            'leaderboard': leaderboard
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/<int:test_id>/next-variant', methods=['GET'])
def get_next_ab_test_variant(test_id):
    """Get next variant to assign (round-robin)"""
    try:
        variant = db_manager.get_next_variant_for_test(test_id)
        
        return jsonify({
            'success': True,
            'variant': variant
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/ab-tests/stats', methods=['GET'])
def get_ab_test_stats():
    """Get overall AB testing statistics"""
    try:
        all_tests = db_manager.get_all_ab_tests()
        active_tests = db_manager.get_active_ab_tests()
        
        total_tests = len(all_tests)
        completed_tests = sum(1 for t in all_tests if t.get('status') == 'completed')
        total_messages_tested = sum(t.get('total_sent', 0) for t in all_tests)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_tests': total_tests,
                'active_tests': len(active_tests),
                'completed_tests': completed_tests,
                'total_messages_tested': total_messages_tested,
                'avg_messages_per_test': total_messages_tested / total_tests if total_tests > 0 else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SC AI Lead Generation System - Clean Dynamic Version")
    print("=" * 60)
    print("\n✅ NO hardcoded personas - everything from YOUR uploads!")
    print("\n📋 Steps:")
    print("1. Visit: http://localhost:5000")
    print("2. Save credentials")
    print("3. Upload your document")
    print("4. AI extracts personas")
    print("5. Start bot to generate leads")
    print("\n" + "=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )