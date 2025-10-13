import sqlite3

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, profile_url FROM leads WHERE id = 26')
row = cursor.fetchone()

if row:
    print(f'✅ Lead 26 EXISTS: {row[1]}')
    print(f'   Profile: {row[2]}')
else:
    print('❌ Lead 26 does NOT exist in database!')

cursor.execute('SELECT COUNT(*) FROM leads')
count = cursor.fetchone()[0]
print(f'\nTotal leads in database: {count}')

conn.close()
