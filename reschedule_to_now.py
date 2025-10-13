"""
Reschedule a message to NOW for testing
"""
import sqlite3
from datetime import datetime

db_path = 'data/database.db'

print("=" * 60)
print("⏰ RESCHEDULE MESSAGE TO NOW")
print("=" * 60)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get scheduled messages with valid leads
cursor.execute('''
    SELECT 
        ms.id as schedule_id,
        ms.message_id,
        ms.scheduled_time,
        m.lead_id,
        l.name as lead_name
    FROM message_schedule ms
    JOIN messages m ON ms.message_id = m.id
    LEFT JOIN leads l ON m.lead_id = l.id
    WHERE ms.status = 'scheduled'
    AND m.lead_id IS NOT NULL
    AND l.id IS NOT NULL
    ORDER BY ms.scheduled_time
''')

messages = cursor.fetchall()

if not messages:
    print("\n❌ No scheduled messages with valid leads found!")
    conn.close()
    exit(1)

print(f"\n📋 Found {len(messages)} message(s) with valid leads:")
print("-" * 60)

for i, msg in enumerate(messages, 1):
    print(f"{i}. Schedule ID: {msg[0]}, Lead: {msg[4]}, Time: {msg[2]}")

# Pick the first one
schedule_id = messages[0][0]
old_time = messages[0][2]
lead_name = messages[0][4]

# Update to NOW
now = datetime.now()
cursor.execute('''
    UPDATE message_schedule
    SET scheduled_time = ?, updated_at = ?
    WHERE id = ?
''', (now.isoformat(), now.isoformat(), schedule_id))

conn.commit()

print(f"\n✅ Rescheduled message for {lead_name}:")
print(f"   Schedule ID: {schedule_id}")
print(f"   Old time: {old_time}")
print(f"   New time: {now.isoformat()}")
print(f"   Status: READY TO SEND NOW!")

conn.close()

print("\n" + "=" * 60)
print("🚀 Now run: python backend/automation/queue_processor.py --test")
print("=" * 60)