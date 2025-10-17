"""Find and delete the database"""
import os
from pathlib import Path

print("🔍 Searching for leads.db...")

# Search from project root
project_root = Path(__file__).parent

found_dbs = list(project_root.rglob("leads.db"))

if not found_dbs:
    print("❌ No leads.db found!")
else:
    print(f"\n✅ Found {len(found_dbs)} database file(s):")
    for db in found_dbs:
        print(f"   📁 {db}")
    
    confirm = input("\n❓ Delete ALL of these? Type 'YES': ")
    
    if confirm == "YES":
        for db in found_dbs:
            try:
                db.unlink()
                print(f"   ✅ Deleted: {db}")
            except Exception as e:
                print(f"   ❌ Error deleting {db}: {e}")
        
        # Also clear exports and cookies
        for pattern in ["**/*.csv", "**/cookies/*.pkl"]:
            for file in project_root.glob(pattern):
                try:
                    file.unlink()
                except:
                    pass
        
        print("\n✅ Database cleared!")
    else:
        print("❌ Cancelled")