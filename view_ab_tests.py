import sqlite3

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

print("=" * 80)
print("A/B TESTS DATABASE")
print("=" * 80)

cursor.execute("SELECT * FROM ab_tests")
tests = cursor.fetchall()

if tests:
    for test in tests:
        print(f"\nTest ID: {test[0]}")
        print(f"Name: {test[1]}")
        print(f"Status: {test[7]}")
        print(f"Variant A: {test[3]} sent, {test[4]} replies ({test[6]:.1f}% rate)")
        print(f"Variant B: {test[10]} sent, {test[11]} replies ({test[13]:.1f}% rate)")
        print(f"Variant C: {test[17]} sent, {test[18]} replies ({test[20]:.1f}% rate)")
        if test[21]:
            print(f"🏆 Winner: Variant {test[21]}")
        print("-" * 80)
else:
    print("No tests found")

conn.close()