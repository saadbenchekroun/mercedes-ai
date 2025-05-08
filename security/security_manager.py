"""
Security manager for handling authentication and encryption.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
import json
from pathlib import Path
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import settings

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security features including authentication and encryption."""
    
    def __init__(self):
        """Initialize the security manager."""
        self.secrets_file = Path(settings.SECRETS_DIR) / "secrets.json"
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._secrets: Dict[str, Any] = self._load_secrets()
        self._secrets_lock = asyncio.Lock()
        
        # Initialize encryption
        self._encryption_key = self._derive_key(settings.ENCRYPTION_SALT)
        self._fernet = Fernet(self._encryption_key)
        
        logger.info("Security manager initialized")
    
    def _load_secrets(self) -> Dict[str, Any]:
        """
        Load secrets from file.
        
        Returns:
            Dict[str, Any]: Loaded secrets
        """
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading secrets: {str(e)}")
                return self._get_default_secrets()
        else:
            return self._get_default_secrets()
    
    def _get_default_secrets(self) -> Dict[str, Any]:
        """
        Get default secrets.
        
        Returns:
            Dict[str, Any]: Default secrets
        """
        return {
            "api_keys": {},
            "tokens": {},
            "certificates": {},
            "encryption_keys": {}
        }
    
    def _derive_key(self, salt: str) -> bytes:
        """
        Derive encryption key from salt.
        
        Args:
            salt: Salt for key derivation
            
        Returns:
            bytes: Derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000
        )
        return base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
    
    async def _save_secrets(self):
        """Save secrets to file."""
        try:
            with open(self.secrets_file, "w") as f:
                json.dump(self._secrets, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving secrets: {str(e)}")
            raise
    
    async def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """
        Generate JWT token for user.
        
        Args:
            user_id: User ID
            expires_in: Token expiration time in seconds
            
        Returns:
            str: Generated token
        """
        try:
            # Create token payload
            payload = {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(seconds=expires_in),
                "iat": datetime.utcnow()
            }
            
            # Generate token
            token = jwt.encode(
                payload,
                settings.JWT_SECRET,
                algorithm="HS256"
            )
            
            # Store token
            async with self._secrets_lock:
                self._secrets["tokens"][user_id] = {
                    "token": token,
                    "expires_at": payload["exp"].isoformat()
                }
                await self._save_secrets()
            
            return token
            
        except Exception as e:
            logger.error(f"Error generating token: {str(e)}")
            raise
    
    async def verify_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Verify JWT token.
        
        Args:
            token: Token to verify
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, user_id)
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"]
            )
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                return False, None
            
            return True, payload["user_id"]
            
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return False, None
    
    async def store_api_key(self, service: str, key: str):
        """
        Store API key.
        
        Args:
            service: Service name
            key: API key
        """
        try:
            # Encrypt key
            encrypted_key = self._fernet.encrypt(key.encode())
            
            # Store encrypted key
            async with self._secrets_lock:
                self._secrets["api_keys"][service] = encrypted_key.decode()
                await self._save_secrets()
            
            logger.info(f"Stored API key for {service}")
            
        except Exception as e:
            logger.error(f"Error storing API key: {str(e)}")
            raise
    
    async def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key.
        
        Args:
            service: Service name
            
        Returns:
            Optional[str]: API key
        """
        try:
            async with self._secrets_lock:
                encrypted_key = self._secrets["api_keys"].get(service)
                if not encrypted_key:
                    return None
                
                # Decrypt key
                key = self._fernet.decrypt(encrypted_key.encode())
                return key.decode()
            
        except Exception as e:
            logger.error(f"Error getting API key: {str(e)}")
            return None
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            str: Encrypted data
        """
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return encrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Data to decrypt
            
        Returns:
            str: Decrypted data
        """
        try:
            decrypted_data = self._fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            raise
    
    def generate_hash(self, data: str) -> str:
        """
        Generate hash of data.
        
        Args:
            data: Data to hash
            
        Returns:
            str: Hash
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_hash(self, data: str, hash_value: str) -> bool:
        """
        Verify hash of data.
        
        Args:
            data: Data to verify
            hash_value: Hash to verify against
            
        Returns:
            bool: True if hash matches, False otherwise
        """
        return self.generate_hash(data) == hash_value
    
    def generate_hmac(self, data: str, key: str) -> str:
        """
        Generate HMAC of data.
        
        Args:
            data: Data to hash
            key: Key to use
            
        Returns:
            str: HMAC
        """
        return hmac.new(
            key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_hmac(self, data: str, key: str, hmac_value: str) -> bool:
        """
        Verify HMAC of data.
        
        Args:
            data: Data to verify
            key: Key to use
            hmac_value: HMAC to verify against
            
        Returns:
            bool: True if HMAC matches, False otherwise
        """
        return self.generate_hmac(data, key) == hmac_value 