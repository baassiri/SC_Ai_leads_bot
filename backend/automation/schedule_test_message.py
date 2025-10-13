"""
Schedule a test message NOW
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager
from backend.automation.scheduler import MessageScheduler

def main():
    print("="*60)
    print("📅 SCHEDULE TEST MESSAGE")
    print("="*60)
    
    # Get leads
    leads = db_manager.get_all_leads(limit=5)
    
    if not leads:
        print("❌ No leads found!")
        return
    
    print(f"\n✅ Found {len(leads)} leads")
    for i, lead in enumerate(leads, 1):
        print(f"   {i}. {lead['name']} - {lead['title']}")
    
    # Pick first lead
    lead = leads[0]
    print(f"\n✅ Using: {lead['name']}")
    
    # Create message
    message_id = db_manager.create_message(
        lead_id=lead['id'],
        message_type='connection_request',
        content=f"Hi {lead['name'].split()[0]}! I came across your profile and would love to connect.",
        variant='A',
        status='approved'
    )
    print(f"✅ Created message: {message_id}")
    
    # Schedule for NOW
    scheduler = MessageScheduler()
    schedule_id = scheduler.schedule_message(
        message_id=message_id,
        scheduled_time=datetime.now(),  # NOW!
        lead_id=lead['id']
    )
    print(f"✅ Scheduled: {schedule_id}")
    
    print("\n" + "="*60)
    print("✅ READY TO SEND!")
    print("="*60)
    print("\nRun: python backend/automation/queue_processor.py --test")

if __name__ == '__main__':
    main()