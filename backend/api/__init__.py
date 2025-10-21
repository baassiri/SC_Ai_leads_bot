"""
API Routes Package - Handles all route registrations
Place this file as: backend/api/__init__.py
"""

def register_all_routes(app, db_manager, credentials_manager):
    """Register all API routes"""
    
    # Try to import and register each route module
    # If a module uses Blueprints, register the blueprint
    # If it has a register function, call it
    
    print("📋 Registering API routes...")
    
    # Lead routes
    try:
        from . import lead_routes
        if hasattr(lead_routes, 'lead_routes'):
            # It's a Blueprint
            app.register_blueprint(lead_routes.lead_routes)
            print("✅ Lead routes (Blueprint) registered")
        elif hasattr(lead_routes, 'register_lead_routes'):
            lead_routes.register_lead_routes(app, db_manager)
        else:
            print("⚠️  Lead routes: No registration method found")
    except Exception as e:
        print(f"⚠️  Lead routes error: {str(e)}")
    
    # Message routes
    try:
        from . import message_routes
        if hasattr(message_routes, 'message_routes'):
            app.register_blueprint(message_routes.message_routes)
            print("✅ Message routes (Blueprint) registered")
        elif hasattr(message_routes, 'register_message_routes'):
            message_routes.register_message_routes(app, db_manager)
        else:
            print("⚠️  Message routes: No registration method found")
    except Exception as e:
        print(f"⚠️  Message routes error: {str(e)}")
    
    # Persona routes
    try:
        from . import persona_routes
        if hasattr(persona_routes, 'register_persona_routes'):
            persona_routes.register_persona_routes(app, db_manager)
        else:
            print("⚠️  Persona routes: No registration method found")
    except Exception as e:
        print(f"⚠️  Persona routes error: {str(e)}")
    
    # Template routes
    try:
        from . import template_routes
        if hasattr(template_routes, 'register_template_routes'):
            template_routes.register_template_routes(app, db_manager)
        else:
            print("⚠️  Template routes: No registration method found")
    except Exception as e:
        print(f"⚠️  Template routes error: {str(e)}")
    
    # Timeline routes
    try:
        from . import timeline_routes
        if hasattr(timeline_routes, 'register_timeline_routes'):
            timeline_routes.register_timeline_routes(app, db_manager)
        else:
            print("⚠️  Timeline routes: No registration method found")
    except Exception as e:
        print(f"⚠️  Timeline routes error: {str(e)}")
    
    # Schedule routes  
    try:
        from . import schedule_routes
        if hasattr(schedule_routes, 'register_scheduling_routes'):
            schedule_routes.register_scheduling_routes(app, db_manager)
        else:
            print("⚠️  Schedule routes: No registration method found")
    except Exception as e:
        print(f"⚠️  Schedule routes error: {str(e)}")
    
    # Analytics routes
    try:
        from . import analytics_routes
        if hasattr(analytics_routes, 'register_analytics_routes'):
            analytics_routes.register_analytics_routes(app, db_manager)
        else:
            print("⚠️  Analytics routes: No registration method found")
    except Exception as e:
        print(f"⚠️  Analytics routes error: {str(e)}")
    
    # Missing endpoints
    try:
        from . import missing_endpoints
        if hasattr(missing_endpoints, 'register_missing_endpoints'):
            missing_endpoints.register_missing_endpoints(app, db_manager, credentials_manager)
        else:
            print("⚠️  Missing endpoints: No registration method found")
    except Exception as e:
        print(f"⚠️  Missing endpoints error: {str(e)}")
    
    print("✅ Route registration complete!")


# For backwards compatibility
def register_lead_routes(app, db_manager):
    from . import lead_routes
    if hasattr(lead_routes, 'lead_routes'):
        app.register_blueprint(lead_routes.lead_routes)

def register_message_routes(app, db_manager):
    from . import message_routes
    if hasattr(message_routes, 'message_routes'):
        app.register_blueprint(message_routes.message_routes)

def register_persona_routes(app, db_manager):
    from . import persona_routes
    if hasattr(persona_routes, 'register_persona_routes'):
        persona_routes.register_persona_routes(app, db_manager)

def register_template_routes(app, db_manager):
    from . import template_routes
    if hasattr(template_routes, 'register_template_routes'):
        template_routes.register_template_routes(app, db_manager)

def register_timeline_routes(app, db_manager):
    from . import timeline_routes
    if hasattr(timeline_routes, 'register_timeline_routes'):
        timeline_routes.register_timeline_routes(app, db_manager)

def register_scheduling_routes(app, db_manager):
    from . import schedule_routes
    if hasattr(schedule_routes, 'register_scheduling_routes'):
        schedule_routes.register_scheduling_routes(app, db_manager)

def register_analytics_routes(app, db_manager):
    from . import analytics_routes
    if hasattr(analytics_routes, 'register_analytics_routes'):
        analytics_routes.register_analytics_routes(app, db_manager)

def register_missing_endpoints(app, db_manager, credentials_manager):
    from . import missing_endpoints
    if hasattr(missing_endpoints, 'register_missing_endpoints'):
        missing_endpoints.register_missing_endpoints(app, db_manager, credentials_manager)