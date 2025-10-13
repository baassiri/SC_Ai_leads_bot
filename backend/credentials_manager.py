"""
Credentials Manager - Secure storage for API keys and credentials
"""

import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
import base64

class CredentialsManager:
    def __init__(self):
        self.data_dir = Path('data')
        self.credentials_file = self.data_dir / 'credentials.json'
        self.key_file = self.data_dir / 'secret.key'
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Load or generate encryption key
        self.cipher = self._get_cipher()
    
    def _get_cipher(self):
        """Get or create encryption cipher"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        
        return Fernet(key)
    
    def _encrypt(self, data):
        """Encrypt sensitive data"""
        if not data:
            return None
        return self.cipher.encrypt(data.encode()).decode()
    
    def _decrypt(self, encrypted_data):
        """Decrypt sensitive data"""
        if not encrypted_data:
            return None
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except:
            return None
    
    def save_credentials(self, linkedin_email=None, linkedin_password=None, openai_api_key=None):
        """Save credentials (encrypts passwords)"""
        # Load existing credentials
        creds = self.get_all_credentials()
        
        # Update with new values (only if provided)
        if linkedin_email:
            creds['linkedin_email'] = linkedin_email
        
        if linkedin_password:
            creds['linkedin_password'] = self._encrypt(linkedin_password)
        
        if openai_api_key:
            creds['openai_api_key'] = self._encrypt(openai_api_key)
        
        # Save to file
        with open(self.credentials_file, 'w') as f:
            json.dump(creds, f, indent=2)
        
        print(f"✅ Credentials saved to: {self.credentials_file}")
        return True
    
    def save_all_credentials(self, linkedin_email, linkedin_password, openai_api_key, sales_nav_enabled=False):
        """Save all credentials at once"""
        creds = {
            'linkedin_email': linkedin_email,
            'linkedin_password': self._encrypt(linkedin_password),
            'openai_api_key': self._encrypt(openai_api_key),
            'sales_nav_enabled': sales_nav_enabled
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(creds, f, indent=2)
        
        print(f"✅ All credentials saved")
        return True
    
    def get_all_credentials(self):
        """Get all credentials (decrypts passwords)"""
        if not self.credentials_file.exists():
            return {
                'linkedin_email': '',
                'linkedin_password': '',
                'openai_api_key': '',
                'sales_nav_enabled': False
            }
        
        try:
            with open(self.credentials_file, 'r') as f:
                creds = json.load(f)
            
            # Decrypt sensitive fields
            if 'linkedin_password' in creds and creds['linkedin_password']:
                creds['linkedin_password'] = self._decrypt(creds['linkedin_password'])
            
            if 'openai_api_key' in creds and creds['openai_api_key']:
                creds['openai_api_key'] = self._decrypt(creds['openai_api_key'])
            
            return creds
        except Exception as e:
            print(f"Error loading credentials: {str(e)}")
            return {
                'linkedin_email': '',
                'linkedin_password': '',
                'openai_api_key': '',
                'sales_nav_enabled': False
            }
    
    def get_linkedin_credentials(self):
        """Get LinkedIn credentials"""
        creds = self.get_all_credentials()
        
        email = creds.get('linkedin_email')
        password = creds.get('linkedin_password')
        
        if not email or not password:
            return None
        
        return {
            'email': email,
            'password': password,
            'sales_nav_enabled': creds.get('sales_nav_enabled', False)
        }
    
    def get_openai_key(self):
        """Get OpenAI API key"""
        creds = self.get_all_credentials()
        return creds.get('openai_api_key')
    
    def clear_credentials(self):
        """Clear all stored credentials"""
        if self.credentials_file.exists():
            os.remove(self.credentials_file)
        print("✅ Credentials cleared")
        return True


# Global instance
credentials_manager = CredentialsManager()