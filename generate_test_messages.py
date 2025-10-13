"""
Generate A/B/C Message Variants for Test Leads
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_manager import db_manager
from backend.credentials_manager import credentials_manager
from backend.ai_engine.message_generator_abc import ABCMessageGenerator

def generate_messages():
    print("="*60)
    print("Generate A/B/C Message Variants")
    print("="*60)
    
    # Check for OpenAI key
    api_key = credentials_manager.get_openai_key()
    if not api_key:
        print("\n❌ No OpenAI API key found!")
        print("Please add your OpenAI API key in the Settings page")
        return
    
    print(f"✅ OpenAI API key found: {api_key[:20]}...")
    
    # Get test leads
    leads = db_manager.get_all_leads(min_score=70)
    
    if not leads:
        print("\n❌ No leads found!")
        print("Please run quick_manual_lead_entry.py first")
        return
    
    print(f"\n✅ Found {len(leads)} qualified leads")
    for lead in leads:
        print(f"   - {lead['name']}, {lead['title']} at {lead['company']}")
    
    input("\nPress Enter to generate A/B/C messages for all leads...")
    
    # Initialize generator
    generator = ABCMessageGenerator(api_key=api_key)
    
    # Generate for each lead
    total_generated = 0
    for lead in leads:
        print(f"\n📝 Generating messages for {lead['name']}...")
        
        try:
            result = generator.generate_for_lead(
                lead_id=lead['id'],
                save_to_db=True
            )
            
            print(f"   ✅ Variant A: {result['variant_a'][:60]}...")
            print(f"   ✅ Variant B: {result['variant_b'][:60]}...")
            print(f"   ✅ Variant C: {result['variant_c'][:60]}...")
            total_generated += 3
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n✅ Generated {total_generated} message variants!")
    print("\nNext steps:")
    print("1. Go to http://localhost:5000/messages")
    print("2. Review all variants (A, B, C)")
    print("3. Approve the ones you like")
    print("4. Manually send to test LinkedIn profiles")

if __name__ == '__main__':
    generate_messages()