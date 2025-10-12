"""
Test script for message generation
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)  # Change working directory

# Now import
from backend.ai_engine.message_generator import generate_connection_message
from backend.database.db_manager import db_manager

print(f"✅ Imports successful from: {project_root}")

print("\n" + "=" * 60)
print("🧪 MESSAGE GENERATION TEST")
print("=" * 60)

# Get a high-scoring lead
print("\n📊 Fetching high-scoring leads from database...")
leads = db_manager.get_all_leads(min_score=70, limit=3)

if not leads:
    print("⚠️  No high-scoring leads found. Trying any lead...")
    leads = db_manager.get_all_leads(limit=3)

if not leads:
    print("❌ No leads found in database!")
    print("\n💡 Next steps:")
    print("   1. Run the scraper first: python backend/app.py")
    print("   2. Click 'Start Bot' in the web interface")
    print("   3. Wait for leads to be scraped and scored")
    sys.exit(1)

# Test with first lead
lead = leads[0]

print(f"\n✅ Found {len(leads)} leads. Testing with:")
print(f"   Name: {lead['name']}")
print(f"   Title: {lead['title']}")
print(f"   Company: {lead['company']}")
print(f"   AI Score: {lead['ai_score']}/100")

# Generate message
print("\n🎨 Generating connection request messages (calling GPT-4)...\n")

try:
    messages = generate_connection_message(
        lead_name=lead['name'],
        lead_title=lead['title'],
        lead_company=lead['company'],
        persona_name=lead.get('persona_name', 'Business Professional')
    )
    
    print("=" * 60)
    print("✅ GENERATED MESSAGES")
    print("=" * 60)
    
    for variant_key, message in messages.items():
        print(f"\n{variant_key.upper().replace('_', ' ')}:")
        print(f"─" * 60)
        print(message)
        print(f"\n📏 Length: {len(message)} characters")
        
        if len(message) > 300:
            print("⚠️  WARNING: Exceeds LinkedIn's 300 character limit!")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)
    
    print("\n💡 Next steps:")
    print("   1. Review the messages above")
    print("   2. Test with more leads: modify script to loop through all leads")
    print("   3. Build the UI to display these in the web interface")
    print("   4. Add approval workflow before sending")
    
except Exception as e:
    print(f"\n❌ Error generating messages: {str(e)}")
    print("\n🔍 Troubleshooting:")
    print("   1. Check your OPENAI_API_KEY in .env file")
    print("   2. Verify you have GPT-4 API access")
    print("   3. Check your OpenAI API quota")
    import traceback
    print(f"\n📋 Full error:\n{traceback.format_exc()}")