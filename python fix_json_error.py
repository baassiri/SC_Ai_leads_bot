"""
Fix for JSON Decode Error in /api/bot/start endpoint
This fixes the 400 Bad Request error
"""

import os
from pathlib import Path

# Path to app.py
app_file = Path("backend/app.py")

if not app_file.exists():
    print("❌ backend/app.py not found!")
    exit(1)

# Read the file
with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the line that reads request.json
old_line = "        request_data = request.json or {}"

# Replace with safer version that handles empty body
new_line = "        request_data = request.get_json(silent=True) or {}"

if old_line in content:
    content = content.replace(old_line, new_line)
    
    # Write back
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed JSON decode error in app.py!")
    print("\nThe bot will now handle requests without JSON body properly.")
    print("\nRestart the server:")
    print("1. Press Ctrl+C to stop current server")
    print("2. Run: START_WINDOWS.bat")
else:
    print("⚠️  Could not find the exact line to replace")
    print("The file might already be fixed")
    
print("\nDone!")