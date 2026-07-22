"""Security utilities: JWT, bcrypt password hashing, Fernet encryption."""

import hashlib
import base64
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def _derive_fernet_key(secret: str) -> bytes:
    """Derive a 32-byte Fernet key from the app secret using SHA-256."""
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())


def create_access_token(data: dict) -> str:
    """Create a JWT access token with 7-day expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises JWTError on failure."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise


def hash_password(password: str) -> str:
    """Hash a password using bcrypt. Returns a utf-8 decoded string."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def encrypt_api_key(key: str, secret: str) -> str:
    """Encrypt an API key using Fernet derived from the given secret."""
    fernet_key = _derive_fernet_key(secret)
    f = Fernet(fernet_key)
    return f.encrypt(key.encode()).decode()


def decrypt_api_key(encrypted: str, secret: str) -> str:
    """Decrypt a Fernet-encrypted API key."""
    fernet_key = _derive_fernet_key(secret)
    f = Fernet(fernet_key)
    return f.decrypt(encrypted.encode()).decode()
