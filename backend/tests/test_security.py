"""Tests for security module — JWT, bcrypt, Fernet."""

import time

import pytest
from jose import jwt as jose_jwt, JWTError

from app.core.config import settings
from app.core.security import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    encrypt_api_key,
    decrypt_api_key,
)


class TestJWT:
    def test_create_and_verify_token(self):
        """RED: Create a JWT, verify it returns the original data."""
        data = {"sub": "user@test.com", "role": "user"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["sub"] == "user@test.com"
        assert payload["role"] == "user"

    def test_token_contains_expiry(self):
        """TRIANGULATE: Token must include an exp claim."""
        token = create_access_token({"sub": "test@test.com"})
        payload = verify_token(token)
        assert "exp" in payload

    def test_expired_token_raises(self):
        """TRIANGULATE: Expired token raises JWTError."""
        # Create a token that expired 1 hour ago, signed with the same key
        expired_payload = {
            "sub": "test@test.com",
            "exp": int(time.time()) - 3600,
        }
        token = jose_jwt.encode(
            expired_payload, settings.secret_key, algorithm="HS256"
        )

        with pytest.raises(JWTError):
            verify_token(token)

    def test_invalid_token_raises(self):
        """TRIANGULATE: Malformed token raises JWTError."""
        with pytest.raises(JWTError):
            verify_token("not.a.valid.token")


class TestPassword:
    def test_hash_and_verify_password(self):
        """RED: Hash a password and verify it matches."""
        hashed = hash_password("securePass123!")
        assert verify_password("securePass123!", hashed)
        assert not verify_password("wrongPassword", hashed)

    def test_hash_is_unique(self):
        """TRIANGULATE: Same password produces different hashes."""
        h1 = hash_password("MiClaveSegura")
        h2 = hash_password("MiClaveSegura")
        assert h1 != h2


class TestFernet:
    def test_encrypt_and_decrypt_api_key(self):
        """RED: Encrypt and decrypt an API key with the same secret."""
        key = "sk-test-key-12345"
        secret = "super-secret-key"
        encrypted = encrypt_api_key(key, secret)
        assert encrypted != key
        decrypted = decrypt_api_key(encrypted, secret)
        assert decrypted == key

    def test_different_secret_fails(self):
        """TRIANGULATE: Wrong secret cannot decrypt."""
        key = "sk-another-test-key"
        encrypted = encrypt_api_key(key, "secret-one")
        with pytest.raises(Exception):
            decrypt_api_key(encrypted, "wrong-secret")
