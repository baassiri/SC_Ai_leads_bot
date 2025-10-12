"""
Batch Message Generator - Generate messages for all high-scoring leads
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.ai_engine.message_generator import MessageGenerator
from backend.database.db_manager import db_manager
import time

print("\n" + "="*60)
print("📝 BATCH MESSAGE GENERATION")
print("="*60)

# Configuration
MIN_SCORE = 70  # Only generate for leads with score >= 70
MAX_LEADS = 10  # Limit how many to generate (to save API costs)

# Get high-scoring leads
print(f"\n📊 Fetching leads with score >= {MIN_SCORE}...")
leads = db_manager.get_all_leads(min_score=MIN_SCORE, limit=MAX_LEADS)

if not leads:
    print(f"❌ No leads found with score >= {MIN_SCORE}")
    sys.exit(1)

print(f"✅ Found {len(leads)} leads to process")

# Initialize message generator
generator = MessageGenerator()

# Track results
success_count = 0
error_count = 0

# Generate messages for each lead
for i, lead in enumerate(leads, 1):
    print(f"\n[{i}/{len(leads)}] Processing: {lead['name']}")
    print(f"            Company: {lead['company']}")
    print(f"            Score: {lead['ai_score']}/100")
    
    try:
        # Generate connection request messages
        messages = generator.generate_connection_request(
            lead_name=lead['name'],
            lead_title=lead['title'],
            lead_company=lead['company'],
            persona_name=lead.get('persona_name', 'Business Professional')
        )
        
        # Show preview of generated messages
        print(f"\n    ✅ Generated 3 variants:")
        print(f"       A: {messages['variant_a'][:60]}...")
        print(f"       B: {messages['variant_b'][:60]}...")
        print(f"       C: {messages['variant_c'][:60]}...")
        
        success_count += 1
        
        # Rate limiting - wait 2 seconds between API calls
        if i < len(leads):  # Don't wait after the last one
            print(f"    ⏳ Waiting 2 seconds before next generation...")
            time.sleep(2)
        
    except Exception as e:
        print(f"    ❌ Error: {str(e)}")
        error_count += 1

# Summary
print("\n" + "="*60)
print("📊 GENERATION COMPLETE")
print("="*60)
print(f"✅ Successful: {success_count}")
print(f"❌ Errors: {error_count}")
print(f"💰 Estimated cost: ${success_count * 0.015:.3f} (at ~$0.015 per generation)")
print("\n💡 Next step: Review the messages and approve for sending")