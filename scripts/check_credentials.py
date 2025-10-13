"""
Check and Update LinkedIn Credentials
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.credentials_manager import credentials_manager


def main():
    print("="*60)
    print("🔐 LINKEDIN CREDENTIALS CHECK")
    print("="*60)
    
    # Check existing credentials
    creds = credentials_manager.get_linkedin_credentials()
    
    if creds:
        print("\n✅ Found credentials:")
        print(f"   Email: {creds['email']}")
        print(f"   Password: {'*' * len(creds['password'])}")
    else:
        print("\n❌ No credentials found!")
    
    # Prompt to update
    print("\n" + "-"*60)
    update = input("Update credentials? (y/n): ").lower()
    
    if update == 'y':
        email = input("LinkedIn Email: ")
        password = input("LinkedIn Password: ")
        
        credentials_manager.save_linkedin_credentials(email, password)
        print("\n✅ Credentials saved!")
        
        # Verify
        creds = credentials_manager.get_linkedin_credentials()
        print(f"\n✅ Verified - Email: {creds['email']}")
    else:
        print("\n👍 Keeping existing credentials")


if __name__ == '__main__':
    main()