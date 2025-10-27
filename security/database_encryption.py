"""
Database Encryption System
Chiffre et stocke les API keys de manière sécurisée dans SQLite

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import os
import sqlite3
import logging
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Dict, Optional
import base64
import hashlib

LOG = logging.getLogger(__name__)


class DatabaseEncryption:
    """
    Système de chiffrement pour API keys dans base de données
    
    Features:
    - AES-256 encryption (via Fernet)
    - Master key depuis env variable
    - Stockage SQLite sécurisé
    - Support multi-exchange
    """
    
    def __init__(self, db_path: str = None, master_key: str = None):
        """
        Initialize Database Encryption
        
        Args:
            db_path: Path to SQLite database
            master_key: Master encryption key (from env if not provided)
        """
        # Database path
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'data/smartorder.db')
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Master key
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')
        
        if not self.master_key:
            # Generate new master key if not exists
            LOG.warning("⚠️ No master key found, generating new one...")
            self.master_key = self._generate_master_key()
            LOG.info(f"✅ Master key generated. Add to .env:\nENCRYPTION_MASTER_KEY={self.master_key}")
        
        # Fernet cipher
        self.cipher = self._init_cipher()
        
        # Initialize database
        self._init_database()
        
        LOG.info("✅ Database Encryption initialized")
    
    def _generate_master_key(self) -> str:
        """Generate a new Fernet master key"""
        return Fernet.generate_key().decode('utf-8')
    
    def _init_cipher(self) -> Fernet:
        """Initialize Fernet cipher from master key"""
        try:
            # Ensure key is in bytes
            if isinstance(self.master_key, str):
                key_bytes = self.master_key.encode('utf-8')
            else:
                key_bytes = self.master_key
            
            return Fernet(key_bytes)
        
        except Exception as e:
            LOG.error(f"❌ Failed to initialize cipher: {e}")
            raise
    
    def _init_database(self):
        """Initialize SQLite database with API keys table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for encrypted API keys
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT NOT NULL UNIQUE,
                api_key_encrypted TEXT NOT NULL,
                api_secret_encrypted TEXT NOT NULL,
                passphrase_encrypted TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_exchange 
            ON api_keys(exchange)
        ''')
        
        conn.commit()
        conn.close()
        
        LOG.info(f"✅ Database initialized at {self.db_path}")
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data
        
        Args:
            data: Plain text to encrypt
        
        Returns:
            Encrypted data (base64 string)
        """
        if not data:
            return ""
        
        try:
            encrypted_bytes = self.cipher.encrypt(data.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        
        except Exception as e:
            LOG.error(f"❌ Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Encrypted data (base64 string)
        
        Returns:
            Plain text
        """
        if not encrypted_data:
            return ""
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        
        except Exception as e:
            LOG.error(f"❌ Decryption failed: {e}")
            raise
    
    def store_api_keys(self,
                       exchange: str,
                       api_key: str,
                       api_secret: str,
                       passphrase: str = None) -> bool:
        """
        Store encrypted API keys in database
        
        Args:
            exchange: Exchange name (bybit, binance, okx, kucoin)
            api_key: API key (plain text)
            api_secret: API secret (plain text)
            passphrase: API passphrase for OKX/KuCoin (optional)
        
        Returns:
            Success status
        """
        try:
            # Encrypt keys
            encrypted_key = self.encrypt(api_key)
            encrypted_secret = self.encrypt(api_secret)
            encrypted_passphrase = self.encrypt(passphrase) if passphrase else None
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO api_keys 
                (exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (exchange, encrypted_key, encrypted_secret, encrypted_passphrase))
            
            conn.commit()
            conn.close()
            
            LOG.info(f"✅ API keys stored for {exchange}")
            return True
        
        except Exception as e:
            LOG.error(f"❌ Failed to store API keys for {exchange}: {e}")
            return False
    
    def get_api_keys(self, exchange: str) -> Optional[Dict]:
        """
        Retrieve and decrypt API keys from database
        
        Args:
            exchange: Exchange name
        
        Returns:
            Dictionary with api_key, api_secret, passphrase (decrypted)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT api_key_encrypted, api_secret_encrypted, passphrase_encrypted
                FROM api_keys
                WHERE exchange = ?
            ''', (exchange,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                LOG.warning(f"⚠️ No API keys found for {exchange}")
                return None
            
            # Decrypt keys
            api_key = self.decrypt(result[0])
            api_secret = self.decrypt(result[1])
            passphrase = self.decrypt(result[2]) if result[2] else None
            
            return {
                'api_key': api_key,
                'api_secret': api_secret,
                'passphrase': passphrase
            }
        
        except Exception as e:
            LOG.error(f"❌ Failed to retrieve API keys for {exchange}: {e}")
            return None
    
    def delete_api_keys(self, exchange: str) -> bool:
        """
        Delete API keys for an exchange
        
        Args:
            exchange: Exchange name
        
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM api_keys WHERE exchange = ?', (exchange,))
            
            conn.commit()
            conn.close()
            
            LOG.info(f"✅ API keys deleted for {exchange}")
            return True
        
        except Exception as e:
            LOG.error(f"❌ Failed to delete API keys for {exchange}: {e}")
            return False
    
    def list_exchanges(self) -> list:
        """
        List all exchanges with stored API keys
        
        Returns:
            List of exchange names
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT exchange FROM api_keys')
            
            results = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in results]
        
        except Exception as e:
            LOG.error(f"❌ Failed to list exchanges: {e}")
            return []
    
    def rotate_master_key(self, new_master_key: str) -> bool:
        """
        Rotate master encryption key (re-encrypt all keys)
        
        Args:
            new_master_key: New master key
        
        Returns:
            Success status
        """
        try:
            # Get all current keys (decrypted)
            exchanges = self.list_exchanges()
            all_keys = {}
            
            for exchange in exchanges:
                keys = self.get_api_keys(exchange)
                if keys:
                    all_keys[exchange] = keys
            
            # Update master key and cipher
            self.master_key = new_master_key
            self.cipher = self._init_cipher()
            
            # Re-encrypt and store all keys
            for exchange, keys in all_keys.items():
                self.store_api_keys(
                    exchange=exchange,
                    api_key=keys['api_key'],
                    api_secret=keys['api_secret'],
                    passphrase=keys.get('passphrase')
                )
            
            LOG.info(f"✅ Master key rotated for {len(all_keys)} exchanges")
            return True
        
        except Exception as e:
            LOG.error(f"❌ Failed to rotate master key: {e}")
            return False
    
    def verify_encryption(self) -> bool:
        """
        Verify encryption system is working
        
        Returns:
            True if encryption/decryption works
        """
        try:
            test_data = "test_encryption_123"
            encrypted = self.encrypt(test_data)
            decrypted = self.decrypt(encrypted)
            
            success = test_data == decrypted
            
            if success:
                LOG.info("✅ Encryption verification passed")
            else:
                LOG.error("❌ Encryption verification failed")
            
            return success
        
        except Exception as e:
            LOG.error(f"❌ Encryption verification error: {e}")
            return False


