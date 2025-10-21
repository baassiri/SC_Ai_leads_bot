"""
SC AI Lead Generation System - Main Flask Application
SIMPLE VERSION - Works with any route style
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import configuration
from config import Config

# Import database and managers
from database.db_manager import DatabaseManager
from credentials_manager import credentials_manager

# Initialize Flask app
app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

# Load configuration
app.config.from_object(Config)

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": Config.CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize database manager
db_manager = DatabaseManager()

print("🚀 SC AI Lead Generation System Starting...")
print(f"📁 Database: {Config.get_database_path()}")
print(f"🌍 Environment: {Config.FLASK_ENV}")

# ============================================================================
# REGISTER ALL ROUTES - SMART LOADER
# ============================================================================

print("📋 Registering API routes...")

# Try different import styles for each route module
route_modules = [
    'lead_routes',
    'message_routes', 
    'persona_routes',
    'template_routes',
    'timeline_routes',
    'schedule_routes',
    'analytics_routes',
    'missing_endpoints'
]

for module_name in route_modules:
    try:
        # Import the module
        module = __import__(f'api.{module_name}', fromlist=[module_name])
        
        # Check if it's a Blueprint
        if hasattr(module, module_name):
            blueprint = getattr(module, module_name)
            app.register_blueprint(blueprint)
            print(f"✅ {module_name} (Blueprint) registered")
        
        # Check if it has a register function
        elif hasattr(module, f'register_{module_name}'):
            register_func = getattr(module, f'register_{module_name}')
            if module_name == 'missing_endpoints':
                register_func(app, db_manager, credentials_manager)
            else:
                register_func(app, db_manager)
            print(f"✅ {module_name} (Function) registered")
        
        # Check for alternate register function names
        elif hasattr(module, 'register_scheduling_routes') and module_name == 'schedule_routes':
            module.register_scheduling_routes(app, db_manager)
            print(f"✅ {module_name} (Function) registered")
        
        else:
            print(f"⚠️  {module_name}: No registration method found")
            
    except Exception as e:
        print(f"❌ {module_name} error: {str(e)}")

print("✅ Route registration complete!")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found',
            'path': request.path
        }), 404
    return jsonify({'error': '404 Not Found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error)
    }), 500


# ============================================================================
# MAIN PAGE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    return jsonify({
        'status': 'running',
        'message': 'SC AI Lead Generation System',
        'version': '1.0.0'
    })


@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    return jsonify({'message': 'Dashboard endpoint'})


# ============================================================================
# AUTHENTICATION & CREDENTIALS API
# ============================================================================

@app.route('/api/auth/save-credentials', methods=['POST'])
def save_credentials():
    """Save user credentials"""
    try:
        data = request.json
        
        linkedin_email = data.get('linkedin_email', '').strip()
        linkedin_password = data.get('linkedin_password', '').strip()
        openai_api_key = data.get('openai_api_key', '').strip()
        sales_nav_enabled = data.get('sales_nav_enabled', False)
        
        if not linkedin_email or not linkedin_password:
            return jsonify({
                'success': False,
                'message': 'LinkedIn credentials are required'
            }), 400
        
        if not openai_api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key is required'
            }), 400
        
        success = credentials_manager.save_all_credentials(
            linkedin_email=linkedin_email,
            linkedin_password=linkedin_password,
            openai_api_key=openai_api_key,
            sales_nav_enabled=sales_nav_enabled
        )
        
        if success:
            db_manager.log_activity(
                activity_type='credentials_saved',
                description='System credentials updated',
                status='success'
            )
            
            return jsonify({
                'success': True,
                'message': 'Credentials saved successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save credentials'
            }), 500
    
    except Exception as e:
        print(f"❌ Error saving credentials: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/auth/test-connection', methods=['POST'])
def test_connection():
    """Test API connections"""
    try:
        data = request.json or {}
        service = data.get('service', 'all')
        
        results = {
            'linkedin': False,
            'openai': False,
            'messages': []
        }
        
        if service in ['all', 'linkedin']:
            creds = credentials_manager.get_linkedin_credentials()
            if creds and creds.get('email'):
                results['linkedin'] = True
                results['messages'].append('✅ LinkedIn credentials configured')
            else:
                results['messages'].append('❌ LinkedIn credentials missing')
        
        if service in ['all', 'openai']:
            openai_key = credentials_manager.get_openai_key()
            if openai_key:
                if openai_key.startswith('sk-') and len(openai_key) > 20:
                    results['openai'] = True
                    results['messages'].append('✅ OpenAI API key configured')
                else:
                    results['messages'].append('⚠️ OpenAI API key format invalid')
            else:
                results['messages'].append('❌ OpenAI API key missing')
        
        all_valid = results['linkedin'] and results['openai']
        
        return jsonify({
            'success': all_valid,
            'message': '\n'.join(results['messages']),
            'details': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================================
# BOT CONTROL API
# ============================================================================

bot_state = {
    'running': False,
    'current_activity': 'Stopped',
    'leads_scraped': 0,
    'progress': 0,
    'started_at': None
}


@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Get current bot status"""
    return jsonify({
        'success': True,
        'status': bot_state
    })


@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the LinkedIn scraping bot"""
    try:
        if bot_state['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is already running'
            })
        
        personas = db_manager.get_all_personas()
        
        if not personas or len(personas) == 0:
            return jsonify({
                'success': False,
                'message': 'No personas found. Please create a persona first.'
            }), 400
        
        bot_state['running'] = True
        bot_state['current_activity'] = 'Starting...'
        bot_state['leads_scraped'] = 0
        bot_state['progress'] = 0
        bot_state['started_at'] = datetime.now().isoformat()
        
        db_manager.log_activity(
            activity_type='bot_started',
            description=f'Bot started with {len(personas)} persona(s)',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'Bot started! Targeting {len(personas)} personas.',
            'personas': len(personas)
        })
    
    except Exception as e:
        bot_state['running'] = False
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    try:
        if not bot_state['running']:
            return jsonify({
                'success': False,
                'message': 'Bot is not running'
            })
        
        leads_scraped = bot_state['leads_scraped']
        
        bot_state['running'] = False
        bot_state['current_activity'] = 'Stopped'
        bot_state['progress'] = 0
        
        db_manager.log_activity(
            activity_type='bot_stopped',
            description=f'Bot stopped. Scraped {leads_scraped} leads.',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'Bot stopped successfully. Scraped {leads_scraped} leads.',
            'leads_scraped': leads_scraped
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_ok = db_manager.test_connection()
        creds = credentials_manager.get_all_credentials()
        creds_ok = bool(creds.get('linkedin_email') and creds.get('openai_api_key'))
        
        return jsonify({
            'status': 'healthy' if db_ok and creds_ok else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected' if db_ok else 'error',
            'credentials': 'configured' if creds_ok else 'missing',
            'version': '1.0.0'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎯 SC AI LEAD GENERATION SYSTEM")
    print("="*70)
    print(f"📍 Server: http://localhost:5000")
    print(f"📊 Dashboard: http://localhost:5000/dashboard")
    print(f"💾 Database: {Config.get_database_path()}")
    print(f"🔑 Credentials: {'Configured' if credentials_manager.get_all_credentials().get('linkedin_email') else 'Not configured'}")
    print("="*70 + "\n")
    
    Config.ensure_directories()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG,
        threaded=True
    )