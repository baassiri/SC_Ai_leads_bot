"""
Message Routes - IMPROVED ERROR LOGGING
"""

from flask import jsonify, request
from datetime import datetime
import traceback

db_manager = None

def register_message_routes(app, database_manager):
    """Register all message routes"""
    global db_manager
    db_manager = database_manager
    
    app.add_url_rule('/api/messages', 'get_messages', get_messages, methods=['GET'])
    app.add_url_rule('/api/messages/stats', 'get_message_stats', get_message_stats, methods=['GET'])
    app.add_url_rule('/api/messages/generate', 'generate_messages', generate_messages, methods=['POST'])
    app.add_url_rule('/api/messages/<int:message_id>/approve', 'approve_message', approve_message, methods=['POST'])
    app.add_url_rule('/api/messages/<int:message_id>/reject', 'reject_message', reject_message, methods=['POST'])
    app.add_url_rule('/api/messages/send', 'send_messages', send_messages, methods=['POST'])
    app.add_url_rule('/api/messages/<int:message_id>', 'delete_message_route', delete_message, methods=['DELETE'])
    
    print("✅ Message routes registered")

def get_messages():
    """Get all messages with optional filtering"""
    try:
        status = request.args.get('status', '')
        lead_id = request.args.get('lead_id', type=int)
        
        messages = db_manager.get_messages_by_status_with_lead_info(
            status=status if status else None,
            lead_id=lead_id,
            limit=100
        )
        
        return jsonify({
            'success': True,
            'messages': messages
        })
        
    except Exception as e:
        print(f"❌ Error getting messages: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_message_stats():
    """Get message statistics"""
    try:
        stats = db_manager.get_message_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ Error getting message stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_messages():
    """Generate messages for selected leads"""
    print("\n" + "="*60)
    print("🎨 GENERATE MESSAGES REQUEST")
    print("="*60)
    
    try:
        # Log the request
        data = request.json
        print(f"📥 Request data: {data}")
        
        lead_ids = data.get('lead_ids', [])
        template_id = data.get('template_id')
        
        print(f"🎯 Lead IDs: {lead_ids}")
        print(f"📝 Template ID: {template_id}")
        
        if not lead_ids:
            error_msg = 'No leads selected'
            print(f"❌ ERROR: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Get template if provided
        template_text = None
        if template_id:
            print(f"📋 Fetching template {template_id}...")
            with db_manager.session_scope() as session:
                from backend.database.models import MessageTemplate
                template = session.query(MessageTemplate).filter_by(id=template_id).first()
                if template:
                    template_text = template.template
                    print(f"✅ Template loaded: {template_text[:50]}...")
        
        # Import message generator
        print("🤖 Initializing MessageGenerator...")
        from backend.ai_engine.message_generator import MessageGenerator
        
        try:
            generator = MessageGenerator()
            print("✅ MessageGenerator initialized")
        except Exception as gen_error:
            print(f"❌ ERROR initializing MessageGenerator: {str(gen_error)}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Failed to initialize AI generator: {str(gen_error)}'
            }), 500
        
        generated_count = 0
        errors = []
        
        for lead_id in lead_ids:
            print(f"\n📍 Processing lead {lead_id}...")
            
            # Get lead details
            lead = db_manager.get_lead_by_id(lead_id)
            
            if not lead:
                error_msg = f"Lead {lead_id} not found"
                print(f"⚠️ {error_msg}")
                errors.append(error_msg)
                continue
            
            print(f"   Name: {lead['name']}")
            print(f"   Title: {lead.get('title', 'N/A')}")
            print(f"   Company: {lead.get('company', 'N/A')}")
            
            try:
                # Generate messages (3 variants)
                print(f"   🎨 Generating messages...")
                messages = generator.generate_connection_request(
                    lead_name=lead['name'],
                    lead_title=lead.get('title', ''),
                    lead_company=lead.get('company', ''),
                    persona_name=lead.get('persona', 'Professional'),
                    custom_context=template_text
                )
                
                print(f"   ✅ Generated {len(messages)} variants")
                
                # Save each variant
                for variant_key, content in messages.items():
                    variant = variant_key.split('_')[-1].upper()
                    
                    print(f"   💾 Saving variant {variant}...")
                    db_manager.create_message(
                        lead_id=lead_id,
                        message_type='connection_request',
                        content=content,
                        variant=variant,
                        generated_by='gpt-4',
                        prompt_used='Generated from message routes'
                    )
                
                generated_count += 1
                print(f"   ✅ Saved all variants for {lead['name']}")
                
            except Exception as lead_error:
                error_msg = f"Error generating for {lead['name']}: {str(lead_error)}"
                print(f"   ❌ {error_msg}")
                traceback.print_exc()
                errors.append(error_msg)
        
        print("\n" + "="*60)
        print(f"✅ Generation complete: {generated_count} leads processed")
        if errors:
            print(f"⚠️ Errors: {len(errors)}")
            for err in errors:
                print(f"   - {err}")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'message': f'Generated messages for {generated_count} leads',
            'count': generated_count,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR generating messages: {str(e)}")
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def approve_message(message_id):
    """Approve a message"""
    try:
        result = db_manager.update_message_status(message_id, 'approved')
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Message approved'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Message not found'
            }), 404
            
    except Exception as e:
        print(f"❌ Error approving message: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def reject_message(message_id):
    """Reject/delete a message"""
    try:
        result = db_manager.delete_message(message_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Message rejected'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Message not found'
            }), 404
            
    except Exception as e:
        print(f"❌ Error rejecting message: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def send_messages():
    """Send approved messages"""
    try:
        messages = db_manager.get_messages_by_status_with_lead_info(
            status='approved',
            limit=100
        )
        
        if not messages:
            return jsonify({
                'success': False,
                'error': 'No approved messages to send'
            }), 400
        
        from backend.linkedin.linkedin_sender import LinkedInSender
        sender = LinkedInSender()
        
        sent_count = 0
        failed_count = 0
        
        for msg in messages:
            try:
                success = sender.send_message(
                    profile_url=msg['linkedin_url'],
                    message=msg['content']
                )
                
                if success:
                    db_manager.update_message_status(msg['id'], 'sent')
                    sent_count += 1
                else:
                    db_manager.update_message_status(msg['id'], 'failed')
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error sending message {msg['id']}: {str(e)}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Sent {sent_count} messages, {failed_count} failed',
            'sent': sent_count,
            'failed': failed_count
        })
        
    except Exception as e:
        print(f"❌ Error sending messages: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def delete_message(message_id):
    """Delete a message"""
    try:
        result = db_manager.delete_message(message_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Message deleted'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Message not found'
            }), 404
            
    except Exception as e:
        print(f"❌ Error deleting message: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500