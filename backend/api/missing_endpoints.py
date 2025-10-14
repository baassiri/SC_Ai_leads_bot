"""
SC AI Lead Generation System - Missing API Endpoints
Add these endpoints to fix frontend-backend integration

USAGE:
------
1. Import this module in backend/app.py:
   from backend.api.missing_endpoints import register_missing_endpoints

2. Call after creating Flask app:
   register_missing_endpoints(app, db_manager, credentials_manager)

3. Restart Flask server
"""

from flask import jsonify, request


def register_missing_endpoints(app, db_manager, credentials_manager):
    """
    Register all missing API endpoints
    
    Args:
        app: Flask application instance
        db_manager: Database manager instance
        credentials_manager: Credentials manager instance
    """
    
    print("✅ Missing endpoints registered successfully!")
    print("   - GET  /api/settings")
    print("   - POST /api/settings/save")
    print("   - POST /api/settings/test")
    print("   - GET  /api/auth/check-credentials")
    print("   - GET  /api/leads/stats")
    print("   - DELETE /api/leads/<id>")
    print("   - POST /api/leads/<id>/archive")
    print("   - POST /api/leads/bulk-delete")
    print("   - POST /api/leads/bulk-archive")
    
    # ============================================================================
    # SETTINGS ENDPOINTS
    # ============================================================================
    
    @app.route('/api/settings', methods=['GET'])
    def get_settings():
        """Get current system settings"""
        try:
            # FIXED: Use get_all_credentials() instead of get_credentials()
            creds = credentials_manager.get_all_credentials()
            
            return jsonify({
                'success': True,
                'linkedin_email': creds.get('linkedin_email', ''),
                'max_leads': 100,
                'scrape_delay': 3.0,
                'sales_nav_enabled': creds.get('sales_nav_enabled', False),
                'headless_mode': False,
                'messages_per_hour': 15,
                'connection_limit': 50
            })
        except Exception as e:
            print(f"Error getting settings: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/settings/save', methods=['POST'])
    def save_settings():
        """Save system settings (alias for /api/auth/save-credentials)"""
        try:
            data = request.json
            
            # Extract credentials
            linkedin_email = data.get('linkedin_email', '').strip()
            linkedin_password = data.get('linkedin_password', '').strip()
            openai_api_key = data.get('openai_api_key', '').strip()
            sales_nav_enabled = data.get('sales_nav_enabled', False)
            
            if not all([linkedin_email, linkedin_password, openai_api_key]):
                return jsonify({
                    'success': False,
                    'message': 'All credentials are required'
                }), 400
            
            # Save credentials
            success = credentials_manager.save_all_credentials(
                linkedin_email=linkedin_email,
                linkedin_password=linkedin_password,
                openai_api_key=openai_api_key,
                sales_nav_enabled=sales_nav_enabled
            )
            
            if success:
                # Log activity
                db_manager.log_activity(
                    activity_type='settings_saved',
                    description='System settings updated',
                    status='success'
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Settings saved successfully!'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to save settings'
                }), 500
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/settings/test', methods=['POST'])
    def test_settings():
        """Test LinkedIn and OpenAI credentials"""
        try:
            # FIXED: Use get_all_credentials()
            creds = credentials_manager.get_all_credentials()
            
            results = {
                'linkedin': False,
                'openai': False,
                'messages': []
            }
            
            # Check LinkedIn
            if creds.get('linkedin_email') and creds.get('linkedin_password'):
                results['linkedin'] = True
                results['messages'].append('LinkedIn credentials found')
            else:
                results['messages'].append('LinkedIn credentials missing')
            
            # Check OpenAI
            if creds.get('openai_api_key'):
                results['openai'] = True
                results['messages'].append('OpenAI API key found')
            else:
                results['messages'].append('OpenAI API key missing')
            
            all_valid = results['linkedin'] and results['openai']
            
            return jsonify({
                'success': all_valid,
                'message': ' | '.join(results['messages']),
                'details': results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    # ============================================================================
    # AUTH ENDPOINTS
    # ============================================================================
    
    @app.route('/api/auth/check-credentials', methods=['GET'])
    def check_credentials():
        """Check if credentials are configured"""
        try:
            # FIXED: Use the correct method names
            linkedin_creds = credentials_manager.get_linkedin_credentials()
            openai_key = credentials_manager.get_openai_key()
            
            configured = bool(linkedin_creds and openai_key)
            
            return jsonify({
                'success': True,
                'configured': configured,
                'linkedin': bool(linkedin_creds),
                'openai': bool(openai_key)
            })
            
        except Exception as e:
            print(f"Error checking credentials: {str(e)}")
            return jsonify({
                'success': False,
                'configured': False,
                'linkedin': False,
                'openai': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    # ============================================================================
    # LEADS ENDPOINTS
    # ============================================================================
    
    @app.route('/api/leads/stats', methods=['GET'])
    def get_lead_stats():
        """Get lead statistics"""
        try:
            # Get counts from database
            all_leads = db_manager.get_all_leads(limit=1000)
            
            total = len(all_leads)
            qualified = len([l for l in all_leads if l.get('score', 0) >= 70])
            contacted = len([l for l in all_leads if l.get('status') == 'contacted'])
            replied = len([l for l in all_leads if l.get('status') == 'replied'])
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': total,
                    'qualified': qualified,
                    'contacted': contacted,
                    'replied': replied
                }
            })
        except Exception as e:
            print(f"Error getting lead stats: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
    def delete_lead(lead_id):
        """Delete a lead"""
        try:
            success = db_manager.delete_lead(lead_id)
            
            if success:
                db_manager.log_activity(
                    activity_type='lead_deleted',
                    description=f'Lead {lead_id} deleted',
                    status='success'
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Lead deleted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Lead not found'
                }), 404
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/leads/<int:lead_id>/archive', methods=['POST'])
    def archive_lead(lead_id):
        """Archive a lead"""
        try:
            success = db_manager.update_lead_status(lead_id, 'archived')
            
            if success:
                db_manager.log_activity(
                    activity_type='lead_archived',
                    description=f'Lead {lead_id} archived',
                    status='success'
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Lead archived successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Lead not found'
                }), 404
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/leads/bulk-delete', methods=['POST'])
    def bulk_delete_leads():
        """Delete multiple leads"""
        try:
            data = request.json
            lead_ids = data.get('lead_ids', [])
            
            if not lead_ids:
                return jsonify({
                    'success': False,
                    'message': 'No lead IDs provided'
                }), 400
            
            deleted_count = 0
            for lead_id in lead_ids:
                if db_manager.delete_lead(lead_id):
                    deleted_count += 1
            
            db_manager.log_activity(
                activity_type='bulk_delete',
                description=f'{deleted_count} leads deleted',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': f'{deleted_count} leads deleted',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/leads/bulk-archive', methods=['POST'])
    def bulk_archive_leads():
        """Archive multiple leads"""
        try:
            data = request.json
            lead_ids = data.get('lead_ids', [])
            
            if not lead_ids:
                return jsonify({
                    'success': False,
                    'message': 'No lead IDs provided'
                }), 400
            
            archived_count = 0
            for lead_id in lead_ids:
                if db_manager.update_lead_status(lead_id, 'archived'):
                    archived_count += 1
            
            db_manager.log_activity(
                activity_type='bulk_archive',
                description=f'{archived_count} leads archived',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': f'{archived_count} leads archived',
                'archived_count': archived_count
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500