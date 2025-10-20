"""
Message Routes - Handle all message-related API endpoints
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import traceback

# This will be passed when registering routes
db_manager = None

def register_message_routes(app, database_manager):
    """Register all message routes"""
    global db_manager
    db_manager = database_manager
    
    # Register all endpoints
    app.add_url_rule('/api/messages', 'get_messages', get_messages, methods=['GET'])
    app.add_url_rule('/api/messages/stats', 'get_message_stats', get_message_stats, methods=['GET'])
    app.add_url_rule('/api/messages/generate', 'generate_messages', generate_messages, methods=['POST'])
    app.add_url_rule('/api/messages/<int:message_id>/approve', 'approve_message', approve_message, methods=['POST'])
    app.add_url_rule('/api/messages/<int:message_id>/reject', 'reject_message', reject_message, methods=['POST'])
    app.add_url_rule('/api/messages/send', 'send_messages', send_messages, methods=['POST'])
    app.add_url_rule('/api/messages/<int:message_id>', 'delete_message', delete_message, methods=['DELETE'])
    
    print("✅ Message routes registered")

# ============================================================================
# GET MESSAGES
# ============================================================================

def get_messages():
    """Get all messages with optional filtering"""
    try:
        status = request.args.get('status', '')
        lead_id = request.args.get('lead_id', type=int)
        
        # Build query
        query = "SELECT m.*, l.name as lead_name, l.company, l.title FROM messages m "
        query += "LEFT JOIN leads l ON m.lead_id = l.id WHERE 1=1"
        
        params = []
        
        if status:
            query += " AND m.status = ?"
            params.append(status)
        
        if lead_id:
            query += " AND m.lead_id = ?"
            params.append(lead_id)
        
        query += " ORDER BY m.created_at DESC"
        
        messages = db_manager.execute_query(query, params)
        
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

# ============================================================================
# GET MESSAGE STATS
# ============================================================================

def get_message_stats():
    """Get message statistics"""
    try:
        stats = {
            'draft': db_manager.execute_query(
                "SELECT COUNT(*) as count FROM messages WHERE status='draft'"
            )[0]['count'],
            'approved': db_manager.execute_query(
                "SELECT COUNT(*) as count FROM messages WHERE status='approved'"
            )[0]['count'],
            'sent': db_manager.execute_query(
                "SELECT COUNT(*) as count FROM messages WHERE status='sent'"
            )[0]['count'],
            'failed': db_manager.execute_query(
                "SELECT COUNT(*) as count FROM messages WHERE status='failed'"
            )[0]['count']
        }
        
        # Calculate reply rate
        total_sent = stats['sent']
        if total_sent > 0:
            replied = db_manager.execute_query(
                "SELECT COUNT(DISTINCT lead_id) as count FROM messages WHERE status='sent' AND reply_received=1"
            )[0]['count']
            stats['reply_rate'] = round((replied / total_sent) * 100, 1)
        else:
            stats['reply_rate'] = 0
        
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

# ============================================================================
# GENERATE MESSAGES
# ============================================================================

def generate_messages():
    """Generate messages for selected leads"""
    try:
        data = request.json
        lead_ids = data.get('lead_ids', [])
        template_id = data.get('template_id')
        
        if not lead_ids:
            return jsonify({
                'success': False,
                'error': 'No leads selected'
            }), 400
        
        # Get template if provided
        template_text = None
        if template_id:
            template = db_manager.execute_query(
                "SELECT template FROM message_templates WHERE id=?",
                [template_id]
            )
            if template:
                template_text = template[0]['template']
        
        # Import message generator
        from backend.ai_engine.message_generator import MessageGenerator
        generator = MessageGenerator()
        
        generated_count = 0
        
        for lead_id in lead_ids:
            # Get lead details
            lead = db_manager.execute_query(
                "SELECT * FROM leads WHERE id=?",
                [lead_id]
            )
            
            if not lead:
                continue
            
            lead = lead[0]
            
            # Generate messages (3 variants)
            messages = generator.generate_connection_request(
                lead_name=lead['name'],
                lead_title=lead.get('title', ''),
                lead_company=lead.get('company', ''),
                persona_name=lead.get('persona', 'Professional'),
                custom_template=template_text
            )
            
            # Save each variant
            for variant_key, content in messages.items():
                variant = variant_key.split('_')[-1].upper()
                
                db_manager.execute_update(
                    """INSERT INTO messages 
                    (lead_id, message_type, content, variant, status, generated_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    [lead_id, 'connection_request', content, variant, 'draft', 'gpt-4', datetime.now()]
                )
            
            generated_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Generated messages for {generated_count} leads',
            'count': generated_count
        })
        
    except Exception as e:
        print(f"❌ Error generating messages: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# APPROVE MESSAGE
# ============================================================================

def approve_message(message_id):
    """Approve a message"""
    try:
        result = db_manager.execute_update(
            "UPDATE messages SET status='approved', approved_at=? WHERE id=?",
            [datetime.now(), message_id]
        )
        
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

# ============================================================================
# REJECT MESSAGE
# ============================================================================

def reject_message(message_id):
    """Reject/delete a message"""
    try:
        result = db_manager.execute_update(
            "DELETE FROM messages WHERE id=?",
            [message_id]
        )
        
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

# ============================================================================
# SEND MESSAGES
# ============================================================================

def send_messages():
    """Send approved messages"""
    try:
        # Get approved messages
        messages = db_manager.execute_query(
            """SELECT m.*, l.name as lead_name, l.linkedin_url 
            FROM messages m 
            LEFT JOIN leads l ON m.lead_id = l.id 
            WHERE m.status='approved'"""
        )
        
        if not messages:
            return jsonify({
                'success': False,
                'error': 'No approved messages to send'
            }), 400
        
        # Import LinkedIn sender
        from backend.linkedin.linkedin_sender import LinkedInSender
        sender = LinkedInSender()
        
        sent_count = 0
        failed_count = 0
        
        for msg in messages:
            try:
                # Send via LinkedIn
                success = sender.send_message(
                    profile_url=msg['linkedin_url'],
                    message=msg['content']
                )
                
                if success:
                    db_manager.execute_update(
                        "UPDATE messages SET status='sent', sent_at=? WHERE id=?",
                        [datetime.now(), msg['id']]
                    )
                    sent_count += 1
                else:
                    db_manager.execute_update(
                        "UPDATE messages SET status='failed' WHERE id=?",
                        [msg['id']]
                    )
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

# ============================================================================
# DELETE MESSAGE
# ============================================================================

def delete_message(message_id):
    """Delete a message"""
    try:
        result = db_manager.execute_update(
            "DELETE FROM messages WHERE id=?",
            [message_id]
        )
        
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