import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

# Create a test lead
cursor.execute('''
    INSERT INTO leads (name, title, company, profile_url, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
''', ('John Doe', 'CEO', 'Test Corp', 'https://linkedin.com/in/test', 'active', datetime.now().isoformat()))

lead_id = cursor.lastrowid
print(f'✅ Created test lead ID: {lead_id}')

# Create a test message
cursor.execute('''
    INSERT INTO messages (lead_id, message_type, content, variant, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
''', (lead_id, 'connection_request', 'Hi John! Would love to connect.', 'A', 'approved', datetime.now().isoformat()))

message_id = cursor.lastrowid
print(f'✅ Created test message ID: {message_id}')

# Schedule it for NOW
cursor.execute('''
    INSERT INTO message_schedule (message_id, scheduled_time, status, created_at)
    VALUES (?, ?, ?, ?)
''', (message_id, datetime.now().isoformat(), 'scheduled', datetime.now().isoformat()))

schedule_id = cursor.lastrowid
print(f'✅ Scheduled message ID: {schedule_id}')

conn.commit()
conn.close()

print('\n🚀 Ready to test! Run: python backend/automation/queue_processor.py --test')
