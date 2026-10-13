import os
from flask import Flask, send_from_directory, render_template, abort
from werkzeug.utils import secure_filename
from config import config_by_name
from app.extensions import db, csrf
from app.utils.decorators import get_current_user

def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Ensure required folders exist
    os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MEDIA_UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.user import user_bp
    from app.routes.appointments import appointments_bp
    from app.routes.caregiver import caregiver_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    # Exempt REST API blueprint from CSRF for Postman & fetch interoperability
    csrf.exempt(api_bp)

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(caregiver_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Global Template Context
    @app.context_processor
    def inject_global_vars():
        return {
            'current_user': get_current_user(),
            'app_name': 'Elden Care'
        }

    # Template Filters
    @app.template_filter('currency')
    def currency_filter(val):
        try:
            return f"${float(val):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    # Safe Upload Serving Route
    @app.route('/uploads/<folder>/<filename>')
    def uploaded_file(folder, filename):
        if folder not in ('profiles', 'media'):
            abort(404)
        safe_name = secure_filename(filename)
        folder_path = app.config['UPLOAD_FOLDER'] / folder
        return send_from_directory(folder_path, safe_name)

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('public/error.html', error_code=403, error_title="Access Forbidden", error_message="You don't have permission to access this resource."), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('public/error.html', error_code=404, error_title="Page Not Found", error_message="The page or elder care resource you requested could not be located."), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('public/error.html', error_code=500, error_title="System Error", error_message="An unexpected server error occurred. Our team has been notified."), 500

    return app
