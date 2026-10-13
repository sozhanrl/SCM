from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify, abort
from app.extensions import db
from app.models.user import User

def get_current_user():
    """Returns the current logged-in User instance or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        session.clear()
        return None
    return user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Enforces role-based permissions strictly on the backend."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Authentication required.'}), 401
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.path))
            
            if user.role not in allowed_roles:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Access forbidden: Insufficient permissions.'}), 403
                flash('You do not have permission to access that resource.', 'danger')
                if user.is_admin:
                    return redirect(url_for('admin.dashboard'))
                elif user.is_caregiver:
                    return redirect(url_for('caregiver.dashboard'))
                return redirect(url_for('user.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('admin')(f)

def caregiver_or_admin_required(f):
    return role_required('admin', 'caregiver')(f)
