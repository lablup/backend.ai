"""Tests for JWT validator."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

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
        secret_key="test-secret-key-at-least-32-bytes-long",
        algorithm="HS256",
        token_expiration_seconds=900,
        issuer="backend.ai-webserver",
    )


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
        user_id=uuid4(),
        access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        role="user",
        domain_name="default",
        is_admin=False,
        is_superadmin=False,
    )


def test_validate_token_with_valid_token(
    jwt_signer: JWTSigner,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
) -> None:
    """Test that validator accepts valid tokens."""
    token = jwt_signer.generate_token(user_context)
    claims = jwt_validator.validate_token(token)

    assert claims.sub == user_context.user_id
    assert claims.access_key == user_context.access_key
    assert claims.role == user_context.role
    assert claims.domain_name == user_context.domain_name
    assert claims.is_admin == user_context.is_admin
    assert claims.is_superadmin == user_context.is_superadmin


def test_validate_token_with_expired_token(
    jwt_config: JWTConfig,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
) -> None:
    """Test that validator rejects expired tokens."""
    # Create token that expired 1 hour ago
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)

    payload = {
        "sub": str(user_context.user_id),
        "exp": int((past_time + timedelta(seconds=900)).timestamp()),
        "iat": int(past_time.timestamp()),
        "iss": jwt_config.issuer,
        "access_key": str(user_context.access_key),
        "role": user_context.role,
        "domain_name": user_context.domain_name,
        "is_admin": user_context.is_admin,
        "is_superadmin": user_context.is_superadmin,
    }

    expired_token = pyjwt.encode(
        payload,
        jwt_config.secret_key,
        algorithm=jwt_config.algorithm,
    )

    with pytest.raises(JWTExpiredError):
        jwt_validator.validate_token(expired_token)


def test_validate_token_with_invalid_signature(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    user_context: JWTUserContext,
) -> None:
    """Test that validator rejects tokens with invalid signature."""
    token = jwt_signer.generate_token(user_context)

    # Create validator with different secret
    wrong_config = JWTConfig(
        secret_key="wrong-secret-key-different-from-original",
        algorithm="HS256",
        token_expiration_seconds=900,
        issuer="backend.ai-webserver",
    )
    wrong_validator = JWTValidator(wrong_config)

    with pytest.raises(JWTInvalidSignatureError):
        wrong_validator.validate_token(token)


def test_validate_token_with_malformed_token(
    jwt_validator: JWTValidator,
) -> None:
    """Test that validator rejects malformed tokens."""
    malformed_token = "not.a.valid.jwt.token"

    with pytest.raises(JWTDecodeError):
        jwt_validator.validate_token(malformed_token)


def test_validate_token_with_missing_claims(
    jwt_config: JWTConfig,
    jwt_validator: JWTValidator,
) -> None:
    """Test that validator rejects tokens with missing required claims."""
    # Create token with missing claims
    payload = {
        "sub": str(uuid4()),
        "exp": int((datetime.now(timezone.utc) + timedelta(seconds=900)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": jwt_config.issuer,
        # Missing: access_key, role, domain_name, is_admin, is_superadmin
    }

    incomplete_token = pyjwt.encode(
        payload,
        jwt_config.secret_key,
        algorithm=jwt_config.algorithm,
    )

    with pytest.raises(JWTInvalidClaimsError):
        jwt_validator.validate_token(incomplete_token)


def test_validate_token_with_invalid_role(
    jwt_config: JWTConfig,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
) -> None:
    """Test that validator rejects tokens with invalid role."""
    payload = {
        "sub": str(user_context.user_id),
        "exp": int((datetime.now(timezone.utc) + timedelta(seconds=900)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": jwt_config.issuer,
        "access_key": str(user_context.access_key),
        "role": "invalid_role",  # Not in valid_roles
        "domain_name": user_context.domain_name,
        "is_admin": user_context.is_admin,
        "is_superadmin": user_context.is_superadmin,
    }

    invalid_token = pyjwt.encode(
        payload,
        jwt_config.secret_key,
        algorithm=jwt_config.algorithm,
    )

    with pytest.raises(JWTInvalidClaimsError) as exc_info:
        jwt_validator.validate_token(invalid_token)

    assert "Invalid role" in str(exc_info.value)


def test_validate_token_with_wrong_issuer(
    jwt_config: JWTConfig,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
) -> None:
    """Test that validator rejects tokens with wrong issuer."""
    payload = {
        "sub": str(user_context.user_id),
        "exp": int((datetime.now(timezone.utc) + timedelta(seconds=900)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": "wrong-issuer",  # Different from expected issuer
        "access_key": str(user_context.access_key),
        "role": user_context.role,
        "domain_name": user_context.domain_name,
        "is_admin": user_context.is_admin,
        "is_superadmin": user_context.is_superadmin,
    }

    wrong_issuer_token = pyjwt.encode(
        payload,
        jwt_config.secret_key,
        algorithm=jwt_config.algorithm,
    )

    with pytest.raises(JWTInvalidClaimsError) as exc_info:
        jwt_validator.validate_token(wrong_issuer_token)

    assert "Invalid issuer" in str(exc_info.value)


def test_validate_token_with_admin_role(
    jwt_signer: JWTSigner,
    jwt_validator: JWTValidator,
) -> None:
    """Test validation of token with admin role."""
    admin_context = JWTUserContext(
        user_id=uuid4(),
        access_key=AccessKey("AKIAADMIN123456789"),
        role="admin",
        domain_name="admin-domain",
        is_admin=True,
        is_superadmin=False,
    )

    token = jwt_signer.generate_token(admin_context)
    claims = jwt_validator.validate_token(token)

    assert claims.role == "admin"
    assert claims.is_admin is True
    assert claims.is_superadmin is False


def test_validate_token_with_superadmin_role(
    jwt_signer: JWTSigner,
    jwt_validator: JWTValidator,
) -> None:
    """Test validation of token with superadmin role."""
    superadmin_context = JWTUserContext(
        user_id=uuid4(),
        access_key=AccessKey("AKIASUPERADMIN123456"),
        role="superadmin",
        domain_name="super-domain",
        is_admin=True,
        is_superadmin=True,
    )

    token = jwt_signer.generate_token(superadmin_context)
    claims = jwt_validator.validate_token(token)

    assert claims.role == "superadmin"
    assert claims.is_admin is True
    assert claims.is_superadmin is True


def test_validate_token_roundtrip(
    jwt_signer: JWTSigner,
    jwt_validator: JWTValidator,
    user_context: JWTUserContext,
) -> None:
    """Test complete roundtrip: sign -> validate -> verify data."""
    # Generate token
    token = jwt_signer.generate_token(user_context)

    # Validate token
    claims = jwt_validator.validate_token(token)

    # Verify all data matches
    assert claims.sub == user_context.user_id
    assert claims.access_key == user_context.access_key
    assert claims.role == user_context.role
    assert claims.domain_name == user_context.domain_name
    assert claims.is_admin == user_context.is_admin
    assert claims.is_superadmin == user_context.is_superadmin


def test_validate_token_with_invalid_uuid_in_sub(
    jwt_config: JWTConfig,
    jwt_validator: JWTValidator,
) -> None:
    """Test that validator rejects tokens with invalid UUID in sub claim."""
    payload = {
        "sub": "not-a-valid-uuid",
        "exp": int((datetime.now(timezone.utc) + timedelta(seconds=900)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": jwt_config.issuer,
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "role": "user",
        "domain_name": "default",
        "is_admin": False,
        "is_superadmin": False,
    }

    invalid_token = pyjwt.encode(
        payload,
        jwt_config.secret_key,
        algorithm=jwt_config.algorithm,
    )

    with pytest.raises(JWTInvalidClaimsError):
        jwt_validator.validate_token(invalid_token)
