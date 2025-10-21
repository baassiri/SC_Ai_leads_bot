"""
Analytics Routes - Dashboard analytics and statistics
"""

from flask import jsonify, request
from datetime import datetime, timedelta


def register_analytics_routes(app, db_manager):
    """Register analytics routes"""
    
    @app.route('/api/analytics/dashboard', methods=['GET'])
    def analytics_dashboard():
        """Get dashboard analytics data"""
        try:
            # Get time range from query params
            days = int(request.args.get('days', 7))
            
            # Get stats from database
            stats = db_manager.get_dashboard_stats()
            
            # Mock chart data (replace with real data)
            chart_data = generate_chart_data(days)
            
            return jsonify({
                'success': True,
                'stats': stats,
                'charts': chart_data
            })
        
        except Exception as e:
            print(f"Error in analytics_dashboard: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/analytics/leads', methods=['GET'])
    def analytics_leads():
        """Get lead analytics"""
        try:
            leads = db_manager.get_all_leads()
            
            # Calculate metrics
            total = len(leads)
            qualified = len([l for l in leads if l.get('ai_score', 0) >= 70])
            contacted = len([l for l in leads if l.get('status') == 'contacted'])
            replied = len([l for l in leads if l.get('status') == 'replied'])
            
            return jsonify({
                'success': True,
                'metrics': {
                    'total': total,
                    'qualified': qualified,
                    'contacted': contacted,
                    'replied': replied,
                    'qualification_rate': (qualified / total * 100) if total > 0 else 0,
                    'response_rate': (replied / contacted * 100) if contacted > 0 else 0
                }
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/analytics/messages', methods=['GET'])
    def analytics_messages():
        """Get message analytics"""
        try:
            messages = db_manager.get_all_messages()
            
            # Calculate metrics
            total = len(messages)
            draft = len([m for m in messages if m.get('status') == 'draft'])
            approved = len([m for m in messages if m.get('status') == 'approved'])
            sent = len([m for m in messages if m.get('status') == 'sent'])
            
            return jsonify({
                'success': True,
                'metrics': {
                    'total': total,
                    'draft': draft,
                    'approved': approved,
                    'sent': sent,
                    'approval_rate': (approved / total * 100) if total > 0 else 0,
                    'send_rate': (sent / total * 100) if total > 0 else 0
                }
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    print("✅ Analytics routes registered")


def generate_chart_data(days):
    """Generate mock chart data"""
    # In production, this would query actual data from database
    
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
    
    return {
        'messages_over_time': {
            'labels': dates,
            'sent': [5, 8, 12, 15, 10, 14, 18],
            'replies': [1, 2, 3, 4, 2, 3, 5]
        },
        'lead_quality': {
            'labels': ['High (90-100)', 'Good (70-89)', 'Medium (50-69)', 'Low (<50)'],
            'data': [15, 42, 28, 15]
        },
        'conversion_funnel': {
            'labels': ['Scraped', 'Qualified', 'Contacted', 'Replied', 'Meeting'],
            'data': [100, 75, 50, 20, 5]
        }
    }