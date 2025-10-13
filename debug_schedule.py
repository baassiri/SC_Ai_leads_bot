import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

print("=== SCHEDULED MESSAGES ===")
cursor.execute("""
    SELECT id, message_id, lead_id, scheduled_time, status
    FROM message_schedule
    ORDER BY scheduled_time
""")

for row in cursor.fetchall():
    print(f"ID: {row[0]}, Msg: {row[1]}, Lead: {row[2]}, Time: {row[3]}, Status: {row[4]}")

print("\n=== PENDING CHECK ===")
now = datetime.now().isoformat()
print(f"Current time: {now}")

cursor.execute("""
    SELECT COUNT(*) 
    FROM message_schedule 
    WHERE status = 'scheduled' 
    AND scheduled_time <= ?
""", (now,))

count = cursor.fetchone()[0]
print(f"Messages ready: {count}")

conn.close()
