"""
Encryption Utilities for SC AI Lead Generation System
Handles secure encryption/decryption of sensitive credentials

Usage:
    from backend.utils.encryption import encrypt_credential, decrypt_credential
    
    # Encrypt
    encrypted = encrypt_credential("my_password123")
    
    # Decrypt
    original = decrypt_credential(encrypted)
"""

import os
from cryptography.fernet import Fernet
from pathlib import Path


class CredentialEncryption:
    """Handles encryption and decryption of sensitive credentials"""
    
    def __init__(self):
        """Initialize with encryption key from environment or generate new one"""
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or create new one"""
        # Try to get key from environment variable
        key_string = os.getenv('ENCRYPTION_KEY')
        
        if key_string:
            # Key exists in environment
            return key_string.encode()
        
        # Generate new key and save to .env file
        new_key = Fernet.generate_key()
        self._save_key_to_env(new_key)
        
        print("🔐 Generated new encryption key and saved to .env")
        print("⚠️  IMPORTANT: Backup your .env file - lost keys = lost credentials!")
        
        return new_key
    
    def _save_key_to_env(self, key: bytes):
        """Save encryption key to .env file"""
        env_path = Path(__file__).parent.parent.parent / '.env'
        
        key_string = key.decode()
        env_line = f'\n# Encryption key for credentials\nENCRYPTION_KEY={key_string}\n'
        
        # Check if key already exists
        if env_path.exists():
            with open(env_path, 'r') as f:
                content = f.read()
                if 'ENCRYPTION_KEY=' in content:
                    return  # Key already exists
        
        # Append key to .env
        with open(env_path, 'a') as f:
            f.write(env_line)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string credential"""
        if not plaintext:
            return None
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt an encrypted credential"""
        if not encrypted_text:
            return None
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            print(f"❌ Decryption failed: {str(e)}")
            print("⚠️  This usually means:")
            print("   1. The ENCRYPTION_KEY changed")
            print("   2. The data was not encrypted with this key")
            print("   3. The data is corrupted")
            return None
    
    def is_encrypted(self, text: str) -> bool:
        """Check if a string appears to be encrypted"""
        if not text:
            return False
        
        try:
            # Fernet encrypted strings are always base64-urlsafe
            # and start with 'gAAAAA'
            return text.startswith('gAAAAA')
        except:
            return False


# Singleton instance
_encryptor = CredentialEncryption()


def encrypt_credential(plaintext: str) -> str:
    """
    Encrypt a credential string
    
    Args:
        plaintext: The credential to encrypt (password, API key, etc.)
    
    Returns:
        Encrypted string safe to store in database
    
    Example:
        >>> encrypted_password = encrypt_credential("mySecretPassword123")
        >>> print(encrypted_password)
        'gAAAAABhX...'
    """
    return _encryptor.encrypt(plaintext)


def decrypt_credential(encrypted_text: str) -> str:
    """
    Decrypt an encrypted credential
    
    Args:
        encrypted_text: The encrypted string from database
    
    Returns:
        Original plaintext credential
    
    Example:
        >>> password = decrypt_credential("gAAAAABhX...")
        >>> print(password)
        'mySecretPassword123'
    """
    return _encryptor.decrypt(encrypted_text)


def is_encrypted(text: str) -> bool:
    """
    Check if a credential appears to be encrypted
    
    Args:
        text: The string to check
    
    Returns:
        True if encrypted, False if plaintext
    
    Example:
        >>> is_encrypted("gAAAAABhX...")
        True
        >>> is_encrypted("myPassword123")
        False
    """
    return _encryptor.is_encrypted(text)


def migrate_plaintext_to_encrypted(plaintext: str) -> str:
    """
    Migrate plaintext credential to encrypted format
    Only encrypts if not already encrypted
    
    Args:
        plaintext: Credential that might be plaintext or encrypted
    
    Returns:
        Encrypted credential
    
    Example:
        >>> credential = migrate_plaintext_to_encrypted("oldPassword")
        >>> # If already encrypted, returns same value
        >>> credential = migrate_plaintext_to_encrypted(credential)
    """
    if is_encrypted(plaintext):
        return plaintext  # Already encrypted
    
    return encrypt_credential(plaintext)


# Convenience functions for common credential types

def encrypt_linkedin_credentials(email: str, password: str) -> tuple:
    """Encrypt LinkedIn credentials"""
    return encrypt_credential(email), encrypt_credential(password)


def decrypt_linkedin_credentials(encrypted_email: str, encrypted_password: str) -> tuple:
    """Decrypt LinkedIn credentials"""
    return decrypt_credential(encrypted_email), decrypt_credential(encrypted_password)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key"""
    return encrypt_credential(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    return decrypt_credential(encrypted_key)


if __name__ == '__main__':
    """Test encryption functionality"""
    print("🧪 Testing Encryption Module\n")
    
    # Test basic encryption
    test_password = "MySecurePassword123!"
    print(f"Original: {test_password}")
    
    encrypted = encrypt_credential(test_password)
    print(f"Encrypted: {encrypted}")
    
    decrypted = decrypt_credential(encrypted)
    print(f"Decrypted: {decrypted}")
    
    # Verify
    if test_password == decrypted:
        print("\n✅ Encryption/Decryption working correctly!")
    else:
        print("\n❌ Encryption/Decryption FAILED!")
    
    # Test detection
    print(f"\nIs '{encrypted}' encrypted? {is_encrypted(encrypted)}")
    print(f"Is '{test_password}' encrypted? {is_encrypted(test_password)}")
    
    # Test migration
    print("\n🔄 Testing migration:")
    migrated_once = migrate_plaintext_to_encrypted("plaintext_password")
    print(f"First migration: {migrated_once}")
    
    migrated_twice = migrate_plaintext_to_encrypted(migrated_once)
    print(f"Second migration (should be same): {migrated_twice}")
    
    if migrated_once == migrated_twice:
        print("✅ Migration idempotency working!")
    else:
        print("❌ Migration FAILED!")