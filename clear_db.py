"""
Database Cleanup Script
Clears all data from the database for fresh testing
"""

import os
import sys
from pathlib import Path

def clear_database():
    """Clear all data from database"""
    print("\n" + "="*70)
    print("🗑️  DATABASE CLEANUP SCRIPT")
    print("="*70)
    
    print("\n⚠️  WARNING: This will delete ALL data!")
    print("   - All leads")
    print("   - All messages")
    print("   - All campaigns")
    print("   - All personas")
    print("   - All activity logs")
    
    confirm = input("\n❓ Are you sure? Type 'YES' to confirm: ")
    
    if confirm != "YES":
        print("\n❌ Cleanup cancelled.")
        return
    
    print("\n🔄 Clearing database...")
    
    # CORRECT database file name: database.db (not leads.db)
    try:
        db_file = Path(__file__).parent / 'data' / 'database.db'
        
        if db_file.exists():
            db_file.unlink()
            print("  ✅ Deleted database.db")
        else:
            print("  ⚠️  Database file not found (already clean)")
        
    except PermissionError:
        print("\n❌ ERROR: Database is locked!")
        print("   Please STOP Flask first (CTRL+C), then run this script again.")
        return
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return
    
    # Clear exports
    try:
        exports_dir = Path(__file__).parent / 'data' / 'exports'
        if exports_dir.exists():
            csv_count = 0
            for file in exports_dir.glob('*.csv'):
                try:
                    file.unlink()
                    csv_count += 1
                except:
                    pass
            if csv_count > 0:
                print(f"  ✅ Cleared {csv_count} CSV export(s)")
    except Exception as e:
        print(f"  ⚠️  Could not clear exports: {str(e)}")
    
    # Clear cookies
    try:
        cookies_dir = Path(__file__).parent / 'backend' / 'scrapers' / 'data' / 'cookies'
        if cookies_dir.exists():
            cookie_count = 0
            for file in cookies_dir.glob('*.pkl'):
                try:
                    file.unlink()
                    cookie_count += 1
                except:
                    pass
            if cookie_count > 0:
                print(f"  ✅ Cleared {cookie_count} LinkedIn cookie(s)")
    except Exception as e:
        print(f"  ⚠️  Could not clear cookies: {str(e)}")
    
    # Clear uploaded personas
    try:
        persona_dir = Path(__file__).parent / 'data' / 'personas'
        if persona_dir.exists():
            persona_count = 0
            for file in persona_dir.glob('*'):
                if file.is_file():
                    try:
                        file.unlink()
                        persona_count += 1
                    except:
                        pass
            if persona_count > 0:
                print(f"  ✅ Cleared {persona_count} persona file(s)")
    except Exception as e:
        print(f"  ⚠️  Could not clear personas: {str(e)}")
    
    print("\n" + "="*70)
    print("✅ CLEANUP COMPLETE!")
    print("="*70)
    print("\n📋 Next steps:")
    print("   1. Start Flask: python backend/app.py")
    print("      (Database will be recreated automatically)")
    print("   2. Go to Settings and enter credentials")
    print("   3. Upload target document")
    print("   4. Start scraping!")
    print("\n")

if __name__ == '__main__':
    clear_database()