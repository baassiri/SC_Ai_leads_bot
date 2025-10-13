import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

now = datetime.now()
print(f'Current time: {now}')
print('\nScheduled messages:')

cursor.execute('''
    SELECT ms.id, ms.scheduled_time, ms.status, m.lead_id, l.name
    FROM message_schedule ms
    JOIN messages m ON ms.message_id = m.id
    LEFT JOIN leads l ON m.lead_id = l.id
    WHERE ms.status = 'scheduled'
    ORDER BY ms.scheduled_time
''')

for row in cursor.fetchall():
    sched_time = datetime.fromisoformat(row[1].replace('Z', ''))
    diff = (sched_time - now).total_seconds() / 60
    ready = 'READY' if sched_time <= now else f'in {diff:.1f} mins'
    print(f'  ID:{row[0]} Lead:{row[4]} Time:{row[1]} [{ready}]')

conn.close()
