from flask import session, redirect, url_for, request
from functools import wraps
import secrets
import hashlib
from datetime import datetime, timedelta

class Auth:
    def __init__(self):
        self.secret_key = secrets.token_hex(32)
        self.session_timeout = timedelta(hours=24)
        
    def generate_session_token(self, user_id):
        timestamp = datetime.now().isoformat()
        data = f"{user_id}:{timestamp}:{self.secret_key}"
        token = hashlib.sha256(data.encode()).hexdigest()
        return token
        
    def create_session(self, user_id, username):
        token = self.generate_session_token(user_id)
        session['user_id'] = user_id
        session['username'] = username
        session['token'] = token
        session['created_at'] = datetime.now().isoformat()
        session.permanent = True
        return token
        
    def destroy_session(self):
        session.clear()
        
    def is_authenticated(self):
        if 'user_id' not in session or 'token' not in session:
            return False
            
        created_at = session.get('created_at')
        if created_at:
            created_time = datetime.fromisoformat(created_at)
            if datetime.now() - created_time > self.session_timeout:
                self.destroy_session()
                return False
        
        return True
        
    def get_current_user(self):
        if self.is_authenticated():
            return {
                'user_id': session.get('user_id'),
                'username': session.get('username')
            }
        return None
        
    def refresh_session(self):
        if self.is_authenticated():
            session['created_at'] = datetime.now().isoformat()
            return True
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = Auth()
        if not auth.is_authenticated():
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = Auth()
        if not auth.is_authenticated():
            return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401
        return f(*args, **kwargs)
    return decorated_function

auth_manager = Auth()