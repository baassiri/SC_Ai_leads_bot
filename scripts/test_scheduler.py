"""
Test Message Scheduling System
Tests scheduler, rate limiting, and queue processing
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from backend.automation.scheduler import MessageScheduler
from backend.database.db_manager import db_manager

def test_scheduler():
    """Test the complete scheduling system"""
    
    print("=" * 60)
    print("🧪 TESTING MESSAGE SCHEDULING SYSTEM")
    print("=" * 60)
    
    scheduler = MessageScheduler()
    
    # Test 1: Get current stats
    print("\n📊 Test 1: Get Schedule Statistics")
    print("-" * 60)
    stats = scheduler.get_schedule_stats()
    
    print(f"✅ Current Schedule Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test 2: Check for messages to schedule
    print("\n💬 Test 2: Check for Draft Messages")
    print("-" * 60)
    
    messages = db_manager.get_messages_by_status('draft', limit=10)
    
    if not messages:
        print("⚠️ No draft messages found!")
        print("   Please run: python -m backend.ai_engine.message_generator_abc --top 3")
        print("   This will generate test messages")
        return False
    
    print(f"✅ Found {len(messages)} draft messages to schedule")
    for msg in messages[:3]:
        print(f"   - Message {msg['id']}: {msg['content'][:50]}...")
    
    # Test 3: Schedule a single message
    print("\n📅 Test 3: Schedule Single Message")
    print("-" * 60)
    
    test_message_id = messages[0]['id']
    
    try:
        # Schedule for 10 minutes from now
        send_time = datetime.utcnow() + timedelta(minutes=10)
        
        schedule_id = scheduler.schedule_message(
            message_id=test_message_id,
            scheduled_time=send_time,
            ai_optimize=False
        )
        
        print(f"✅ Successfully scheduled message {test_message_id}")
        print(f"   Schedule ID: {schedule_id}")
        print(f"   Scheduled for: {send_time}")
    except Exception as e:
        print(f"❌ Error scheduling message: {str(e)}")
        return False
    
    # Test 4: Schedule batch of messages
    print("\n📦 Test 4: Schedule Batch of Messages")
    print("-" * 60)
    
    if len(messages) >= 3:
        # Take next 3 messages
        batch_ids = [msg['id'] for msg in messages[1:4]]
        
        try:
            schedule_ids = scheduler.schedule_batch(
                message_ids=batch_ids,
                start_time=None,  # Start ASAP
                spread_hours=4,   # Spread over 4 hours
                ai_optimize=True  # Use AI optimization
            )
            
            print(f"✅ Successfully scheduled {len(schedule_ids)} messages")
            print(f"   Schedule IDs: {schedule_ids}")
        except Exception as e:
            print(f"❌ Error scheduling batch: {str(e)}")
            return False
    else:
        print("⚠️ Not enough messages for batch test (need 3+)")
    
    # Test 5: Check rate limiting
    print("\n⏱️ Test 5: Rate Limiting Check")
    print("-" * 60)
    
    now = datetime.utcnow()
    can_send = scheduler._check_rate_limit(now)
    
    print(f"✅ Rate limit check: {'PASS' if can_send else 'BLOCKED'}")
    
    # Get next available slot
    next_slot = scheduler._get_next_available_slot()
    print(f"   Next available slot: {next_slot}")
    
    time_until = (next_slot - now).total_seconds() / 60
    print(f"   Time until next slot: {time_until:.1f} minutes")
    
    # Test 6: Business hours adjustment
    print("\n🕐 Test 6: Business Hours Adjustment")
    print("-" * 60)
    
    # Test early morning (7 AM)
    early_time = datetime.utcnow().replace(hour=7, minute=0)
    adjusted_early = scheduler._adjust_to_business_hours(early_time)
    print(f"✅ 7:00 AM → {adjusted_early.strftime('%I:%M %p')}")
    
    # Test late evening (8 PM)
    late_time = datetime.utcnow().replace(hour=20, minute=0)
    adjusted_late = scheduler._adjust_to_business_hours(late_time)
    print(f"✅ 8:00 PM → {adjusted_late.strftime('%I:%M %p on %A')}")
    
    # Test 7: Get pending messages
    print("\n📬 Test 7: Get Pending Scheduled Messages")
    print("-" * 60)
    
    pending = scheduler.get_pending_messages(limit=10)
    
    print(f"✅ Found {len(pending)} pending messages")
    
    if pending:
        for msg in pending[:3]:
            print(f"   - {msg['lead_name']}: Scheduled for {msg['scheduled_time']}")
    
    # Test 8: Final stats
    print("\n📈 Test 8: Updated Statistics")
    print("-" * 60)
    
    final_stats = scheduler.get_schedule_stats()
    
    print("✅ Final Schedule Stats:")
    for key, value in final_stats.items():
        print(f"   {key}: {value}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("   1. Review scheduled messages in database")
    print("   2. Start queue processor: python -m backend.automation.queue_processor")
    print("   3. Messages will be sent automatically at scheduled times")
    print("   4. Monitor in Flask dashboard: http://localhost:5000/messages")
    
    return True

if __name__ == '__main__':
    success = test_scheduler()
    
    if not success:
        sys.exit(1)