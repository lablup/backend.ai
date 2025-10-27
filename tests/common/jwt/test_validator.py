"""Tests for JWT validator."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest

from ai.backend.common.jwt.config import JWTConfig
from ai.backend.common.jwt.exceptions import (
    JWTDecodeError,
    JWTExpiredError,
    JWTInvalidClaimsError,
    JWTInvalidSignatureError,
)
from ai.backend.common.jwt.signer import JWTSigner
from ai.backend.common.jwt.types import JWTUserContext
from ai.backend.common.jwt.validator import JWTValidator
from ai.backend.common.types import AccessKey


@pytest.fixture
def jwt_config() -> JWTConfig:
    """Create test JWT configuration."""
    return JWTConfig(
        algorithm="HS256",
        token_expiration_seconds=900,
    )


@pytest.fixture
def test_secret_key() -> str:
    """Create test secret key."""
    return "test-secret-key-at-least-32-bytes-long"


@pytest.fixture
def jwt_signer(jwt_config: JWTConfig) -> JWTSigner:
    """Create JWT signer instance."""
    return JWTSigner(jwt_config)


@pytest.fixture
def jwt_validator(jwt_config: JWTConfig) -> JWTValidator:
    """Create JWT validator instance."""
    return JWTValidator(jwt_config)


@pytest.fixture
def user_context() -> JWTUserContext:
    """Create test user context."""
    return JWTUserContext(
        access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        role="user",
    )


def test_validate_token_with_valid_token(
    jwt_signer: JWTSigner,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that validator accepts valid tokens."""
    token = jwt_signer.generate_token(user_context, test_secret_key)
    claims = jwt_validator.validate_token(token, test_secret_key)

    assert claims.access_key == user_context.access_key
    assert claims.role == user_context.role


def test_validate_token_with_expired_token(
    jwt_config: JWTConfig,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that validator rejects expired tokens."""
    # Create token that expired 1 hour ago
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)

    payload = {
        "exp": int((past_time + timedelta(seconds=900)).timestamp()),
        "iat": int(past_time.timestamp()),
        "access_key": str(user_context.access_key),
        "role": user_context.role,
    }

    expired_token = pyjwt.encode(
        payload,
        test_secret_key,
        algorithm=jwt_config.algorithm,
    )

    with pytest.raises(JWTExpiredError):
        jwt_validator.validate_token(expired_token, test_secret_key)


def test_validate_token_with_invalid_signature(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that validator rejects tokens with invalid signature."""
    token = jwt_signer.generate_token(user_context, test_secret_key)

    # Create validator with configuration
    validator = JWTValidator(jwt_config)

    # Try to validate with wrong secret
    wrong_secret = "wrong-secret-key-different-from-original"
    with pytest.raises(JWTInvalidSignatureError):
        validator.validate_token(token, wrong_secret)


def test_validate_token_with_malformed_token(
    jwt_validator: JWTValidator,
    test_secret_key: str,
) -> None:
    """Test that validator rejects malformed tokens."""
    malformed_token = "not.a.valid.jwt.token"

    with pytest.raises(JWTDecodeError):
        jwt_validator.validate_token(malformed_token, test_secret_key)


def test_validate_token_with_missing_claims(
    jwt_config: JWTConfig,
    jwt_validator: JWTValidator,
    test_secret_key: str,
) -> None:
    """Test that validator rejects tokens with missing required claims."""
    # Create token with missing claims
    payload = {
        "exp": int((datetime.now(timezone.utc) + timedelta(seconds=900)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        # Missing: access_key, role
    }

    incomplete_token = pyjwt.encode(
        payload,
        test_secret_key,
        algorithm=jwt_config.algorithm,
    )

    with pytest.raises(JWTInvalidClaimsError):
        jwt_validator.validate_token(incomplete_token, test_secret_key)


def test_validate_token_with_invalid_role(
    jwt_config: JWTConfig,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that validator rejects tokens with invalid role."""
    payload = {
        "exp": int((datetime.now(timezone.utc) + timedelta(seconds=900)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "access_key": str(user_context.access_key),
        "role": "invalid_role",  # Not in valid_roles
    }

    invalid_token = pyjwt.encode(
        payload,
        test_secret_key,
        algorithm=jwt_config.algorithm,
    )

    with pytest.raises(JWTInvalidClaimsError) as exc_info:
        jwt_validator.validate_token(invalid_token, test_secret_key)

    assert "Invalid role" in str(exc_info.value)


def test_validate_token_with_admin_role(
    jwt_signer: JWTSigner,
    jwt_validator: JWTValidator,
    test_secret_key: str,
) -> None:
    """Test validation of token with admin role."""
    admin_context = JWTUserContext(
        access_key=AccessKey("AKIAADMIN123456789"),
        role="admin",
    )

    token = jwt_signer.generate_token(admin_context, test_secret_key)
    claims = jwt_validator.validate_token(token, test_secret_key)

    assert claims.role == "admin"


def test_validate_token_with_superadmin_role(
    jwt_signer: JWTSigner,
    jwt_validator: JWTValidator,
    test_secret_key: str,
) -> None:
    """Test validation of token with superadmin role."""
    superadmin_context = JWTUserContext(
        access_key=AccessKey("AKIASUPERADMIN123456"),
        role="superadmin",
    )

    token = jwt_signer.generate_token(superadmin_context, test_secret_key)
    claims = jwt_validator.validate_token(token, test_secret_key)

    assert claims.role == "superadmin"


def test_validate_token_roundtrip(
    jwt_signer: JWTSigner,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test complete roundtrip: sign -> validate -> verify data."""
    # Generate token
    token = jwt_signer.generate_token(user_context, test_secret_key)

    # Validate token
    claims = jwt_validator.validate_token(token, test_secret_key)

    # Verify all data matches
    assert claims.access_key == user_context.access_key
    assert claims.role == user_context.role
