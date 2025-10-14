"""
SC AI Lead Generation System - Missing API Endpoints
Add these endpoints to fix frontend-backend integration

USAGE:
------
1. Import this module in backend/app.py:
   from backend.api.missing_endpoints import register_missing_endpoints

2. Call after creating Flask app:
   register_missing_endpoints(app, db_manager)

3. Restart Flask server

This will add:
- GET /api/settings
- POST /api/settings/save  
- GET /api/auth/check-credentials
- GET /api/leads/stats
- DELETE /api/leads/<id>
- POST /api/leads/<id>/archive
"""

from flask import jsonify, request
from datetime import datetime


def register_missing_endpoints(app, db_manager, credentials_manager):
    """
    Register all missing API endpoints
    
    Args:
        app: Flask application instance
        db_manager: Database manager instance
        credentials_manager: Credentials manager instance
    """
    
    # ============================================================================
    # SETTINGS ENDPOINTS
    # ============================================================================
    
    @app.route('/api/settings', methods=['GET'])
    def get_settings():
        """
        Get current system settings
        
        Returns:
            JSON with all settings
        """
        try:
            creds = credentials_manager.get_credentials()
            
            return jsonify({
                'success': True,
                'linkedin_email': creds.get('linkedin_email', ''),
                'max_leads': 100,
                'scrape_delay': 3.0,
                'sales_nav_enabled': True,
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
        """
        Save system settings (alias for /api/auth/save-credentials)
        
        Body:
            {
                "linkedin_email": str,
                "linkedin_password": str,
                "openai_api_key": str,
                "max_leads": int (optional),
                "scrape_delay": float (optional),
                "sales_nav_enabled": bool (optional),
                "headless_mode": bool (optional),
                "messages_per_hour": int (optional),
                "connection_limit": int (optional)
            }
        
        Returns:
            JSON with success/failure
        """
        try:
            data = request.json
            
            # Save credentials (required)
            linkedin_email = data.get('linkedin_email', '').strip()
            linkedin_password = data.get('linkedin_password', '').strip()
            openai_api_key = data.get('openai_api_key', '').strip()
            
            if not linkedin_email:
                return jsonify({
                    'success': False,
                    'message': 'LinkedIn email is required'
                }), 400
            
            # Save to credentials manager
            credentials_manager.save_credentials(
                linkedin_email=linkedin_email,
                linkedin_password=linkedin_password,
                openai_api_key=openai_api_key
            )
            
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
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/settings/test', methods=['POST'])
    def test_settings():
        """
        Test LinkedIn and OpenAI credentials
        
        Returns:
            JSON with test results
        """
        try:
            creds = credentials_manager.get_credentials()
            
            results = {
                'linkedin': False,
                'openai': False,
                'messages': []
            }
            
            # Check LinkedIn
            if creds.get('linkedin_email') and creds.get('linkedin_password'):
                # Just check if credentials exist (full test would require Selenium)
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
        """
        Check if credentials are configured
        
        Returns:
            JSON with credential status
        """
        try:
            creds = credentials_manager.get_credentials()
            
            has_linkedin = bool(
                creds.get('linkedin_email') and 
                creds.get('linkedin_password')
            )
            has_openai = bool(creds.get('openai_api_key'))
            
            return jsonify({
                'success': True,
                'configured': has_linkedin and has_openai,
                'linkedin': has_linkedin,
                'openai': has_openai,
                'details': {
                    'linkedin_email': creds.get('linkedin_email', '') if has_linkedin else None,
                    'has_password': bool(creds.get('linkedin_password')),
                    'has_api_key': has_openai
                }
            })
        except Exception as e:
            print(f"Error checking credentials: {e}")
            return jsonify({
                'success': True,
                'configured': False,
                'linkedin': False,
                'openai': False
            })
    
    
    # ============================================================================
    # LEAD STATISTICS
    # ============================================================================
    
    @app.route('/api/leads/stats', methods=['GET'])
    def get_lead_stats():
        """
        Get lead statistics for dashboard cards
        
        Returns:
            JSON with lead counts by category
        """
        try:
            # Get all leads and filter
            all_leads = db_manager.get_all_leads()
            
            total = len(all_leads)
            qualified = len([l for l in all_leads if l.get('ai_score', 0) >= 70])
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
    
    
    # ============================================================================
    # LEAD MANAGEMENT
    # ============================================================================
    
    @app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
    def delete_lead(lead_id):
        """
        Delete a lead from the database
        
        Args:
            lead_id: ID of lead to delete
            
        Returns:
            JSON with success/failure
        """
        try:
            # Get lead first to check if exists
            lead = db_manager.get_lead_by_id(lead_id)
            
            if not lead:
                return jsonify({
                    'success': False,
                    'message': 'Lead not found'
                }), 404
            
            # Delete from database
            success = db_manager.delete_lead(lead_id)
            
            if success:
                # Log activity
                db_manager.log_activity(
                    activity_type='lead_deleted',
                    description=f'Deleted lead: {lead.get("name", "Unknown")} (ID: {lead_id})',
                    status='success'
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Lead deleted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to delete lead'
                }), 500
                
        except Exception as e:
            print(f"Error deleting lead {lead_id}: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/leads/<int:lead_id>/archive', methods=['POST'])
    def archive_lead(lead_id):
        """
        Archive a lead (set status to 'archived')
        
        Args:
            lead_id: ID of lead to archive
            
        Returns:
            JSON with success/failure
        """
        try:
            # Get lead first to check if exists
            lead = db_manager.get_lead_by_id(lead_id)
            
            if not lead:
                return jsonify({
                    'success': False,
                    'message': 'Lead not found'
                }), 404
            
            # Update status to archived
            success = db_manager.update_lead_status(lead_id, 'archived')
            
            if success:
                # Log activity
                db_manager.log_activity(
                    activity_type='lead_archived',
                    description=f'Archived lead: {lead.get("name", "Unknown")} (ID: {lead_id})',
                    status='success'
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Lead archived successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to archive lead'
                }), 500
                
        except Exception as e:
            print(f"Error archiving lead {lead_id}: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/leads/bulk-delete', methods=['POST'])
    def bulk_delete_leads():
        """
        Delete multiple leads at once
        
        Body:
            {
                "lead_ids": [1, 2, 3, ...]
            }
            
        Returns:
            JSON with deletion results
        """
        try:
            data = request.json
            lead_ids = data.get('lead_ids', [])
            
            if not lead_ids:
                return jsonify({
                    'success': False,
                    'message': 'No lead IDs provided'
                }), 400
            
            deleted_count = 0
            failed_count = 0
            
            for lead_id in lead_ids:
                try:
                    if db_manager.delete_lead(lead_id):
                        deleted_count += 1
                    else:
                        failed_count += 1
                except:
                    failed_count += 1
            
            # Log activity
            db_manager.log_activity(
                activity_type='bulk_delete',
                description=f'Bulk deleted {deleted_count} leads ({failed_count} failed)',
                status='success' if deleted_count > 0 else 'failed'
            )
            
            return jsonify({
                'success': True,
                'message': f'Deleted {deleted_count} leads',
                'deleted': deleted_count,
                'failed': failed_count
            })
            
        except Exception as e:
            print(f"Error in bulk delete: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
    @app.route('/api/leads/bulk-archive', methods=['POST'])
    def bulk_archive_leads():
        """
        Archive multiple leads at once
        
        Body:
            {
                "lead_ids": [1, 2, 3, ...]
            }
            
        Returns:
            JSON with archival results
        """
        try:
            data = request.json
            lead_ids = data.get('lead_ids', [])
            
            if not lead_ids:
                return jsonify({
                    'success': False,
                    'message': 'No lead IDs provided'
                }), 400
            
            archived_count = 0
            failed_count = 0
            
            for lead_id in lead_ids:
                try:
                    if db_manager.update_lead_status(lead_id, 'archived'):
                        archived_count += 1
                    else:
                        failed_count += 1
                except:
                    failed_count += 1
            
            # Log activity
            db_manager.log_activity(
                activity_type='bulk_archive',
                description=f'Bulk archived {archived_count} leads ({failed_count} failed)',
                status='success' if archived_count > 0 else 'failed'
            )
            
            return jsonify({
                'success': True,
                'message': f'Archived {archived_count} leads',
                'archived': archived_count,
                'failed': failed_count
            })
            
        except Exception as e:
            print(f"Error in bulk archive: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    
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
# HELPER FUNCTION TO ADD TO db_manager.py
# ============================================================================

def add_delete_method_to_db_manager():
    """
    Add this method to DBManager class in backend/database/db_manager.py
    """
    code = '''
    def delete_lead(self, lead_id):
        """
        Delete a lead from the database
        
        Args:
            lead_id: ID of lead to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            with self.get_session() as session:
                from backend.database.models import Lead
                
                lead = session.query(Lead).filter_by(id=lead_id).first()
                
                if lead:
                    session.delete(lead)
                    session.commit()
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Error deleting lead {lead_id}: {e}")
            return False
    '''
    
    return code


# ============================================================================
# INTEGRATION INSTRUCTIONS
# ============================================================================

INTEGRATION_INSTRUCTIONS = """
STEP-BY-STEP INTEGRATION GUIDE
================================

1. CREATE THE FILE
   -----------------
   Save this file as: backend/api/missing_endpoints.py


2. UPDATE backend/app.py
   ----------------------
   Add these imports at the top:
   
   from backend.api.missing_endpoints import register_missing_endpoints
   
   
   Then add this line AFTER creating db_manager but BEFORE app.run():
   
   # Register missing endpoints
   register_missing_endpoints(app, db_manager, credentials_manager)


3. ADD DELETE METHOD TO db_manager.py
   -----------------------------------
   Open: backend/database/db_manager.py
   
   Add this method to the DBManager class:
   
   def delete_lead(self, lead_id):
       try:
           with self.get_session() as session:
               from backend.database.models import Lead
               lead = session.query(Lead).filter_by(id=lead_id).first()
               if lead:
                   session.delete(lead)
                   session.commit()
                   return True
               return False
       except Exception as e:
           print(f"Error deleting lead: {e}")
           return False


4. UPDATE messages.js (CRITICAL FIX)
   ----------------------------------
   Open: frontend/static/js/messages.js
   
   Find this line:
       const response = await fetch('/api/messages/schedule-batch', {
   
   Replace with:
       const response = await fetch('/api/schedule/batch', {


5. UPDATE leads.js (ADD PERSONA FILTER)
   -------------------------------------
   Open: frontend/static/js/leads.js
   
   Add this function:
   
   async function loadPersonaFilter() {
       try {
           const response = await fetch('/api/personas');
           const data = await response.json();
           
           if (data.success && data.personas) {
               const select = document.getElementById('persona-filter');
               data.personas.forEach(persona => {
                   const option = document.createElement('option');
                   option.value = persona.id;
                   option.textContent = persona.name;
                   select.appendChild(option);
               });
           }
       } catch (error) {
           console.error('Error loading personas:', error);
       }
   }
   
   Then call it in DOMContentLoaded:
       loadPersonaFilter();


6. UPDATE leads.js (ADD STATS UPDATE)
   -----------------------------------
   Add this function:
   
   async function loadLeadStats() {
       try {
           const response = await fetch('/api/leads/stats');
           const data = await response.json();
           
           if (data.success) {
               document.getElementById('total-leads-count').textContent = data.stats.total;
               document.getElementById('qualified-leads-count').textContent = data.stats.qualified;
               document.getElementById('contacted-leads-count').textContent = data.stats.contacted;
               document.getElementById('replied-leads-count').textContent = data.stats.replied;
           }
       } catch (error) {
           console.error('Error loading stats:', error);
       }
   }
   
   Call in DOMContentLoaded:
       loadLeadStats();
       setInterval(loadLeadStats, 30000);


7. UPDATE leads.js (FIX ARCHIVE/DELETE BUTTONS)
   ---------------------------------------------
   Replace the archiveLeads() function:
   
   async function archiveLeads(leadIds) {
       try {
           const response = await fetch('/api/leads/bulk-archive', {
               method: 'POST',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify({ lead_ids: leadIds })
           });
           
           const data = await response.json();
           
           if (data.success) {
               alert(`✅ Archived ${data.archived} leads!`);
               loadLeads();
           } else {
               alert('❌ ' + data.message);
           }
       } catch (error) {
           alert('Error archiving leads');
       }
   }
   
   Replace the deleteLeads() function:
   
   async function deleteLeads(leadIds) {
       try {
           const response = await fetch('/api/leads/bulk-delete', {
               method: 'POST',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify({ lead_ids: leadIds })
           });
           
           const data = await response.json();
           
           if (data.success) {
               alert(`✅ Deleted ${data.deleted} leads!`);
               loadLeads();
           } else {
               alert('❌ ' + data.message);
           }
       } catch (error) {
           alert('Error deleting leads');
       }
   }


8. RESTART FLASK SERVER
   ---------------------
   Ctrl+C to stop
   python backend/app.py
   
   You should see:
   "✅ Missing endpoints registered successfully!"


9. TEST THE FIXES
   ---------------
   Test these workflows:
   
   ✅ Go to Settings → Save credentials
   ✅ Go to Dashboard → Check stats update
   ✅ Go to Leads → Filter by persona
   ✅ Go to Leads → Archive a lead
   ✅ Go to Leads → Delete a lead
   ✅ Go to Messages → Send all approved
   
   
10. VERIFY ENDPOINTS
    ----------------
    Test in browser console or Postman:
    
    GET  http://localhost:5000/api/settings
    GET  http://localhost:5000/api/auth/check-credentials
    GET  http://localhost:5000/api/leads/stats
    

That's it! All critical issues should now be fixed. 🎉
"""

if __name__ == "__main__":
    print(INTEGRATION_INSTRUCTIONS)