"""
Template Routes - Handle message template management
"""

from flask import jsonify, request
from datetime import datetime
import traceback

db_manager = None

def register_template_routes(app, database_manager):
    """Register all template routes"""
    global db_manager
    db_manager = database_manager
    
    app.add_url_rule('/api/templates', 'get_templates', get_templates, methods=['GET'])
    app.add_url_rule('/api/templates/<int:template_id>', 'get_template', get_template, methods=['GET'])
    app.add_url_rule('/api/templates/save', 'save_template', save_template, methods=['POST'])
    app.add_url_rule('/api/templates/<int:template_id>', 'delete_template', delete_template, methods=['DELETE'])
    
    print("✅ Template routes registered")

# ============================================================================
# GET ALL TEMPLATES
# ============================================================================

def get_templates():
    """Get all message templates"""
    try:
        templates = db_manager.execute_query(
            "SELECT * FROM message_templates ORDER BY created_at DESC"
        )
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        print(f"❌ Error getting templates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# GET SINGLE TEMPLATE
# ============================================================================

def get_template(template_id):
    """Get a single template by ID"""
    try:
        template = db_manager.execute_query(
            "SELECT * FROM message_templates WHERE id=?",
            [template_id]
        )
        
        if template:
            return jsonify({
                'success': True,
                'template': template[0]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
            
    except Exception as e:
        print(f"❌ Error getting template: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# SAVE TEMPLATE
# ============================================================================

def save_template():
    """Save a new message template"""
    try:
        data = request.json
        template_text = data.get('template', '').strip()
        
        if not template_text:
            return jsonify({
                'success': False,
                'error': 'Template text is required'
            }), 400
        
        # Insert template
        db_manager.execute_update(
            "INSERT INTO message_templates (template, created_at) VALUES (?, ?)",
            [template_text, datetime.now()]
        )
        
        return jsonify({
            'success': True,
            'message': 'Template saved successfully'
        })
        
    except Exception as e:
        print(f"❌ Error saving template: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# DELETE TEMPLATE
# ============================================================================

def delete_template(template_id):
    """Delete a template"""
    try:
        result = db_manager.execute_update(
            "DELETE FROM message_templates WHERE id=?",
            [template_id]
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Template deleted'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
            
    except Exception as e:
        print(f"❌ Error deleting template: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500