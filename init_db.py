"""
Initialize the database with tables
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import Base and DatabaseManager
from backend.database.models import Base
from backend.database.db_manager import DatabaseManager

def init_database():
    """Initialize database with all tables"""
    print("🗄️  Initializing database...")
    
    try:
        # Create database manager instance
        db_manager = DatabaseManager()
        
        # Create all tables using the engine from db_manager
        Base.metadata.create_all(db_manager.engine)
        print("✅ Database tables created successfully!")
        
        # Check if database has any data
        from backend.database.models import User, Persona, Lead, Message, Campaign, ActivityLog
        
        with db_manager.session_scope() as session:
            stats = {
                'users': session.query(User).count(),
                'personas': session.query(Persona).count(),
                'leads': session.query(Lead).count(),
                'messages': session.query(Message).count(),
                'campaigns': session.query(Campaign).count(),
                'activity_logs': session.query(ActivityLog).count()
            }
            
            print("\n📊 Current database status:")
            for table, count in stats.items():
                print(f"   {table}: {count} records")
            
            # Add sample activity log if database is empty
            if stats['activity_logs'] == 0:
                print("\n🔍 Adding sample activity log...")
                db_manager.log_activity(
                    activity_type='database_initialized',
                    description='Database initialized successfully',
                    status='success'
                )
                print("✅ Sample activity log added")
        
        print("\n✨ Database initialization complete!")
        print("\n💡 Next steps:")
        print("   1. Start the Flask app: python backend/app.py")
        print("   2. Go to: http://localhost:5000/leads")
        print("   3. Should show 0 leads!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)