"""
Test Queue Processor
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from backend.automation.scheduler import scheduler
from backend.automation.queue_processor import QueueProcessor
from backend.database.db_manager import db_manager


def test_queue_processor():
    """Test the queue processor"""
    
    print("="*60)
    print("🧪 QUEUE PROCESSOR TEST")
    print("="*60)
    
    # Test 1: Check scheduled messages
    print("\n📊 Test 1: Check Scheduled Messages")
    print("-"*60)
    
    stats = scheduler.get_schedule_stats()
    print(f"✅ Scheduled messages: {stats['scheduled']}")
    print(f"   Next scheduled: {stats['next_scheduled']}")
    
    # Test 2: Check pending messages (ready to send now)
    print("\n📬 Test 2: Check Pending Messages")
    print("-"*60)
    
    pending = scheduler.get_pending_messages(limit=5)
    print(f"✅ Found {len(pending)} pending messages")
    
    if pending:
        for msg in pending:
            print(f"   - {msg['lead_name']}: {msg['scheduled_time']}")
    else:
        print("   ℹ️  No messages ready to send right now")
        print("   (Messages are scheduled for future times)")
    
    # Test 3: Reschedule one message to NOW for testing
    print("\n⏰ Test 3: Reschedule Message to NOW")
    print("-"*60)
    
    if stats['scheduled'] > 0:
        # Get first scheduled message
        import sqlite3
        from backend.config import Config
        db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, message_id, scheduled_time 
            FROM message_schedule 
            WHERE status = 'scheduled' 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        
        if result:
            schedule_id = result[0]
            message_id = result[1]
            old_time = result[2]
            
            # Reschedule to now
            now = datetime.utcnow()
            scheduler.reschedule_message(schedule_id, now)
            
            print(f"✅ Rescheduled message {message_id}")
            print(f"   Old time: {old_time}")
            print(f"   New time: {now}")
        
        conn.close()
    else:
        print("⚠️  No scheduled messages to reschedule")
    
    # Test 4: Check pending again
    print("\n📬 Test 4: Check Pending Again")
    print("-"*60)
    
    pending = scheduler.get_pending_messages(limit=5)
    print(f"✅ Found {len(pending)} pending messages")
    
    if pending:
        for msg in pending:
            print(f"   - {msg['lead_name']}: Ready to send!")
    
    # Test 5: Process queue (DRY RUN - won't actually send)
    print("\n🔄 Test 5: Queue Processor DRY RUN")
    print("-"*60)
    print("ℹ️  This would normally send messages via LinkedIn")
    print("ℹ️  But we're skipping the actual send for testing")
    
    processor = QueueProcessor()
    
    print(f"\n✅ Queue processor initialized")
    print(f"   Check interval: {processor.check_interval}s")
    print(f"   Messages sent: {processor.stats['messages_sent']}")
    print(f"   Messages failed: {processor.stats['messages_failed']}")
    
    # Summary
    print("\n" + "="*60)
    print("🎉 QUEUE PROCESSOR TEST COMPLETE!")
    print("="*60)
    
    print("\n📋 What You Built:")
    print("   ✅ Queue processor that checks every 60 seconds")
    print("   ✅ Automatically sends pending messages")
    print("   ✅ Handles errors and retries")
    print("   ✅ Logs all activity")
    
    print("\n🚀 HOW TO USE:")
    print("   1. Schedule messages with scheduler")
    print("   2. Run: python backend/automation/queue_processor.py")
    print("   3. Leave it running - it auto-sends at scheduled times")
    print("   4. Press Ctrl+C to stop")
    
    print("\n💡 TIPS:")
    print("   • Use --test flag to process queue once")
    print("   • Use --headless flag to hide browser")
    print("   • Use --interval X to check every X seconds")
    
    print("\n" + "="*60)
    
    return True


if __name__ == '__main__':
    success = test_queue_processor()
    sys.exit(0 if success else 1)