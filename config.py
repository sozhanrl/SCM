import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / 'instance'
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'elden-care-default-secure-key-2026')
    
    # Database configuration
    # Can be MySQL (e.g. mysql+pymysql://user:pass@localhost:3306/elden_care) or SQLite fallback
    raw_db_url = os.getenv('DATABASE_URL', '')
    if not raw_db_url:
        DATABASE_URL = f"sqlite:///{(INSTANCE_DIR / 'elden_care.db').as_posix()}"
    elif raw_db_url.startswith('sqlite:///') and ':memory:' not in raw_db_url:
        rel_sub = raw_db_url.replace('sqlite:///', '')
        if not (len(rel_sub) > 2 and rel_sub[1] == ':'):
            abs_p = (BASE_DIR / rel_sub).resolve().as_posix()
            DATABASE_URL = f"sqlite:///{abs_p}"
        else:
            DATABASE_URL = raw_db_url
    else:
        DATABASE_URL = raw_db_url

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # Uploads
    UPLOAD_FOLDER = BASE_DIR / os.getenv('UPLOAD_FOLDER', 'uploads')
    PROFILE_UPLOAD_FOLDER = UPLOAD_FOLDER / 'profiles'
    MEDIA_UPLOAD_FOLDER = UPLOAD_FOLDER / 'media'
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # 16 MB
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

    # Session & Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    # Password Reset & Email Verification Token Lifetime (seconds)
    RESET_TOKEN_EXPIRATION_SECONDS = int(os.getenv('RESET_TOKEN_EXPIRATION_SECONDS', 3600))

    # Email
    MAIL_BACKEND = os.getenv('MAIL_BACKEND', 'console') # 'console' or 'smtp'
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@eldencare.com')

    # WTForms CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('SECRET_KEY', 'elden-care-csrf-secret-key-2026')

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
