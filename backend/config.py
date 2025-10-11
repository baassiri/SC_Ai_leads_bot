"""
SC AI Lead Generation System - Configuration
Handles environment variables and application settings
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')


class Config:
    """Base configuration class"""
    
    # ===========================
    # Application Settings
    # ===========================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    FLASK_APP = os.getenv('FLASK_APP', 'backend/app.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # ===========================
    # Database Configuration
    # ===========================
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{basedir}/data/database.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # Log SQL queries in debug mode
    
    # ===========================
    # OpenAI Configuration
    # ===========================
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    
    # ===========================
    # LinkedIn Configuration
    # ===========================
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL', '')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', '')
    SALES_NAVIGATOR_ENABLED = os.getenv('SALES_NAVIGATOR_ENABLED', 'True').lower() == 'true'
    
    # Scraping settings
    SCRAPE_DELAY_MIN = int(os.getenv('SCRAPE_DELAY_MIN', '2'))
    SCRAPE_DELAY_MAX = int(os.getenv('SCRAPE_DELAY_MAX', '5'))
    MAX_LEADS_PER_SESSION = int(os.getenv('MAX_LEADS_PER_SESSION', '100'))
    
    # ===========================
    # HubSpot Configuration
    # ===========================
    HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY', '')
    HUBSPOT_ENABLED = os.getenv('HUBSPOT_ENABLED', 'False').lower() == 'true'
    
    # ===========================
    # Automation Settings
    # ===========================
    MESSAGES_PER_HOUR = int(os.getenv('MESSAGES_PER_HOUR', '15'))
    CONNECTION_REQUEST_LIMIT = int(os.getenv('CONNECTION_REQUEST_LIMIT', '10'))
    FOLLOW_UP_DELAY_DAYS = int(os.getenv('FOLLOW_UP_DELAY_DAYS', '3'))
    MAX_FOLLOW_UPS = int(os.getenv('MAX_FOLLOW_UPS', '2'))
    
    # ===========================
    # Redis & Celery (for background tasks)
    # ===========================
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    
    # ===========================
    # File Paths
    # ===========================
    BASE_DIR = basedir
    DATA_DIR = basedir / 'data'
    UPLOAD_DIR = DATA_DIR / 'uploads'
    EXPORT_DIR = DATA_DIR / 'exports'
    PERSONA_DIR = DATA_DIR / 'personas'
    LOG_DIR = basedir / 'logs'
    
    # Create directories if they don't exist
    for directory in [DATA_DIR, UPLOAD_DIR, EXPORT_DIR, PERSONA_DIR, LOG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # ===========================
    # Logging Configuration
    # ===========================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = LOG_DIR / 'app.log'
    
    # ===========================
    # Security
    # ===========================
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000').split(',')
    
    # ===========================
    # Target Personas
    # ===========================
    PERSONAS = [
        'Plastic Surgeon',
        'Dermatologist',
        'Med Spa Owner',
        'Day Spa',
        'Wellness Center',
        'Aesthetic Clinic'
    ]
    
    # ===========================
    # Lead Scoring Weights
    # ===========================
    SCORING_WEIGHTS = {
        'title_match': 0.35,      # 35% weight for job title relevance
        'company_size': 0.25,     # 25% weight for company size
        'geography': 0.20,        # 20% weight for location match
        'profile_quality': 0.20   # 20% weight for profile completeness
    }
    
    # ===========================
    # Message Templates
    # ===========================
    MESSAGE_TYPES = [
        'connection_request',
        'follow_up_1',
        'follow_up_2'
    ]
    
    @staticmethod
    def validate():
        """Validate critical configuration"""
        errors = []
        
        if not Config.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set")
        
        if not Config.LINKEDIN_EMAIL or not Config.LINKEDIN_PASSWORD:
            errors.append("LinkedIn credentials not set")
        
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
    
    @staticmethod
    def get_project_root():
        """Get project root directory"""
        return Config.BASE_DIR
    
    @staticmethod
    def get_database_path():
        """Get database file path"""
        if Config.DATABASE_URL.startswith('sqlite:///'):
            return Config.DATABASE_URL.replace('sqlite:///', '')
        return None


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    TESTING = False
    
    # Use PostgreSQL in production
    if not os.getenv('DATABASE_URL'):
        raise ValueError("DATABASE_URL must be set in production")


class TestingConfig(Config):
    """Testing-specific configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory database for tests


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get current configuration based on FLASK_ENV"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
