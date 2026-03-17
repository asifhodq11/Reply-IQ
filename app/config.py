import os
import secrets
from datetime import timedelta


class Config:
    """Base configuration."""
    
    # Required keys — using os.environ[] means the app crashes immediately on startup
    # if any of these are missing, which is strictly required by the Bible.
    SECRET_KEY = os.environ['SECRET_KEY']
    
    SUPABASE_URL = os.environ['SUPABASE_URL']
    SUPABASE_ANON_KEY = os.environ['SUPABASE_ANON_KEY']
    SUPABASE_SERVICE_ROLE_KEY = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    
    OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    
    STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']
    STRIPE_WEBHOOK_SECRET = os.environ['STRIPE_WEBHOOK_SECRET']
    STRIPE_PRICE_ID_STARTER = os.environ['STRIPE_PRICE_ID_STARTER']
    
    RESEND_API_KEY = os.environ['RESEND_API_KEY']
    FRONTEND_URL = os.environ['FRONTEND_URL']
    
    # Optional keys — safe to use .get()
    UPTIMEROBOT_HEARTBEAT_URL = os.environ.get('UPTIMEROBOT_HEARTBEAT_URL')

    # Flask built-ins
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Talisman / HTTPS
    FORCE_HTTPS = True


class DevelopmentConfig(Config):
    """Development environment defaults."""
    DEBUG = True
    # In dev, cookies can't be secure if testing on localhost HTTP
    SESSION_COOKIE_SECURE = False
    FORCE_HTTPS = False


class TestingConfig(Config):
    """Testing environment defaults."""
    TESTING = True
    DEBUG = True


class ProductionConfig(Config):
    """Production environment defaults."""
    DEBUG = False  # CRITICAL: Remote code execution vulnerability if True
    TESTING = False


config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
