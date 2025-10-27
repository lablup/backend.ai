"""Tests for JWT types."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ai.backend.common.jwt.types import JWTClaims, JWTUserContext
from ai.backend.common.types import AccessKey


def test_jwt_user_context_creation() -> None:
    """Test JWTUserContext dataclass creation."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")

    context = JWTUserContext(
        access_key=access_key,
        role="user",
    )

    assert context.access_key == access_key
    assert context.role == "user"


def test_jwt_user_context_immutable() -> None:
    """Test that JWTUserContext is immutable."""
    context = JWTUserContext(
        access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        role="user",
    )

    with pytest.raises(AttributeError):
        context.role = "admin"  # type: ignore


def test_jwt_claims_creation() -> None:
    """Test JWTClaims dataclass creation."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(timezone.utc)

    claims = JWTClaims(
        exp=now,
        iat=now,
        access_key=access_key,
        role="user",
    )

    assert claims.access_key == access_key
    assert claims.role == "user"


def test_jwt_claims_to_dict() -> None:
    """Test JWTClaims serialization to dictionary."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(timezone.utc)

    claims = JWTClaims(
        exp=now,
        iat=now,
        access_key=access_key,
        role="admin",
    )

    claims_dict = claims.to_dict()

    assert claims_dict["exp"] == int(now.timestamp())
    assert claims_dict["iat"] == int(now.timestamp())
    assert claims_dict["access_key"] == str(access_key)
    assert claims_dict["role"] == "admin"


def test_jwt_claims_from_dict() -> None:
    """Test JWTClaims deserialization from dictionary."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(timezone.utc)

    payload = {
        "exp": int(now.timestamp()),
        "iat": int(now.timestamp()),
        "access_key": str(access_key),
        "role": "superadmin",
    }

    claims = JWTClaims.from_dict(payload)

    assert claims.access_key == access_key
    assert claims.role == "superadmin"


def test_jwt_claims_roundtrip() -> None:
    """Test that JWTClaims can be serialized and deserialized correctly."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(timezone.utc)

    original_claims = JWTClaims(
        exp=now,
        iat=now,
        access_key=access_key,
        role="user",
    )

    # Serialize to dict and back
    claims_dict = original_claims.to_dict()
    restored_claims = JWTClaims.from_dict(claims_dict)

    # Compare all fields
    assert restored_claims.access_key == original_claims.access_key
    assert restored_claims.role == original_claims.role


def test_jwt_claims_from_dict_missing_field() -> None:
    """Test that JWTClaims.from_dict raises error when required field is missing."""
    payload = {
        "exp": int(datetime.now(timezone.utc).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        # Missing access_key, role
    }

    with pytest.raises(KeyError):
        JWTClaims.from_dict(payload)
