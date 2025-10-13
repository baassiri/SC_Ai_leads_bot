"""
Quick script to check your current leads
"""

from backend.database.db_manager import db_manager

print("="*60)
print("Current Leads in Database")
print("="*60)

leads = db_manager.get_all_leads()

if not leads:
    print("\n❌ No leads found in database")
else:
    print(f"\n✅ Found {len(leads)} leads:\n")
    
    for i, lead in enumerate(leads, 1):
        print(f"{i}. {lead.get('name', 'Unknown')}")
        print(f"   Title: {lead.get('title', 'N/A')}")
        print(f"   Company: {lead.get('company', 'N/A')}")
        print(f"   Location: {lead.get('location', 'N/A')}")
        print(f"   Profile: {lead.get('profile_url', 'N/A')}")
        print(f"   AI Score: {lead.get('ai_score', 0)}/100")
        print()

print("="*60)
print("Are these REAL LinkedIn profiles or fake test data?")
print("="*60)