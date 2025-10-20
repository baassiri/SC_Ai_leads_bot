"""
Lead management API routes
"""
from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import io
import csv
from database import get_db_connection

lead_bp = Blueprint('lead', __name__)

@lead_bp.route('/api/leads', methods=['GET'])
def get_leads():
    """
    Get paginated list of leads with optional filters
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status')
        min_score = request.args.get('min_score', type=int)
        industry = request.args.get('industry')
        search = request.args.get('search')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT id, name, title, company, industry, location, 
                   linkedin_url, profile_data, score, status, 
                   created_at, last_contacted
            FROM leads
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if min_score:
            query += " AND score >= ?"
            params.append(min_score)
        
        if industry:
            query += " AND industry LIKE ?"
            params.append(f'%{industry}%')
        
        if search:
            query += " AND (name LIKE ? OR company LIKE ? OR title LIKE ?)"
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        leads = []
        for row in rows:
            leads.append({
                'id': row[0],
                'name': row[1],
                'title': row[2],
                'company': row[3],
                'industry': row[4],
                'location': row[5],
                'linkedin_url': row[6],
                'score': row[8],
                'status': row[9],
                'created_at': row[10],
                'last_contacted': row[11]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leads': leads,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@lead_bp.route('/api/leads/stats', methods=['GET'])
def get_lead_stats():
    """
    Get summary statistics for leads
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        total = cursor.fetchone()[0]
        
        # By status
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'")
        new = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'contacted'")
        contacted = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'replied'")
        replied = cursor.fetchone()[0]
        
        # Average score
        cursor.execute("SELECT AVG(score) FROM leads")
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'new': new,
                'contacted': contacted,
                'replied': replied,
                'avg_score': round(avg_score, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@lead_bp.route('/api/leads/<int:lead_id>/timeline', methods=['GET'])
def get_lead_timeline(lead_id):
    """
    Get timeline of events for a specific lead
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get lead basic info
        cursor.execute("""
            SELECT name, title, company, status, score, created_at
            FROM leads WHERE id = ?
        """, (lead_id,))
        lead_row = cursor.fetchone()
        
        if not lead_row:
            return jsonify({'success': False, 'message': 'Lead not found'}), 404
        
        lead_info = {
            'id': lead_id,
            'name': lead_row[0],
            'title': lead_row[1],
            'company': lead_row[2],
            'status': lead_row[3],
            'score': lead_row[4],
            'created_at': lead_row[5]
        }
        
        # Get timeline events from various tables
        timeline = []
        
        # 1. Lead creation
        timeline.append({
            'type': 'lead_created',
            'timestamp': lead_row[5],
            'description': 'Lead added to system',
            'icon': '✨'
        })
        
        # 2. Messages sent
        cursor.execute("""
            SELECT sent_at, message_text, status, response_text
            FROM messages
            WHERE lead_id = ?
            ORDER BY sent_at
        """, (lead_id,))
        
        for msg in cursor.fetchall():
            timeline.append({
                'type': 'message_sent',
                'timestamp': msg[0],
                'description': f'Message sent: "{msg[1][:50]}..."',
                'status': msg[2],
                'icon': '📤'
            })
            
            if msg[3]:  # Response received
                timeline.append({
                    'type': 'response_received',
                    'timestamp': msg[0],
                    'description': f'Response: "{msg[3][:50]}..."',
                    'icon': '📬'
                })
        
        # 3. Status changes (from activity log if available)
        cursor.execute("""
            SELECT timestamp, activity_type, details
            FROM activity_log
            WHERE lead_id = ?
            ORDER BY timestamp
        """, (lead_id,))
        
        for activity in cursor.fetchall():
            if activity[1] == 'status_change':
                timeline.append({
                    'type': 'status_change',
                    'timestamp': activity[0],
                    'description': f'Status changed: {activity[2]}',
                    'icon': '🔄'
                })
            elif activity[1] == 'note_added':
                timeline.append({
                    'type': 'note',
                    'timestamp': activity[0],
                    'description': activity[2],
                    'icon': '📝'
                })
        
        # 4. Campaign assignments
        cursor.execute("""
            SELECT c.name, cl.assigned_at, cl.status
            FROM campaign_leads cl
            JOIN campaigns c ON cl.campaign_id = c.id
            WHERE cl.lead_id = ?
            ORDER BY cl.assigned_at
        """, (lead_id,))
        
        for campaign in cursor.fetchall():
            timeline.append({
                'type': 'campaign_assigned',
                'timestamp': campaign[1],
                'description': f'Added to campaign: {campaign[0]}',
                'status': campaign[2],
                'icon': '🎯'
            })
        
        conn.close()
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'lead': lead_info,
            'timeline': timeline
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@lead_bp.route('/api/leads/<int:lead_id>/message', methods=['POST'])
def send_lead_message(lead_id):
    """
    Send a message to a lead
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if lead exists
        cursor.execute("SELECT name FROM leads WHERE id = ?", (lead_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Lead not found'}), 404
        
        # Here you would integrate with your messaging system
        # For now, we'll just update the status
        cursor.execute("""
            UPDATE leads 
            SET status = 'contacted', last_contacted = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), lead_id))
        
        # Log the activity
        cursor.execute("""
            INSERT INTO activity_log (lead_id, activity_type, details, timestamp)
            VALUES (?, 'message_sent', 'Manual message sent', ?)
        """, (lead_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@lead_bp.route('/api/leads/<int:lead_id>/skip', methods=['POST'])
def skip_lead(lead_id):
    """
    Mark a lead as not interested
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE leads 
            SET status = 'not_interested'
            WHERE id = ?
        """, (lead_id,))
        
        # Log the activity
        cursor.execute("""
            INSERT INTO activity_log (lead_id, activity_type, details, timestamp)
            VALUES (?, 'status_change', 'Marked as not interested', ?)
        """, (lead_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Lead marked as not interested'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@lead_bp.route('/api/leads/export', methods=['GET'])
def export_leads():
    """
    Export leads to CSV
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, title, company, industry, location, 
                   linkedin_url, score, status, created_at
            FROM leads
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Name', 'Title', 'Company', 'Industry', 'Location',
            'LinkedIn URL', 'Score', 'Status', 'Created At'
        ])
        
        # Write data
        writer.writerows(rows)
        
        # Create file response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'leads_export_{datetime.now().strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500