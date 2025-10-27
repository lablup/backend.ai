"""Tests for JWT signer."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest

from ai.backend.common.jwt.config import JWTConfig
from ai.backend.common.jwt.signer import JWTSigner
from ai.backend.common.jwt.types import JWTUserContext
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
def user_context() -> JWTUserContext:
    """Create test user context."""
    return JWTUserContext(
        access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        role="user",
    )


def test_generate_token_creates_valid_jwt(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that generate_token creates a valid JWT token."""
    token = jwt_signer.generate_token(user_context, test_secret_key)

    # Verify token is a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode without verification to check structure
    decoded = pyjwt.decode(
        token,
        options={"verify_signature": False},
    )

    # Verify claims are present
    assert "exp" in decoded
    assert "iat" in decoded
    assert "access_key" in decoded
    assert "role" in decoded


def test_generate_token_includes_user_data(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that generated token includes all user context data."""
    token = jwt_signer.generate_token(user_context, test_secret_key)

    decoded = pyjwt.decode(
        token,
        test_secret_key,
        algorithms=[jwt_config.algorithm],
    )

    assert decoded["access_key"] == str(user_context.access_key)
    assert decoded["role"] == user_context.role


def test_generate_token_sets_expiration(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that generated token has correct expiration time."""
    before_generation = datetime.now(timezone.utc)
    token = jwt_signer.generate_token(user_context, test_secret_key)
    after_generation = datetime.now(timezone.utc)

    decoded = pyjwt.decode(
        token,
        test_secret_key,
        algorithms=[jwt_config.algorithm],
    )

    exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    expected_min = before_generation + jwt_config.token_expiration - timedelta(seconds=2)
    expected_max = after_generation + jwt_config.token_expiration + timedelta(seconds=2)

    # Expiration should be close to configured time (with 2 second margin due to timestamp precision)
    assert expected_min <= exp_time <= expected_max


def test_generate_token_sets_issued_at(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that generated token has correct issued-at time."""
    before_generation = datetime.now(timezone.utc)
    token = jwt_signer.generate_token(user_context, test_secret_key)
    after_generation = datetime.now(timezone.utc)

    decoded = pyjwt.decode(
        token,
        test_secret_key,
        algorithms=[jwt_config.algorithm],
    )

    iat_time = datetime.fromtimestamp(decoded["iat"], tz=timezone.utc)

    # Add tolerance for timestamp precision (JWT uses seconds, not microseconds)
    before_with_margin = before_generation - timedelta(seconds=1)
    after_with_margin = after_generation + timedelta(seconds=1)

    # Issued-at should be within test execution time (with 1 second margin)
    assert before_with_margin <= iat_time <= after_with_margin


def test_generate_token_with_admin_user(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    test_secret_key: str,
) -> None:
    """Test token generation for admin user."""
    admin_context = JWTUserContext(
        access_key=AccessKey("AKIAADMIN123456789"),
        role="admin",
    )

    token = jwt_signer.generate_token(admin_context, test_secret_key)

    decoded = pyjwt.decode(
        token,
        test_secret_key,
        algorithms=[jwt_config.algorithm],
    )

    assert decoded["role"] == "admin"


def test_generate_token_with_superadmin_user(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    test_secret_key: str,
) -> None:
    """Test token generation for superadmin user."""
    superadmin_context = JWTUserContext(
        access_key=AccessKey("AKIASUPERADMIN123456"),
        role="superadmin",
    )

    token = jwt_signer.generate_token(superadmin_context, test_secret_key)

    decoded = pyjwt.decode(
        token,
        test_secret_key,
        algorithms=[jwt_config.algorithm],
    )

    assert decoded["role"] == "superadmin"


def test_generate_token_signature_verification(
    jwt_signer: JWTSigner,
    jwt_config: JWTConfig,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that generated token can be verified with correct secret."""
    token = jwt_signer.generate_token(user_context, test_secret_key)

    # Should not raise exception
    pyjwt.decode(
        token,
        test_secret_key,
        algorithms=[jwt_config.algorithm],
    )


def test_generate_token_wrong_secret_fails_verification(
    jwt_signer: JWTSigner,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that token fails verification with wrong secret."""
    token = jwt_signer.generate_token(user_context, test_secret_key)

    with pytest.raises(pyjwt.InvalidSignatureError):
        pyjwt.decode(
            token,
            "wrong-secret-key",
            algorithms=["HS256"],
        )


def test_multiple_tokens_are_different(
    jwt_signer: JWTSigner,
    user_context: JWTUserContext,
    test_secret_key: str,
) -> None:
    """Test that generating multiple tokens produces different tokens."""
    token1 = jwt_signer.generate_token(user_context, test_secret_key)
    # Sleep to ensure different timestamps (JWT uses second precision)
    time.sleep(1.1)
    token2 = jwt_signer.generate_token(user_context, test_secret_key)

    # Tokens should be different due to different iat/exp timestamps
    assert token1 != token2
