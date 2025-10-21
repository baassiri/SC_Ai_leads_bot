from flask import Blueprint, jsonify, request
from auth import api_login_required
from bot_controller import BotController
from lead_selector import LeadSelector
from optimal_time_ai import OptimalTimeAI
import sqlite3
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

bot = BotController()
lead_selector = LeadSelector()
optimal_time = OptimalTimeAI()

@analytics_bp.route('/api/analytics/dashboard', methods=['GET'])
@api_login_required
def get_dashboard_stats():
    try:
        stats = bot.get_statistics()
        lead_stats = lead_selector.get_lead_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'campaign_stats': stats,
                'lead_stats': lead_stats,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/api/analytics/performance', methods=['GET'])
@api_login_required
def get_performance_metrics():
    try:
        days = request.args.get('days', 30, type=int)
        analytics = optimal_time.get_analytics_summary(days)
        
        total_sent = sum(a['messages_sent'] for a in analytics)
        total_responses = sum(a['responses_received'] for a in analytics)
        avg_conversion = sum(a['conversion_rate'] for a in analytics) / len(analytics) if analytics else 0
        
        return jsonify({
            'success': True,
            'data': {
                'period_days': days,
                'total_messages_sent': total_sent,
                'total_responses': total_responses,
                'average_conversion_rate': round(avg_conversion, 2),
                'daily_analytics': analytics
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/api/analytics/leads', methods=['GET'])
@api_login_required
def get_leads_analytics():
    try:
        stats = lead_selector.get_lead_stats()
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT company, COUNT(*) as count
            FROM leads
            GROUP BY company
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_companies = [{'company': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT title, COUNT(*) as count
            FROM leads
            GROUP BY title
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_titles = [{'title': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'overview': stats,
                'top_companies': top_companies,
                'top_titles': top_titles
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/api/analytics/timeline', methods=['GET'])
@api_login_required
def get_timeline():
    try:
        days = request.args.get('days', 7, type=int)
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count, status
            FROM messages
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp), status
            ORDER BY date DESC
        ''', (cutoff_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        timeline_data = {}
        for row in results:
            date = row[0]
            count = row[1]
            status = row[2]
            
            if date not in timeline_data:
                timeline_data[date] = {'date': date, 'sent': 0, 'failed': 0}
            
            if status == 'sent':
                timeline_data[date]['sent'] = count
            elif status == 'failed':
                timeline_data[date]['failed'] = count
        
        timeline = list(timeline_data.values())
        
        return jsonify({
            'success': True,
            'data': {
                'timeline': timeline,
                'period_days': days
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/api/analytics/conversion', methods=['GET'])
@api_login_required
def get_conversion_funnel():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM leads')
        total_leads = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "contacted"')
        contacted = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM messages WHERE response_received = 1')
        responded = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "converted"')
        converted = cursor.fetchone()[0]
        
        conn.close()
        
        funnel = [
            {'stage': 'Total Leads', 'count': total_leads, 'percentage': 100},
            {'stage': 'Contacted', 'count': contacted, 'percentage': round((contacted/total_leads*100) if total_leads > 0 else 0, 2)},
            {'stage': 'Responded', 'count': responded, 'percentage': round((responded/total_leads*100) if total_leads > 0 else 0, 2)},
            {'stage': 'Converted', 'count': converted, 'percentage': round((converted/total_leads*100) if total_leads > 0 else 0, 2)}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'funnel': funnel
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/api/analytics/optimal-times', methods=['GET'])
@api_login_required
def get_optimal_times():
    try:
        response_patterns = optimal_time.analyze_response_patterns()
        best_days = optimal_time.get_best_days()
        peak_time = optimal_time.get_peak_performance_time()
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        best_day_names = [day_names[day] for day in best_days]
        
        return jsonify({
            'success': True,
            'data': {
                'response_patterns': response_patterns,
                'best_days': best_day_names,
                'peak_performance': peak_time
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/api/campaigns', methods=['GET'])
@api_login_required
def get_campaigns():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, message_template, ab_variant, created_date, active
            FROM campaigns
            ORDER BY created_date DESC
        ''')
        
        campaigns = []
        for row in cursor.fetchall():
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'message_template': row[2],
                'ab_variant': row[3],
                'created_date': row[4],
                'active': bool(row[5])
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': campaigns
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/api/campaigns', methods=['POST'])
@api_login_required
def create_campaign():
    try:
        data = request.get_json()
        
        name = data.get('name')
        message_template = data.get('message_template')
        ab_variant = data.get('ab_variant', 'A')
        
        if not name or not message_template:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO campaigns (name, message_template, ab_variant, created_date)
            VALUES (?, ?, ?, ?)
        ''', (name, message_template, ab_variant, datetime.now().isoformat()))
        
        campaign_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'campaign_id': campaign_id,
                'message': 'Campaign created successfully'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/api/leads/export', methods=['GET'])
@api_login_required
def export_leads():
    try:
        status = request.args.get('status', 'all')
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        if status == 'all':
            cursor.execute('SELECT * FROM leads')
        else:
            cursor.execute('SELECT * FROM leads WHERE status = ?', (status,))
        
        leads = []
        for row in cursor.fetchall():
            leads.append({
                'id': row[0],
                'profile_url': row[1],
                'name': row[2],
                'title': row[3],
                'company': row[4],
                'status': row[5],
                'priority': row[6],
                'added_date': row[7],
                'last_contacted': row[8]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': leads,
            'count': len(leads)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500