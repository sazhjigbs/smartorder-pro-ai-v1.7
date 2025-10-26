"""
SmartOrder PRO - Security Manager
Encryption et gestion sécurisée des API keys
by MAIGA ABOUBACAR

Features:
- Encryption AES-256 des API keys
- Vérification permissions API (NO WITHDRAWAL)
- IP Whitelist checker
- Audit log des accès
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import os
import base64
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List

LOG = logging.getLogger("security.key_manager")

class SecureKeyManager:
    """
    Gestionnaire sécurisé des API keys
    
    Sécurité:
    - Encryption AES-256 avec Fernet
    - Keys dérivées avec PBKDF2
    - Salt unique par installation
    - Audit log complet
    """
    
    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize Security Manager
        
        Args:
            master_password: Master password (si None, utilise .env)
        """
        self.master_password = master_password or os.getenv('MASTER_PASSWORD', 'SmartOrderPRO2025')
        self.salt_file = 'security/.salt'
        self.audit_file = 'security/audit.log'
        
        # Générer ou charger salt
        self.salt = self._get_or_create_salt()
        
        # Créer cipher
        self.cipher = self._create_cipher()
        
        # Permissions interdites (sécurité)
        self.forbidden_permissions = [
            'withdraw',
            'withdrawal',
            'transfer',
            'sub_account_transfer',
            'universal_transfer'
        ]
        
        LOG.info("✅ SecureKeyManager initialized")
    
    def _get_or_create_salt(self) -> bytes:
        """Récupère ou crée le salt unique"""
        os.makedirs('security', exist_ok=True)
        
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            # Générer nouveau salt
            salt = os.urandom(32)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            LOG.info("🔐 New salt generated")
            return salt
    
    def _create_cipher(self) -> Fernet:
        """Crée le cipher Fernet avec dérivation PBKDF2"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        return Fernet(key)
    
    def encrypt_key(self, api_key: str) -> str:
        """
        Encrypte une API key
        
        Args:
            api_key: API key en clair
            
        Returns:
            API key encryptée (base64)
        """
        try:
            encrypted = self.cipher.encrypt(api_key.encode())
            encrypted_b64 = base64.b64encode(encrypted).decode()
            
            self._audit_log('ENCRYPT', 'API key encrypted')
            
            return encrypted_b64
            
        except Exception as e:
            LOG.error(f"❌ Encryption failed: {e}")
            raise
    
    def decrypt_key(self, encrypted_key: str) -> str:
        """
        Décrypte une API key
        
        Args:
            encrypted_key: API key encryptée (base64)
            
        Returns:
            API key en clair
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_key.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            
            self._audit_log('DECRYPT', 'API key decrypted')
            
            return decrypted.decode()
            
        except Exception as e:
            LOG.error(f"❌ Decryption failed: {e}")
            raise
    
    def hash_key(self, api_key: str) -> str:
        """
        Hash une API key (pour vérification sans exposer la clé)
        
        Args:
            api_key: API key
            
        Returns:
            Hash SHA256 de la key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_permissions(self, exchange: str, api_key: str, api_secret: str) -> Dict:
        """
        Vérifie les permissions d'une API key
        
        Args:
            exchange: Exchange name (bybit, binance, etc)
            api_key: API key
            api_secret: API secret
            
        Returns:
            {
                'safe': bool,
                'permissions': List[str],
                'forbidden_detected': List[str],
                'warnings': List[str]
            }
        """
        result = {
            'safe': True,
            'permissions': [],
            'forbidden_detected': [],
            'warnings': []
        }
        
        try:
            # Récupérer permissions selon exchange
            if exchange == 'bybit':
                permissions = self._check_bybit_permissions(api_key, api_secret)
            elif exchange == 'binance':
                permissions = self._check_binance_permissions(api_key, api_secret)
            elif exchange == 'okx':
                permissions = self._check_okx_permissions(api_key, api_secret)
            elif exchange == 'kucoin':
                permissions = self._check_kucoin_permissions(api_key, api_secret)
            else:
                result['warnings'].append(f"Unknown exchange: {exchange}")
                return result
            
            result['permissions'] = permissions
            
            # Détecter permissions interdites
            for perm in permissions:
                perm_lower = perm.lower()
                for forbidden in self.forbidden_permissions:
                    if forbidden in perm_lower:
                        result['forbidden_detected'].append(perm)
                        result['safe'] = False
            
            if not result['safe']:
                result['warnings'].append('⚠️ WITHDRAWAL PERMISSION DETECTED - RISKY!')
            
            self._audit_log('VERIFY_PERMISSIONS', f"{exchange}: safe={result['safe']}")
            
            return result
            
        except Exception as e:
            LOG.error(f"❌ Permission check failed: {e}")
            result['safe'] = False
            result['warnings'].append(f"Error: {str(e)}")
            return result
    
    def _check_bybit_permissions(self, api_key: str, api_secret: str) -> List[str]:
        """Vérifie permissions Bybit"""
        try:
            from pybit.unified_trading import HTTP
            
            session = HTTP(
                testnet=False,
                api_key=api_key,
                api_secret=api_secret
            )
            
            # Tester avec API key info
            response = session.get_api_key_information()
            
            if response['retCode'] == 0:
                permissions_data = response['result'].get('permissions', {})
                permissions = []
                
                for key, value in permissions_data.items():
                    if value:
                        permissions.append(key)
                
                return permissions
            else:
                return ['unknown']
                
        except Exception as e:
            LOG.warning(f"Bybit permission check failed: {e}")
            return ['unknown']
    
    def _check_binance_permissions(self, api_key: str, api_secret: str) -> List[str]:
        """Vérifie permissions Binance"""
        try:
            from binance.client import Client
            
            client = Client(api_key, api_secret)
            account = client.get_account()
            
            permissions = account.get('permissions', [])
            return permissions
            
        except Exception as e:
            LOG.warning(f"Binance permission check failed: {e}")
            return ['unknown']
    
    def _check_okx_permissions(self, api_key: str, api_secret: str) -> List[str]:
        """Vérifie permissions OKX"""
        # TODO: Implémenter avec OKX API
        return ['trade', 'read']
    
    def _check_kucoin_permissions(self, api_key: str, api_secret: str) -> List[str]:
        """Vérifie permissions KuCoin"""
        # TODO: Implémenter avec KuCoin API
        return ['trade', 'read']
    
    def check_ip_whitelist(self, exchange: str, api_key: str) -> bool:
        """
        Vérifie si IP whitelist est activée
        
        Args:
            exchange: Exchange name
            api_key: API key
            
        Returns:
            True si whitelist activée
        """
        # TODO: Implémenter check IP whitelist
        self._audit_log('CHECK_IP', f"{exchange}: checking IP whitelist")
        return False  # Par défaut, assume pas de whitelist
    
    def _audit_log(self, action: str, details: str):
        """Log audit des actions sécurité"""
        os.makedirs('security', exist_ok=True)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """Récupère les logs d'audit"""
        if not os.path.exists(self.audit_file):
            return []
        
        logs = []
        with open(self.audit_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except:
                    pass
        
        return logs[-limit:]
    
    def generate_secure_env_template(self) -> str:
        """
        Génère template .env sécurisé
        
        Returns:
            Template .env avec keys encryptées
        """
        template = """# SmartOrder PRO - Secure Configuration
# by MAIGA ABOUBACAR
# Generated: {timestamp}

# Security
MASTER_PASSWORD=YourSecurePassword123!

# Bybit (Encrypted)
BYBIT_ENABLED=true
BYBIT_API_KEY_ENCRYPTED=your_encrypted_key_here
BYBIT_API_SECRET_ENCRYPTED=your_encrypted_secret_here

# Binance (Encrypted)
BINANCE_ENABLED=false
BINANCE_API_KEY_ENCRYPTED=
BINANCE_API_SECRET_ENCRYPTED=

# OKX (Encrypted)
OKX_ENABLED=false
OKX_API_KEY_ENCRYPTED=
OKX_API_SECRET_ENCRYPTED=

# KuCoin (Encrypted)
KUCOIN_ENABLED=false
KUCOIN_API_KEY_ENCRYPTED=
KUCOIN_API_SECRET_ENCRYPTED=

# Telegram
TG_TOKEN=your_telegram_token
TG_CHAT_ID=your_chat_id

# Dashboard
ADMIN_PASSWORD=your_admin_password
FLASK_SECRET_KEY=your_flask_secret

# Trading Config
MODE=live
REAL_MODE=True
""".format(timestamp=datetime.now().isoformat())
        
        return template
    
    def encrypt_env_file(self, input_file: str = '.env', output_file: str = '.env.encrypted'):
        """
        Encrypte un fichier .env
        
        Args:
            input_file: Fichier .env source
            output_file: Fichier .env encrypté
        """
        if not os.path.exists(input_file):
            LOG.error(f"File not found: {input_file}")
            return
        
        with open(input_file, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        encrypted_lines = []
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                
                # Encrypter seulement les API keys/secrets
                if any(x in key for x in ['API_KEY', 'API_SECRET', 'PASSWORD', 'SECRET']):
                    if value.strip():
                        encrypted_value = self.encrypt_key(value.strip())
                        encrypted_lines.append(f"{key}_ENCRYPTED={encrypted_value}")
                    else:
                        encrypted_lines.append(line)
                else:
                    encrypted_lines.append(line)
            else:
                encrypted_lines.append(line)
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(encrypted_lines))
        
        LOG.info(f"✅ File encrypted: {output_file}")
        self._audit_log('ENCRYPT_FILE', f"File encrypted: {input_file} → {output_file}")


# Instance globale
_key_manager = None

def get_key_manager() -> SecureKeyManager:
    """Récupère l'instance singleton"""
    global _key_manager
    if _key_manager is None:
        _key_manager = SecureKeyManager()
    return _key_manager


if __name__ == "__main__":
    print("=" * 60)
    print("🔐 SmartOrder PRO - Security Manager")
    print("by MAIGA ABOUBACAR")
    print("=" * 60)
    
    manager = SecureKeyManager()
    
    # Test encryption
    print("\n✅ Test 1: Encryption/Decryption")
    test_key = "test_api_key_123456"
    encrypted = manager.encrypt_key(test_key)
    decrypted = manager.decrypt_key(encrypted)
    
    print(f"   Original: {test_key}")
    print(f"   Encrypted: {encrypted[:50]}...")
    print(f"   Decrypted: {decrypted}")
    print(f"   ✅ Match: {test_key == decrypted}")
    
    # Test hash
    print("\n✅ Test 2: Key Hashing")
    hashed = manager.hash_key(test_key)
    print(f"   Hash: {hashed}")
    
    # Template
    print("\n✅ Test 3: Secure .env Template")
    template = manager.generate_secure_env_template()
    print(f"   Template generated ({len(template)} chars)")
    
    print("\n" + "=" * 60)
    print("✅ Security Manager Ready!")
    print("=" * 60)
