"""
Fix: 400 Bad Request Error When Starting Bot
=============================================
The frontend is sending an empty body, causing JSON decode error.
This fixes shared.js to send proper JSON body.
"""

from pathlib import Path

print("=" * 70)
print("🔧 FIXING START BOT JSON ERROR")
print("=" * 70)

shared_js = Path("frontend/static/js/shared.js")

if not shared_js.exists():
    print("❌ File not found!")
    exit(1)

print("\n📂 Found shared.js")

# Read file
with open(shared_js, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the startBot function
old_code = """async function startBot() {
    try {
        showNotification('Starting bot...', 'info');
        
        const response = await fetch('/api/bot/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });"""

new_code = """async function startBot() {
    try {
        showNotification('Starting bot...', 'info');
        
        const response = await fetch('/api/bot/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})  // ✅ FIX: Send empty JSON object
        });"""

if old_code in content:
    content = content.replace(old_code, new_code)
    
    # Save
    with open(shared_js, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed startBot() function")
    print("   Added: body: JSON.stringify({})")
else:
    print("⚠️ Could not find exact code")
    print("\nManual fix:")
    print("1. Open: frontend/static/js/shared.js")
    print("2. Find the startBot() function (around line 62)")
    print("3. In the fetch() call, add after headers:")
    print("   body: JSON.stringify({})")

print("\n" + "=" * 70)
print("✅ DONE! Restart server to apply fix.")
print("=" * 70)
