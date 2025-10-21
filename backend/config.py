"""
Configuration Module for SC AI Lead Generation System
Handles all application settings and environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""
    
    # ========================================================================
    # PATHS
    # ========================================================================
    
    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    UPLOAD_DIR = DATA_DIR / 'uploads'
    EXPORT_DIR = DATA_DIR / 'exports'
    LOG_DIR = BASE_DIR / 'logs'
    
    # Database
    DATABASE_PATH = DATA_DIR / 'database.db'
    
    # ========================================================================
    # FLASK SETTINGS
    # ========================================================================
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # ========================================================================
    # CORS SETTINGS
    # ========================================================================
    
    CORS_ORIGINS = [
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'http://localhost:3000',  # React dev server if used
    ]
    
    # ========================================================================
    # API KEYS
    # ========================================================================
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    
    # ========================================================================
    # LINKEDIN SETTINGS
    # ========================================================================
    
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL', '')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', '')
    SALES_NAVIGATOR_ENABLED = os.getenv('SALES_NAVIGATOR_ENABLED', 'False').lower() == 'true'
    
    # Scraping limits
    SCRAPE_DELAY_MIN = int(os.getenv('SCRAPE_DELAY_MIN', '2'))
    SCRAPE_DELAY_MAX = int(os.getenv('SCRAPE_DELAY_MAX', '5'))
    MAX_LEADS_PER_SESSION = int(os.getenv('MAX_LEADS_PER_SESSION', '100'))
    
    # ========================================================================
    # AUTOMATION SETTINGS
    # ========================================================================
    
    # Message sending rate limits
    MESSAGES_PER_HOUR = int(os.getenv('MESSAGES_PER_HOUR', '15'))
    MESSAGES_PER_DAY = int(os.getenv('MESSAGES_PER_DAY', '50'))
    CONNECTION_REQUEST_LIMIT = int(os.getenv('CONNECTION_REQUEST_LIMIT', '10'))
    
    # Follow-up settings
    FOLLOW_UP_DELAY_DAYS = int(os.getenv('FOLLOW_UP_DELAY_DAYS', '3'))
    MAX_FOLLOW_UPS = int(os.getenv('MAX_FOLLOW_UPS', '2'))
    
    # ========================================================================
    # HUBSPOT INTEGRATION (Optional)
    # ========================================================================
    
    HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY', '')
    HUBSPOT_ENABLED = os.getenv('HUBSPOT_ENABLED', 'False').lower() == 'true'
    
    # ========================================================================
    # REDIS/CELERY (Optional - for background tasks)
    # ========================================================================
    
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = LOG_DIR / 'app.log'
    
    # ========================================================================
    # SECURITY
    # ========================================================================
    
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    
    # ========================================================================
    # FILE UPLOAD
    # ========================================================================
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'docx', 'doc', 'txt', 'pdf', 'csv'}
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def get_database_path() -> Path:
        """Get database path"""
        return Config.DATABASE_PATH
    
    @staticmethod
    def ensure_directories():
        """Ensure all required directories exist"""
        directories = [
            Config.DATA_DIR,
            Config.UPLOAD_DIR,
            Config.EXPORT_DIR,
            Config.LOG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def validate_config() -> dict:
        """Validate configuration and return status"""
        status = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required settings
        if not Config.SECRET_KEY or Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            status['warnings'].append('SECRET_KEY is using default value - change in production')
        
        if not Config.OPENAI_API_KEY:
            status['errors'].append('OPENAI_API_KEY is not set')
            status['valid'] = False
        
        if not Config.LINKEDIN_EMAIL or not Config.LINKEDIN_PASSWORD:
            status['warnings'].append('LinkedIn credentials are not configured')
        
        # Check directories
        try:
            Config.ensure_directories()
        except Exception as e:
            status['errors'].append(f'Could not create directories: {str(e)}')
            status['valid'] = False
        
        return status
    
    @staticmethod
    def print_config():
        """Print current configuration (for debugging)"""
        print("\n" + "="*70)
        print("⚙️  CONFIGURATION")
        print("="*70)
        print(f"Environment: {Config.FLASK_ENV}")
        print(f"Debug: {Config.DEBUG}")
        print(f"Database: {Config.DATABASE_PATH}")
        print(f"OpenAI Key: {'Set' if Config.OPENAI_API_KEY else 'Not set'}")
        print(f"LinkedIn Email: {Config.LINKEDIN_EMAIL or 'Not set'}")
        print(f"Sales Navigator: {Config.SALES_NAVIGATOR_ENABLED}")
        print(f"Messages/Hour: {Config.MESSAGES_PER_HOUR}")
        print("="*70 + "\n")


# Initialize directories on import
Config.ensure_directories()


if __name__ == '__main__':
    """Test configuration"""
    print("Testing Configuration...")
    
    Config.print_config()
    
    status = Config.validate_config()
    
    print("\n📋 Validation Results:")
    print(f"Valid: {status['valid']}")
    
    if status['errors']:
        print("\n❌ Errors:")
        for error in status['errors']:
            print(f"  - {error}")
    
    if status['warnings']:
        print("\n⚠️  Warnings:")
        for warning in status['warnings']:
            print(f"  - {warning}")
    
    if status['valid'] and not status['warnings']:
        print("\n✅ Configuration is valid!")