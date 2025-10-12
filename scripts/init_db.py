"""
Initialize the database with tables and sample data
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import after path is set
from backend.database.models import Base, engine
from backend.database.db_manager import db_manager

def init_database():
    """Initialize database with all tables"""
    print("🗄️  Initializing database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully!")
        
        # Check if database has any data
        stats = {
            'users': db_manager.session.query(db_manager.models.User).count(),
            'personas': db_manager.session.query(db_manager.models.Persona).count(),
            'leads': db_manager.session.query(db_manager.models.Lead).count(),
            'messages': db_manager.session.query(db_manager.models.Message).count(),
            'campaigns': db_manager.session.query(db_manager.models.Campaign).count(),
            'activity_logs': db_manager.session.query(db_manager.models.ActivityLog).count()
        }
        
        print("\n📊 Current database status:")
        for table, count in stats.items():
            print(f"   {table}: {count} records")
        
        # Add sample activity log if database is empty
        if stats['activity_logs'] == 0:
            print("\n📝 Adding sample activity log...")
            db_manager.log_activity(
                activity_type='database_initialized',
                description='Database initialized successfully',
                status='success'
            )
            print("✅ Sample activity log added")
        
        print("\n✨ Database initialization complete!")
        print("\n💡 Next steps:")
        print("   1. Start the Flask app: python backend/app.py")
        print("   2. Upload a persona document")
        print("   3. Start the bot to scrape leads")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    init_database()