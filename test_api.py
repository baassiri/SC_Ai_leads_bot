import requests

BASE = "http://localhost:5000"

print("Testing API Endpoints...\n")

tests = [
    ("GET", "/", "Settings Page"),
    ("GET", "/dashboard", "Dashboard"),
    ("GET", "/leads", "Leads Page"),
    ("GET", "/messages", "Messages Page"),
    ("GET", "/analytics", "Analytics"),
    ("GET", "/api/stats/overview", "Stats API"),
    ("GET", "/api/bot/status", "Bot Status"),
    ("GET", "/api/leads", "Leads API"),
    ("GET", "/api/messages", "Messages API"),
]

passed = 0
failed = 0

for method, endpoint, name in tests:
    try:
        r = requests.get(f"{BASE}{endpoint}", timeout=5)
        if r.status_code == 200:
            print(f"✅ {name}")
            passed += 1
        else:
            print(f"❌ {name} - Status {r.status_code}")
            failed += 1
    except:
        print(f"❌ {name} - Connection failed")
        failed += 1

print(f"\n✅ Passed: {passed}/{passed+failed}")