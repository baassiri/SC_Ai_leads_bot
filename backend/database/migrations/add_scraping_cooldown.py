"""
Add Scraping Cooldown Tracking to Users Table
Prevents LinkedIn detection by limiting scraping frequency
"""

import sqlite3
from datetime import datetime
from pathlib import Path

def upgrade(db_path='data/database.db'):
    """Add scraping cooldown columns to users table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add columns for scraping tracking
    columns_to_add = [
        ('last_scrape_date', 'TIMESTAMP'),
        ('scrapes_this_week', 'INTEGER DEFAULT 0'),
        ('scrapes_this_month', 'INTEGER DEFAULT 0'),
        ('weekly_scrape_limit', 'INTEGER DEFAULT 1'),
        ('total_scrapes_alltime', 'INTEGER DEFAULT 0'),
        ('last_week_reset', 'TIMESTAMP'),
        ('last_month_reset', 'TIMESTAMP')
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f'''
                ALTER TABLE users ADD COLUMN {column_name} {column_type}
            ''')
            print(f"✅ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print(f"⚠️  Column {column_name} already exists, skipping")
            else:
                raise
    
    conn.commit()
    conn.close()
    print("✅ Scraping cooldown tracking enabled!")


def downgrade(db_path='data/database.db'):
    """Remove scraping cooldown columns"""
    print("⚠️  Downgrade not implemented (SQLite doesn't support DROP COLUMN)")
    print("   To remove columns, you'd need to recreate the table")


if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    # Get database path
    project_root = Path(__file__).parent.parent.parent.parent
    db_path = project_root / 'data' / 'database.db'
    
    print("\n" + "="*60)
    print("🚀 SCRAPING COOLDOWN MIGRATION")
    print("="*60)
    print(f"\nDatabase: {db_path}")
    
    if '--down' in sys.argv:
        downgrade(str(db_path))
    else:
        upgrade(str(db_path))
    
    print("\n" + "="*60)
    print("✅ Migration complete!")
    print("="*60)