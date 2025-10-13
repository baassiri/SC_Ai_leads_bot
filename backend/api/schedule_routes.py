"""
Scheduling API Routes
Add these to backend/app.py
"""

from flask import jsonify, request
from datetime import datetime
import sqlite3

def register_scheduling_routes(app, db_manager):
    """Register all scheduling routes"""
    
    @app.route('/api/schedule/message', methods=['POST'])
    def schedule_single_message():
        """Schedule a single message"""
        try:
            from backend.automation.scheduler import MessageScheduler
            
            data = request.json
            message_id = data.get('message_id')
            scheduled_time = data.get('scheduled_time')
            ai_optimize = data.get('ai_optimize', False)
            
            if not message_id:
                return jsonify({
                    'success': False,
                    'message': 'Message ID is required'
                }), 400
            
            scheduler = MessageScheduler()
            
            send_time = None
            if scheduled_time:
                send_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            
            schedule_id = scheduler.schedule_message(
                message_id=message_id,
                scheduled_time=send_time,
                ai_optimize=ai_optimize
            )
            
            db_manager.log_activity(
                activity_type='message_scheduled',
                description=f'Scheduled message {message_id}',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'schedule_id': schedule_id,
                'message': 'Message scheduled successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/schedule/batch', methods=['POST'])
    def schedule_batch_messages():
        """Schedule multiple messages intelligently"""
        try:
            from backend.automation.scheduler import MessageScheduler
            
            data = request.json
            message_ids = data.get('message_ids', [])
            start_time = data.get('start_time')
            spread_hours = data.get('spread_hours', 8)
            ai_optimize = data.get('ai_optimize', True)
            
            if not message_ids:
                return jsonify({
                    'success': False,
                    'message': 'Message IDs are required'
                }), 400
            
            scheduler = MessageScheduler()
            
            send_time = None
            if start_time:
                send_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            schedule_ids = scheduler.schedule_batch(
                message_ids=message_ids,
                start_time=send_time,
                spread_hours=spread_hours,
                ai_optimize=ai_optimize
            )
            
            db_manager.log_activity(
                activity_type='batch_scheduled',
                description=f'Scheduled {len(message_ids)} messages',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'schedule_ids': schedule_ids,
                'total_scheduled': len(schedule_ids),
                'message': f'Scheduled {len(schedule_ids)} messages successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/schedule/stats', methods=['GET'])
    def get_schedule_stats():
        """Get scheduling statistics"""
        try:
            from backend.automation.scheduler import MessageScheduler
            
            scheduler = MessageScheduler()
            stats = scheduler.get_schedule_stats()
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/schedule/pending', methods=['GET'])
    def get_pending_messages():
        """Get pending scheduled messages"""
        try:
            from backend.automation.scheduler import MessageScheduler
            
            limit = request.args.get('limit', 50, type=int)
            
            scheduler = MessageScheduler()
            messages = scheduler.get_pending_messages(limit=limit)
            
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
    
    @app.route('/api/schedule/cancel/<int:schedule_id>', methods=['DELETE'])
    def cancel_scheduled_message(schedule_id):
        """Cancel a scheduled message"""
        try:
            conn = sqlite3.connect('data/database.db')
            cursor = conn.cursor()
            
            cancel_time = datetime.utcnow()
            
            cursor.execute(
                "UPDATE message_schedule SET status = 'cancelled', updated_at = ? WHERE id = ? AND status = 'scheduled'",
                (cancel_time, schedule_id)
            )
            
            if cursor.rowcount == 0:
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Schedule not found or already processed'
                }), 404
            
            conn.commit()
            conn.close()
            
            db_manager.log_activity(
                activity_type='schedule_cancelled',
                description=f'Cancelled schedule {schedule_id}',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': 'Schedule cancelled successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500