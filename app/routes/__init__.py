from app.routes.public import public_bp
from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.user import user_bp
from app.routes.appointments import appointments_bp
from app.routes.caregiver import caregiver_bp
from app.routes.admin import admin_bp
from app.routes.api import api_bp

__all__ = [
    'public_bp',
    'auth_bp',
    'profile_bp',
    'user_bp',
    'appointments_bp',
    'caregiver_bp',
    'admin_bp',
    'api_bp'
]
