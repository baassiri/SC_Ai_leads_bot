"""
Database Migration: Enhanced Persona Fields - FIXED FOR SQLITE
Run this from project root: python backend/database/migration_enhanced_personas_fixed.py
"""

import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.config import Config


def run_migration():
    """Execute migration directly with sqlite3"""
    print("🔄 Running enhanced persona migration (SQLite)...")
    
    # Get database path
    db_path = project_root / 'data' / 'database.db'
    print(f"Database: {db_path}")
    
    if not db_path.exists():
        print("❌ Database file not found!")
        return
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # List of columns to add
    columns = [
        ('job_titles', 'TEXT'),
        ('decision_maker_roles', 'TEXT'),
        ('company_types', 'TEXT'),
        ('solutions', 'TEXT'),
        ('linkedin_keywords', 'TEXT'),
        ('smart_search_query', 'VARCHAR(500)'),
        ('message_hooks', 'TEXT'),
        ('seniority_level', 'VARCHAR(100)'),
        ('industry_focus', 'VARCHAR(200)'),
        ('document_source', 'VARCHAR(255)')
    ]
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(personas)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    print(f"\n📋 Existing columns: {existing_columns}")
    
    # Add each column
    added_count = 0
    for col_name, col_type in columns:
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE personas ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                print(f"  ✅ Added: {col_name} ({col_type})")
                added_count += 1
            except Exception as e:
                print(f"  ❌ Failed to add {col_name}: {str(e)}")
        else:
            print(f"  ⏭️  Skip: {col_name} (already exists)")
    
    # Commit changes
    conn.commit()
    
    # Verify
    cursor.execute("PRAGMA table_info(personas)")
    final_columns = [row[1] for row in cursor.fetchall()]
    
    print(f"\n✅ Migration complete!")
    print(f"Added {added_count} new columns")
    print(f"Total columns: {len(final_columns)}")
    
    # Create index
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_personas_search_query 
            ON personas(smart_search_query)
        """)
        conn.commit()
        print("✅ Created index on smart_search_query")
    except Exception as e:
        print(f"⚠️  Index creation: {str(e)}")
    
    conn.close()
    print("\n🎉 Done! Restart Flask and try uploading again.")


if __name__ == '__main__':
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()