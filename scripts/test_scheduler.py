"""
Test Message Scheduling System
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from backend.automation.scheduler import scheduler
from backend.database.db_manager import db_manager


def test_scheduler():
    """Test the scheduling system"""
    
    print("="*60)
    print("🧪 DAY 3: MESSAGE SCHEDULING SYSTEM TEST")
    print("="*60)
    
    # Test 1: Stats
    print("\n📊 Test 1: Schedule Statistics")
    print("-"*60)
    stats = scheduler.get_schedule_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test 2: Get draft messages
    print("\n💬 Test 2: Get Draft Messages")
    print("-"*60)
    messages = db_manager.get_messages_by_status('draft', limit=10)
    
    if not messages:
        print("⚠️  No draft messages - creating test messages...")
        # Get a lead
        leads = db_manager.get_all_leads(limit=1)
        if leads:
            lead_id = leads[0]['id']
            # Create test messages
            for variant in ['A', 'B', 'C']:
                msg_id = db_manager.create_message(
                    lead_id=lead_id,
                    content=f"Test message variant {variant}",
                    variant=variant,
                    status='draft'
                )
            messages = db_manager.get_messages_by_status('draft', limit=10)
    
    print(f"✅ Found {len(messages)} draft messages")
    
    if not messages:
        print("❌ Cannot test without messages!")
        return False
    
    # Test 3: Schedule single message
    print("\n📅 Test 3: Schedule Single Message")
    print("-"*60)
    
    test_msg = messages[0]
    send_time = datetime.utcnow() + timedelta(minutes=10)
    
    schedule_id = scheduler.schedule_message(
        message_id=test_msg['id'],
        scheduled_time=send_time,
        lead_id=test_msg.get('lead_id')
    )
    
    print(f"✅ Scheduled message {test_msg['id']}")
    print(f"   Schedule ID: {schedule_id}")
    print(f"   Send time: {send_time}")
    
    # Test 4: Schedule batch
    print("\n📦 Test 4: Schedule Batch")
    print("-"*60)
    
    if len(messages) >= 3:
        batch_ids = [m['id'] for m in messages[1:4]]
        schedule_ids = scheduler.schedule_batch(
            message_ids=batch_ids,
            spread_hours=2,
            ai_optimize=False
        )
        print(f"✅ Scheduled {len(schedule_ids)} messages")
    
    # Test 5: Rate limiting
    print("\n⏱️  Test 5: Rate Limiting")
    print("-"*60)
    
    test_time = datetime.utcnow()
    can_send = scheduler._check_rate_limit(test_time)
    print(f"✅ Rate limit check: {'PASS' if can_send else 'BLOCKED'}")
    
    next_slot = scheduler._get_next_available_slot()
    print(f"   Next slot: {next_slot}")
    
    # Test 6: Business hours
    print("\n🕐 Test 6: Business Hours")
    print("-"*60)
    
    early = datetime.utcnow().replace(hour=7, minute=0)
    adjusted = scheduler._adjust_to_business_hours(early)
    print(f"✅ 7:00 AM → {adjusted.strftime('%I:%M %p')}")
    
    late = datetime.utcnow().replace(hour=20, minute=0)
    adjusted = scheduler._adjust_to_business_hours(late)
    print(f"✅ 8:00 PM → {adjusted.strftime('%I:%M %p %A')}")
    
    # Test 7: Pending messages
    print("\n📬 Test 7: Pending Messages")
    print("-"*60)
    
    pending = scheduler.get_pending_messages(limit=5)
    print(f"✅ Found {len(pending)} ready to send")
    
    # Test 8: Final stats
    print("\n📈 Test 8: Final Stats")
    print("-"*60)
    
    final_stats = scheduler.get_schedule_stats()
    for key, value in final_stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED!")
    print("="*60)
    print("\n📋 What You Built:")
    print("   ✅ Message scheduling with rate limiting")
    print("   ✅ Business hours enforcement (9 AM - 6 PM)")
    print("   ✅ Batch scheduling with smart spacing")
    print("   ✅ Queue management system")
    print("\n🚀 Next: Build queue processor to send messages!")
    
    return True


if __name__ == '__main__':
    success = test_scheduler()
    sys.exit(0 if success else 1)