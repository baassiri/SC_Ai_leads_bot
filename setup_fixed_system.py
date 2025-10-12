#!/usr/bin/env python
"""
Quick Setup Script - Install Fixed Credentials System
"""

import shutil
from pathlib import Path

def setup_fixed_system():
    print("=" * 60)
    print("🔧 INSTALLING FIXED CREDENTIALS SYSTEM")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent
    backend_dir = project_root / 'backend'
    
    # Create backend directory if it doesn't exist
    backend_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy credentials_manager.py to backend
    credentials_src = project_root / 'credentials_manager.py'
    credentials_dst = backend_dir / 'credentials_manager.py'
    
    if credentials_src.exists():
        shutil.copy(credentials_src, credentials_dst)
        print(f"✅ Installed: {credentials_dst}")
    else:
        print(f"⚠️  Source file not found: {credentials_src}")
    
    # Backup old app.py
    old_app = backend_dir / 'app.py'
    if old_app.exists():
        backup_app = backend_dir / 'app_backup.py'
        shutil.copy(old_app, backup_app)
        print(f"✅ Backed up old app.py to: {backup_app}")
    
    # Copy new app.py
    app_src = project_root / 'app_fixed.py'
    app_dst = backend_dir / 'app.py'
    
    if app_src.exists():
        shutil.copy(app_src, app_dst)
        print(f"✅ Installed: {app_dst}")
    else:
        print(f"⚠️  Source file not found: {app_src}")
    
    print("\n" + "=" * 60)
    print("✅ INSTALLATION COMPLETE!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Run: python backend/app.py")
    print("2. Visit: http://localhost:5000")
    print("3. Enter your LinkedIn and OpenAI credentials")
    print("4. Click 'Test OpenAI' to verify")
    print("5. Click 'Save Credentials'")
    print("6. Start scraping leads!")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    setup_fixed_system()