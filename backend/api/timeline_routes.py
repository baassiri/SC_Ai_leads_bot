"""
Lead Timeline API Routes
Provides endpoints for lead activity timeline
"""

from flask import jsonify, request
from backend.ai_engine.lead_timeline import timeline_manager


def register_timeline_routes(app, db_manager):
    """Register all timeline routes"""
    
    @app.route('/api/leads/<int:lead_id>/timeline', methods=['GET'])
    def get_lead_timeline(lead_id):
        """Get complete timeline for a lead"""
        try:
            timeline = timeline_manager.get_timeline(lead_id)
            
            return jsonify({
                'success': True,
                'timeline': timeline,
                'total_events': len(timeline)
            })
            
        except Exception as e:
            print(f"Error getting timeline: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/leads/<int:lead_id>/timeline/summary', methods=['GET'])
    def get_lead_timeline_summary(lead_id):
        """Get timeline summary stats"""
        try:
            summary = timeline_manager.get_summary(lead_id)
            
            return jsonify({
                'success': True,
                'summary': summary
            })
            
        except Exception as e:
            print(f"Error getting timeline summary: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/leads/<int:lead_id>/timeline/export', methods=['GET'])
    def export_lead_timeline(lead_id):
        """Export timeline as JSON"""
        try:
            timeline = timeline_manager.get_timeline(lead_id)
            summary = timeline_manager.get_summary(lead_id)
            
            # Get lead info
            lead = db_manager.get_lead_by_id(lead_id)
            
            export_data = {
                'lead': {
                    'id': lead_id,
                    'name': lead.get('name') if lead else 'Unknown',
                    'title': lead.get('title') if lead else '',
                    'company': lead.get('company') if lead else ''
                },
                'summary': summary,
                'timeline': timeline,
                'exported_at': timeline[0]['timestamp'] if timeline else None
            }
            
            return jsonify({
                'success': True,
                'export': export_data
            })
            
        except Exception as e:
            print(f"Error exporting timeline: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500