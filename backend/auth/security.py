"""Authentication and security utilities."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import os

from config.settings import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """Password hashing utilities."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """JWT token management."""

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Data to encode in token
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create refresh token."""
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return TokenManager.create_access_token(data, expires_delta)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and verify JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None


class EncryptionManager:
    """API key encryption/decryption."""

    def __init__(self):
        """Initialize encryption manager."""
        # In production, load from secure environment variable
        encryption_key = settings.ENCRYPTION_KEY

        # Ensure key is proper length (32 bytes for Fernet)
        if len(encryption_key) != 44:  # Base64 encoded 32 bytes = 44 chars
            # Generate a new key if not proper format
            encryption_key = Fernet.generate_key().decode()

        self.cipher = Fernet(encryption_key.encode())

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string.

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            Decrypted plaintext
        """
        encrypted = base64.b64decode(ciphertext.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()


# Global instances
password_hasher = PasswordHasher()
token_manager = TokenManager()
encryption_manager = EncryptionManager()
