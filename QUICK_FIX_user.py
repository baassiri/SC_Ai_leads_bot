"""
QUICK FIX: Create Default User for Cooldown Manager
Run this ONCE to fix the "User not found" error
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def quick_fix():
    print("=" * 60)
    print("🔧 QUICK FIX: Creating Default User")
    print("=" * 60)
    print()
    
    try:
        from backend.database.db_manager import db_manager
        from backend.database.models import Base, User
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.config import Config
        
        # Create engine and session
        engine = create_engine(Config.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if user exists
        user = session.query(User).filter(User.id == 1).first()
        
        if user:
            print("✅ User already exists!")
            print(f"   User ID: {user.id}")
            print(f"   Email: {user.email}")
        else:
            # Create user
            print("Creating default user...")
            new_user = User(
                id=1,
                email="default@scai.com",
                is_active=True
            )
            session.add(new_user)
            session.commit()
            print("✅ Default user created!")
            print(f"   User ID: {new_user.id}")
            print(f"   Email: {new_user.email}")
        
        session.close()
        
        print()
        print("=" * 60)
        print("✅ FIX APPLIED!")
        print("=" * 60)
        print()
        print("Now test with:")
        print("curl http://localhost:5000/api/scraping/cooldown-status")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    quick_fix()