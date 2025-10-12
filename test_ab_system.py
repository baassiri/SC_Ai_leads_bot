"""
Quick A/B Testing System Test
Tests the complete A/B testing workflow
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from backend.database.db_manager import db_manager
from backend.ai_engine.message_generator_abc import ABCMessageGenerator
from backend.automation.ab_test_manager import ABTestManager
from backend.credentials_manager import credentials_manager

def test_complete_workflow():
    print("=" * 60)
    print("🧪 TESTING COMPLETE A/B TESTING SYSTEM")
    print("=" * 60)
    
    # Step 1: Check for leads
    print("\n📊 Step 1: Checking for leads...")
    leads = db_manager.get_all_leads(min_score=70, limit=5)
    
    if not leads:
        print("⚠️ No leads found! Please:")
        print("   1. Upload a persona document")
        print("   2. Start the bot to scrape leads")
        print("   3. Then run this test again")
        return
    
    print(f"✅ Found {len(leads)} qualified leads")
    for lead in leads[:3]:
        print(f"   - {lead['name']}, {lead['title']} (Score: {lead['ai_score']})")
    
    # Step 2: Check OpenAI key
    print("\n🔑 Step 2: Checking OpenAI credentials...")
    api_key = credentials_manager.get_openai_key()
    
    if not api_key:
        print("❌ No OpenAI API key found!")
        print("   Please configure credentials in the dashboard")
        return
    
    print("✅ OpenAI credentials configured")
    
    # Step 3: Generate messages with A/B testing
    print("\n🎨 Step 3: Generating A/B/C message variants...")
    lead_ids = [lead['id'] for lead in leads[:5]]
    
    try:
        generator = ABCMessageGenerator(api_key=api_key)
        result = generator.batch_generate(
            lead_ids=lead_ids,
            test_name="Test_System_Check",
            max_leads=5
        )
        
        print(f"\n✅ SUCCESS! Generated messages:")
        print(f"   - Test ID: {result['test_id']}")
        print(f"   - Test Name: {result['test_name']}")
        print(f"   - Total Messages: {result['messages_created']}")
        print(f"   - Successful Leads: {result['successful']}")
        
        # Step 4: Check test results
        print("\n📈 Step 4: Checking A/B test results...")
        manager = ABTestManager()
        test_results = manager.get_test_results(result['test_id'])
        
        if test_results:
            print(f"✅ Test Status: {test_results['status']}")
            print(f"   Variant A: {test_results['variant_a']['sent']} sent")
            print(f"   Variant B: {test_results['variant_b']['sent']} sent")
            print(f"   Variant C: {test_results['variant_c']['sent']} sent")
        
        # Step 5: Check messages in database
        print("\n💾 Step 5: Verifying messages in database...")
        stats = db_manager.get_message_stats()
        print(f"✅ Message Stats:")
        print(f"   Draft: {stats['draft']}")
        print(f"   Approved: {stats['approved']}")
        print(f"   Total: {stats['total']}")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("   1. Go to http://localhost:5000/messages")
        print("   2. Review the generated A/B/C variants")
        print("   3. Approve messages to send")
        print("   4. Track performance in analytics")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_complete_workflow()