"""
Template Routes - Handle message template management
FIXED: Uses SQLAlchemy session methods
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
    app.add_url_rule('/api/templates/<int:template_id>', 'delete_template_route', delete_template, methods=['DELETE'])
    
    print("✅ Template routes registered")

# ============================================================================
# GET ALL TEMPLATES
# ============================================================================

def get_templates():
    """Get all message templates"""
    try:
        with db_manager.session_scope() as session:
            from backend.database.models import MessageTemplate
            
            templates = session.query(MessageTemplate).order_by(
                MessageTemplate.created_at.desc()
            ).all()
            
            template_list = [{
                'id': t.id,
                'template': t.template,
                'created_at': t.created_at.isoformat() if t.created_at else None
            } for t in templates]
        
        return jsonify({
            'success': True,
            'templates': template_list
        })
        
    except Exception as e:
        print(f"❌ Error getting templates: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': True,
            'templates': []
        })

# ============================================================================
# GET SINGLE TEMPLATE
# ============================================================================

def get_template(template_id):
    """Get a single template by ID"""
    try:
        with db_manager.session_scope() as session:
            from backend.database.models import MessageTemplate
            
            template = session.query(MessageTemplate).filter_by(id=template_id).first()
            
            if template:
                return jsonify({
                    'success': True,
                    'template': {
                        'id': template.id,
                        'template': template.template,
                        'created_at': template.created_at.isoformat() if template.created_at else None
                    }
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
        with db_manager.session_scope() as session:
            from backend.database.models import MessageTemplate
            
            new_template = MessageTemplate(
                template=template_text,
                created_at=datetime.now()
            )
            session.add(new_template)
            session.commit()
        
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
        with db_manager.session_scope() as session:
            from backend.database.models import MessageTemplate
            
            template = session.query(MessageTemplate).filter_by(id=template_id).first()
            
            if template:
                session.delete(template)
                session.commit()
                
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