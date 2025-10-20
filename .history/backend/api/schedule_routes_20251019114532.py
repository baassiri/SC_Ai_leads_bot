"""
Scheduling API Routes
Add these to backend/app.py using register_scheduling_routes()
"""

from flask import jsonify, request
from datetime import datetime
import sqlite3

# ✅ FIXED IMPORTS
from backend.automation.message_scheduler import MessageScheduler
from backend.services.optimal_time_ai import optimal_time_ai, distribute_send_times

def register_scheduling_routes(app, db_manager):
    """Register all scheduling routes"""
    
    @app.route('/api/schedule/message', methods=['POST'])
    def schedule_single_message():
        """Schedule a single message"""
        try:
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
            
            # Parse start time or use now
            if start_time:
                try:
                    send_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except:
                    send_time = datetime.now()
            else:
                send_time = datetime.now()
            
            # ✅ Use Optimal Time AI to distribute send times
            send_times = distribute_send_times(
                count=len(message_ids),
                start_time=send_time,
                spread_hours=spread_hours,
                ai_optimize=ai_optimize
            )
            
            # Insert into message_schedule table
            schedule_ids = []
            conn = sqlite3.connect('data/database.db')
            cursor = conn.cursor()
            
            for message_id, scheduled_time in zip(message_ids, send_times):
                cursor.execute('''
                    INSERT INTO message_schedule (message_id, scheduled_time, status, created_at, updated_at)
                    VALUES (?, ?, 'scheduled', ?, ?)
                ''', (
                    message_id,
                    scheduled_time.isoformat(),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                schedule_ids.append(cursor.lastrowid)
            
            conn.commit()
            conn.close()
            
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
            print(f"Error in schedule_batch_messages: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/schedule/stats', methods=['GET'])
    def get_schedule_stats():
        """Get scheduling statistics"""
        try:
            conn = sqlite3.connect('data/database.db')
            cursor = conn.cursor()
            
            now = datetime.now()
            
            # Count scheduled messages
            cursor.execute("SELECT COUNT(*) FROM message_schedule WHERE status = 'scheduled'")
            scheduled_count = cursor.fetchone()[0]
            
            # Count next hour
            next_hour = now.replace(minute=0, second=0, microsecond=0)
            cursor.execute('''
                SELECT COUNT(*) FROM message_schedule 
                WHERE status = 'scheduled' 
                AND scheduled_time BETWEEN ? AND ?
            ''', (now.isoformat(), next_hour.isoformat()))
            next_hour_count = cursor.fetchone()[0]
            
            # Count today
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            cursor.execute('''
                SELECT COUNT(*) FROM message_schedule 
                WHERE status = 'scheduled' 
                AND scheduled_time BETWEEN ? AND ?
            ''', (today_start.isoformat(), today_end.isoformat()))
            today_count = cursor.fetchone()[0]
            
            # Count sent
            cursor.execute("SELECT COUNT(*) FROM message_schedule WHERE status = 'sent'")
            sent_count = cursor.fetchone()[0]
            
            conn.close()
            
            return jsonify({
                'success': True,
                'stats': {
                    'scheduled': scheduled_count,
                    'next_hour': next_hour_count,
                    'today': today_count,
                    'sent': sent_count
                }
            })
            
        except Exception as e:
            print(f"Error in get_schedule_stats: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}',
                'stats': {
                    'scheduled': 0,
                    'next_hour': 0,
                    'today': 0,
                    'sent': 0
                }
            })
    
    @app.route('/api/schedule/pending', methods=['GET'])
    def get_pending_messages():
        """Get pending scheduled messages"""
        try:
            limit = request.args.get('limit', 50, type=int)
            
            conn = sqlite3.connect('data/database.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    ms.id as schedule_id,
                    ms.message_id,
                    ms.scheduled_time,
                    ms.status,
                    m.content,
                    m.variant,
                    m.lead_id,
                    l.name as lead_name
                FROM message_schedule ms
                JOIN messages m ON ms.message_id = m.id
                LEFT JOIN leads l ON m.lead_id = l.id
                WHERE ms.status = 'scheduled'
                ORDER BY ms.scheduled_time
                LIMIT ?
            ''', (limit,))
            
            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({
                'success': True,
                'messages': messages,
                'total': len(messages)
            })
            
        except Exception as e:
            print(f"Error in get_pending_messages: {str(e)}")
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
            
            cancel_time = datetime.now()
            
            cursor.execute(
                "UPDATE message_schedule SET status = 'cancelled', updated_at = ? WHERE id = ? AND status = 'scheduled'",
                (cancel_time.isoformat(), schedule_id)
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