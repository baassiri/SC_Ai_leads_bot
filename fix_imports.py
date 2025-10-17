"""
Quick Fix for Import Issue
Run this to fix the app.py import problem
"""

import os
from pathlib import Path

# Path to app.py
app_file = Path("backend/app.py")

if not app_file.exists():
    print("❌ backend/app.py not found!")
    print(f"Current directory: {os.getcwd()}")
    exit(1)

# Read the file
with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the problematic import section
old_import = """from backend.ai_engine.message_generator_abc import ABCMessageGenerator
from backend.automation.scheduler import scheduler as message_scheduler
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import Config, get_config
from backend.api.missing_endpoints import register_missing_endpoints
from backend.database.db_manager import db_manager

from backend.credentials_manager import credentials_manager
from backend.scraping_cooldown_manager import get_cooldown_manager
from backend.linkedin.linkedin_sender import LinkedInSender"""

new_import = """# Fix import paths - add project root to path FIRST
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai_engine.message_generator_abc import ABCMessageGenerator
from backend.automation.scheduler import scheduler as message_scheduler
from backend.config import Config, get_config
from backend.api.missing_endpoints import register_missing_endpoints
from backend.database.db_manager import db_manager
from backend.credentials_manager import credentials_manager
from backend.scraping_cooldown_manager import get_cooldown_manager
from backend.linkedin.linkedin_sender import LinkedInSender"""

if old_import in content:
    content = content.replace(old_import, new_import)
    
    # Write back
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed app.py import issue!")
    print("\nNow run: START_WINDOWS.bat")
else:
    print("⚠️  Could not find the exact import section to replace")
    print("The file might already be fixed or have a different format")
    print("\nTry running: START_WINDOWS.bat anyway")