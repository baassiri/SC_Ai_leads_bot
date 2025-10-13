"""
Debug script to check scheduled message times
"""
import sqlite3
from datetime import datetime

db_path = 'data/database.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("⏰ SCHEDULED MESSAGES TIME CHECK")
print("=" * 60)

# Current time
now = datetime.now()
print(f"\n📅 Current time: {now}")
print(f"   ISO format:   {now.isoformat()}")

# Get scheduled messages
cursor.execute('''
    SELECT 
        ms.id as schedule_id,
        ms.message_id,
        ms.scheduled_time,
        ms.status,
        m.lead_id,
        l.name as lead_name
    FROM message_schedule ms
    JOIN messages m ON ms.message_id = m.id
    LEFT JOIN leads l ON m.lead_id = l.id
    WHERE ms.status = 'scheduled'
    ORDER BY ms.scheduled_time
''')

messages = cursor.fetchall()

print(f"\n📬 Found {len(messages)} scheduled messages:")
print("-" * 60)

for msg in messages:
    scheduled_time = datetime.fromisoformat(msg['scheduled_time'].replace('Z', ''))
    time_diff = (scheduled_time - now).total_seconds()
    
    # Check if ready
    is_ready = scheduled_time <= now
    status_icon = "✅" if is_ready else "⏰"
    
    print(f"\n{status_icon} Schedule ID: {msg['schedule_id']}")
    print(f"   Message ID: {msg['message_id']}")
    print(f"   Lead: {msg['lead_name']} (ID: {msg['lead_id']})")
    print(f"   Scheduled: {msg['scheduled_time']}")
    print(f"   Status: {msg['status']}")
    
    if is_ready:
        print(f"   🟢 READY TO SEND (was {abs(time_diff)/60:.1f} mins ago)")
    else:
        print(f"   🔴 NOT READY (in {time_diff/60:.1f} mins)")

# Check with the same query the processor uses
print("\n" + "=" * 60)
print("🔍 TESTING PROCESSOR QUERY")
print("=" * 60)

cursor.execute('''
    SELECT 
        ms.id as schedule_id,
        ms.message_id,
        ms.scheduled_time,
        m.content,
        m.variant,
        m.lead_id,
        l.name as lead_name,
        l.profile_url
    FROM message_schedule ms
    JOIN messages m ON ms.message_id = m.id
    LEFT JOIN leads l ON m.lead_id = l.id
    WHERE ms.status = 'scheduled'
    AND ms.scheduled_time <= ?
    AND m.lead_id IS NOT NULL
    AND l.id IS NOT NULL
    ORDER BY ms.scheduled_time
    LIMIT 10
''', (now.isoformat(),))

ready_messages = cursor.fetchall()

print(f"\n📊 Messages ready to send: {len(ready_messages)}")

if ready_messages:
    for msg in ready_messages:
        print(f"\n✅ Ready: {msg['lead_name']}")
        print(f"   Scheduled: {msg['scheduled_time']}")
        print(f"   Message: {msg['content'][:50]}...")
else:
    print("\n❌ No messages meet the criteria:")
    print("   - status = 'scheduled'")
    print("   - scheduled_time <= current time")
    print("   - lead_id IS NOT NULL")
    print("   - lead exists in database")

conn.close()

print("\n" + "=" * 60)
print("💡 TIP: To reschedule a message to NOW:")
print("   UPDATE message_schedule")
print("   SET scheduled_time = datetime('now')")
print("   WHERE id = X;")
print("=" * 60)