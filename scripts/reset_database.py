# scripts/reset_database.py
"""Reset database to zero"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.db_manager import DatabaseManager

def reset_database():
    print("⚠️  WARNING: This will DELETE ALL DATA!")
    confirm = input("Type 'YES' to confirm: ")
    
    if confirm == 'YES':
        db = DatabaseManager()
        
        # Drop all tables
        print("\n🗑️  Dropping all tables...")
        db.drop_tables()
        
        # Recreate tables
        print("🔨 Creating fresh tables...")
        db.create_tables()
        
        print("\n✅ Database reset complete! All data cleared.")
        print("💡 UI will now show zeros for all metrics.")
    else:
        print("❌ Reset cancelled")

if __name__ == "__main__":
    reset_database()