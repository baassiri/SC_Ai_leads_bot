"""
Test End-to-End Message Sending
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager
from backend.automation.scheduler import MessageScheduler


def test_end_to_end():
    print("="*60)
    print("🧪 END-TO-END MESSAGE SENDING TEST")
    print("="*60)
    
    # Step 1: Get or create test lead
    print("\n1️⃣ Finding test lead...")
    leads = db_manager.get_all_leads(limit=1)
    
    if not leads:
        print("❌ No leads found! Run bot first to generate leads.")
        return False
    
    lead = leads[0]
    print(f"✅ Found lead: {lead['name']}")
    
    # Step 2: Create test message
    print("\n2️⃣ Creating test message...")
    message_id = db_manager.create_message(
        lead_id=lead['id'],
        message_type='connection_request',
        content='Hi! I came across your profile and would love to connect.',
        variant='A',
        status='approved'
    )
    print(f"✅ Created message ID: {message_id}")
    
    # Step 3: Schedule message for NOW
    print("\n3️⃣ Scheduling message for immediate send...")
    scheduler = MessageScheduler()
    
    schedule_id = scheduler.schedule_message(
        message_id=message_id,
        scheduled_time=datetime.utcnow(),  # Now!
        lead_id=lead['id']
    )
    print(f"✅ Scheduled ID: {schedule_id}")
    
    # Step 4: Check if message is pending
    print("\n4️⃣ Checking pending messages...")
    pending = scheduler.get_pending_messages(limit=1)
    
    if pending:
        print(f"✅ Found {len(pending)} pending message(s)")
        print(f"   Lead: {pending[0]['lead_name']}")
        print(f"   Message: {pending[0]['content'][:50]}...")
    else:
        print("❌ No pending messages!")
        return False
    
    # Step 5: Instructions
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Make sure LinkedIn message sender is working")
    print("2. Run queue processor:")
    print("   python backend/automation/queue_processor.py --test")
    print("\n⚠️  This will attempt to send a REAL LinkedIn message!")
    print("   Make sure you're using a test account.")
    
    return True


if __name__ == '__main__':
    success = test_end_to_end()
    sys.exit(0 if success else 1)