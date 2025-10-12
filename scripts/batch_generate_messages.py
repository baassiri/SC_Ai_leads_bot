"""
Batch Message Generator - Generate messages for all high-scoring leads
UPDATED: Now saves messages to database
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
total_messages_saved = 0

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
        
        # Save each variant to database
        for variant_key, content in messages.items():
            variant_letter = variant_key.split('_')[-1].upper()  # Extract 'A', 'B', or 'C'
            
            message_id = db_manager.create_message(
                lead_id=lead['id'],
                message_type='connection_request',
                content=content,
                variant=variant_letter,
                generated_by='gpt-4',
                prompt_used=f"Generated via batch script for {lead['name']}"
            )
            total_messages_saved += 1
        
        # Show preview of generated messages
        print(f"\n    ✅ Generated & saved 3 variants:")
        print(f"       A ({len(messages['variant_a'])} chars): {messages['variant_a'][:60]}...")
        print(f"       B ({len(messages['variant_b'])} chars): {messages['variant_b'][:60]}...")
        print(f"       C ({len(messages['variant_c'])} chars): {messages['variant_c'][:60]}...")
        
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
print(f"✅ Successful leads: {success_count}")
print(f"❌ Errors: {error_count}")
print(f"💾 Messages saved to database: {total_messages_saved}")
print(f"💰 Estimated cost: ${success_count * 0.015:.3f} (at ~$0.015 per generation)")
print("\n" + "="*60)
print("💡 NEXT STEPS:")
print("="*60)
print("1. View messages: python -m scripts.view_messages")
print("2. Approve messages in the web UI (coming next)")
print("3. Send approved messages to LinkedIn")