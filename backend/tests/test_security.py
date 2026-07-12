import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_password_hashing():
    """Verify password hashing and verification."""
    raw_password = "dummy_test_password"
    hashed = get_password_hash(raw_password)
    
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_generation_and_decoding():
    """Verify access and refresh token generation, contents, and decoding."""
    subject = "user@test.com"
    role = "fleet_manager"
    
    # 1. Access Token
    access_token = create_access_token(subject, role)
    decoded_access = decode_token(access_token)
    assert decoded_access["sub"] == subject
    assert decoded_access["role"] == role
    assert decoded_access["type"] == "access"
    assert "exp" in decoded_access
    
    # 2. Refresh Token
    refresh_token = create_refresh_token(subject)
    decoded_refresh = decode_token(refresh_token)
    assert decoded_refresh["sub"] == subject
    assert decoded_refresh["type"] == "refresh"
    assert "exp" in decoded_refresh


def test_jwt_expiration():
    """Verify that expired tokens raise JWTError when decoded."""
    subject = "expired@test.com"
    
    # Create an expired token manually using jose jwt
    expire = datetime.now(timezone.utc) - timedelta(minutes=10)
    to_encode = {
        "sub": subject,
        "type": "access",
        "exp": expire
    }
    expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    with pytest.raises(JWTError):
        decode_token(expired_token)


def test_jwt_invalid_signature():
    """Verify that tokens with altered signatures raise JWTError."""
    token = create_access_token("user@test.com", "driver")
    # Alter token signature by changing the last character
    invalid_token = token[:-1] + ("A" if token[-1] != "A" else "B")
    
    with pytest.raises(JWTError):
        decode_token(invalid_token)