# CLI utility functions
def setup_encryption(db_path: str = None):
    """Setup encryption system (generate master key if needed)"""
    enc = DatabaseEncryption(db_path=db_path)
    
    if enc.verify_encryption():
        print("✅ Encryption system ready")
        print(f"\nMaster key: {enc.master_key}")
        print("\n⚠️ IMPORTANT: Add this to your .env file:")
        print(f"ENCRYPTION_MASTER_KEY={enc.master_key}")
        print("\n⚠️ KEEP THIS KEY SAFE! Without it, you cannot decrypt your API keys!")
    else:
        print("❌ Encryption system failed verification")


def store_keys_cli():
    """CLI tool to store API keys"""
    import getpass
    
    enc = DatabaseEncryption()
    
    print("🔐 SmartOrder PRO - API Key Storage")
    print("=" * 50)
    
    exchange = input("Exchange (bybit/binance/okx/kucoin): ").lower()
    api_key = getpass.getpass("API Key: ")
    api_secret = getpass.getpass("API Secret: ")
    
    passphrase = None
    if exchange in ['okx', 'kucoin']:
        passphrase = getpass.getpass("Passphrase: ")
    
    if enc.store_api_keys(exchange, api_key, api_secret, passphrase):
        print(f"✅ API keys stored for {exchange}")
    else:
        print(f"❌ Failed to store API keys")


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_encryption()
    elif len(sys.argv) > 1 and sys.argv[1] == "store":
        store_keys_cli()
    else:
        print("Usage:")
        print("  python database_encryption.py setup  # Setup encryption")
        print("  python database_encryption.py store  # Store API keys")
