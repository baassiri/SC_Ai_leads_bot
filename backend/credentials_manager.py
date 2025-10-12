"""
SC AI Lead Generation System - Credentials Manager
Secure storage and retrieval of user credentials
UPDATED: Now includes Sales Navigator preference
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict


class CredentialsManager:
    """Manage user credentials securely"""
    
    def __init__(self, storage_path: str = None):
        """
        Initialize credentials manager
        
        Args:
            storage_path: Path to store credentials (defaults to data/credentials.json)
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Default to data directory
            base_dir = Path(__file__).parent.parent.parent
            self.storage_path = base_dir / 'data' / 'credentials.json'
        
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage if it doesn't exist
        if not self.storage_path.exists():
            self._initialize_storage()
    
    def _initialize_storage(self):
        """Create empty credentials storage"""
        initial_data = {
            'linkedin': {
                'email': '',
                'password': '',
                'sales_nav_enabled': False
            },
            'openai': {
                'api_key': ''
            },
            'hubspot': {
                'api_key': ''
            }
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(initial_data, f, indent=2)
        
        print(f"✅ Initialized credentials storage at: {self.storage_path}")
    
    def _load_credentials(self) -> Dict:
        """Load credentials from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict):
        """Save credentials to storage"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            print(f"✅ Credentials saved to: {self.storage_path}")
        except Exception as e:
            print(f"Error saving credentials: {e}")
    
    def save_linkedin_credentials(self, email: str, password: str, sales_nav_enabled: bool = False) -> bool:
        """
        Save LinkedIn credentials
        
        Args:
            email: LinkedIn email
            password: LinkedIn password
            sales_nav_enabled: Whether user has Sales Navigator
            
        Returns:
            bool: True if successful
        """
        try:
            credentials = self._load_credentials()
            
            credentials['linkedin'] = {
                'email': email,
                'password': password,
                'sales_nav_enabled': sales_nav_enabled
            }
            
            self._save_credentials(credentials)
            return True
        except Exception as e:
            print(f"Error saving LinkedIn credentials: {e}")
            return False
    
    def get_linkedin_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get LinkedIn credentials
        
        Returns:
            Dict with 'email', 'password', and 'sales_nav_enabled', or None if not found
        """
        try:
            credentials = self._load_credentials()
            linkedin_creds = credentials.get('linkedin', {})
            
            if linkedin_creds.get('email') and linkedin_creds.get('password'):
                return {
                    'email': linkedin_creds['email'],
                    'password': linkedin_creds['password'],
                    'sales_nav_enabled': linkedin_creds.get('sales_nav_enabled', False)
                }
            return None
        except Exception as e:
            print(f"Error getting LinkedIn credentials: {e}")
            return None
    
    def has_sales_navigator(self) -> bool:
        """
        Check if user has Sales Navigator enabled
        
        Returns:
            bool: True if Sales Navigator is enabled
        """
        try:
            linkedin_creds = self.get_linkedin_credentials()
            if linkedin_creds:
                return linkedin_creds.get('sales_nav_enabled', False)
            return False
        except Exception as e:
            print(f"Error checking Sales Navigator status: {e}")
            return False
    
    def save_openai_key(self, api_key: str) -> bool:
        """
        Save OpenAI API key
        
        Args:
            api_key: OpenAI API key
            
        Returns:
            bool: True if successful
        """
        try:
            credentials = self._load_credentials()
            
            credentials['openai'] = {
                'api_key': api_key
            }
            
            self._save_credentials(credentials)
            return True
        except Exception as e:
            print(f"Error saving OpenAI key: {e}")
            return False
    
    def get_openai_key(self) -> Optional[str]:
        """
        Get OpenAI API key
        
        Returns:
            str: API key or None if not found
        """
        try:
            credentials = self._load_credentials()
            openai_creds = credentials.get('openai', {})
            api_key = openai_creds.get('api_key', '')
            
            if api_key and api_key != '' and not api_key.startswith('sk-your-'):
                return api_key
            return None
        except Exception as e:
            print(f"Error getting OpenAI key: {e}")
            return None
    
    def save_hubspot_key(self, api_key: str) -> bool:
        """
        Save HubSpot API key
        
        Args:
            api_key: HubSpot API key
            
        Returns:
            bool: True if successful
        """
        try:
            credentials = self._load_credentials()
            
            credentials['hubspot'] = {
                'api_key': api_key
            }
            
            self._save_credentials(credentials)
            return True
        except Exception as e:
            print(f"Error saving HubSpot key: {e}")
            return False
    
    def get_hubspot_key(self) -> Optional[str]:
        """
        Get HubSpot API key
        
        Returns:
            str: API key or None if not found
        """
        try:
            credentials = self._load_credentials()
            hubspot_creds = credentials.get('hubspot', {})
            return hubspot_creds.get('api_key')
        except Exception as e:
            print(f"Error getting HubSpot key: {e}")
            return None
    
    def save_all_credentials(self, linkedin_email: str = None, 
                           linkedin_password: str = None,
                           openai_api_key: str = None,
                           hubspot_api_key: str = None,
                           sales_nav_enabled: bool = None) -> bool:
        """
        Save multiple credentials at once
        
        Args:
            linkedin_email: LinkedIn email
            linkedin_password: LinkedIn password
            openai_api_key: OpenAI API key
            hubspot_api_key: HubSpot API key
            sales_nav_enabled: Whether user has Sales Navigator
            
        Returns:
            bool: True if successful
        """
        try:
            credentials = self._load_credentials()
            
            # Update LinkedIn if provided
            if linkedin_email and linkedin_password:
                credentials['linkedin'] = {
                    'email': linkedin_email,
                    'password': linkedin_password,
                    'sales_nav_enabled': sales_nav_enabled if sales_nav_enabled is not None else False
                }
            
            # Update OpenAI if provided
            if openai_api_key:
                credentials['openai'] = {
                    'api_key': openai_api_key
                }
            
            # Update HubSpot if provided
            if hubspot_api_key:
                credentials['hubspot'] = {
                    'api_key': hubspot_api_key
                }
            
            self._save_credentials(credentials)
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
    
    def get_all_credentials(self) -> Dict:
        """
        Get all stored credentials
        
        Returns:
            Dict with all credentials (sensitive data masked)
        """
        try:
            credentials = self._load_credentials()
            
            # Mask sensitive data for display
            masked_credentials = {
                'linkedin': {
                    'email': credentials.get('linkedin', {}).get('email', ''),
                    'password': '***' if credentials.get('linkedin', {}).get('password') else '',
                    'sales_nav_enabled': credentials.get('linkedin', {}).get('sales_nav_enabled', False)
                },
                'openai': {
                    'api_key': f"sk-...{credentials.get('openai', {}).get('api_key', '')[-4:]}" if credentials.get('openai', {}).get('api_key') else ''
                },
                'hubspot': {
                    'api_key': f"...{credentials.get('hubspot', {}).get('api_key', '')[-4:]}" if credentials.get('hubspot', {}).get('api_key') else ''
                }
            }
            
            return masked_credentials
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return {}
    
    def test_openai_connection(self) -> bool:
        """
        Test OpenAI API key
        
        Returns:
            bool: True if connection successful
        """
        api_key = self.get_openai_key()
        
        if not api_key:
            print("❌ No OpenAI API key found")
            return False
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            # Simple test request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'test successful'"}],
                max_tokens=10
            )
            
            print("✅ OpenAI connection successful!")
            return True
        except Exception as e:
            print(f"❌ OpenAI connection failed: {str(e)}")
            return False
    
    def clear_all_credentials(self) -> bool:
        """
        Clear all stored credentials
        
        Returns:
            bool: True if successful
        """
        try:
            self._initialize_storage()
            print("✅ All credentials cleared")
            return True
        except Exception as e:
            print(f"Error clearing credentials: {e}")
            return False


# Singleton instance
credentials_manager = CredentialsManager()


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Credentials Manager')
    parser.add_argument('--save-linkedin', nargs=2, metavar=('EMAIL', 'PASSWORD'), 
                       help='Save LinkedIn credentials')
    parser.add_argument('--save-openai', metavar='API_KEY', 
                       help='Save OpenAI API key')
    parser.add_argument('--test-openai', action='store_true',
                       help='Test OpenAI connection')
    parser.add_argument('--show', action='store_true',
                       help='Show all credentials (masked)')
    parser.add_argument('--clear', action='store_true',
                       help='Clear all credentials')
    
    args = parser.parse_args()
    
    if args.save_linkedin:
        email, password = args.save_linkedin
        if credentials_manager.save_linkedin_credentials(email, password):
            print(f"✅ LinkedIn credentials saved: {email}")
    
    if args.save_openai:
        if credentials_manager.save_openai_key(args.save_openai):
            print(f"✅ OpenAI API key saved")
    
    if args.test_openai:
        credentials_manager.test_openai_connection()
    
    if args.show:
        creds = credentials_manager.get_all_credentials()
        print("\n📋 Stored Credentials:")
        print(json.dumps(creds, indent=2))
    
    if args.clear:
        if credentials_manager.clear_all_credentials():
            print("✅ All credentials cleared")