"""Tests for JWT types."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ai.backend.common.jwt.types import JWTClaims, JWTUserContext
from ai.backend.common.types import AccessKey


def test_jwt_user_context_creation() -> None:
    """Test JWTUserContext dataclass creation."""
    user_id = uuid4()
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")

    context = JWTUserContext(
        user_id=user_id,
        access_key=access_key,
        role="user",
        domain_name="default",
        is_admin=False,
        is_superadmin=False,
    )

    assert context.user_id == user_id
    assert context.access_key == access_key
    assert context.role == "user"
    assert context.domain_name == "default"
    assert context.is_admin is False
    assert context.is_superadmin is False


def test_jwt_user_context_immutable() -> None:
    """Test that JWTUserContext is immutable."""
    context = JWTUserContext(
        user_id=uuid4(),
        access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        role="user",
        domain_name="default",
        is_admin=False,
        is_superadmin=False,
    )

    with pytest.raises(AttributeError):
        context.role = "admin"  # type: ignore


def test_jwt_claims_creation() -> None:
    """Test JWTClaims dataclass creation."""
    user_id = uuid4()
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(timezone.utc)

    claims = JWTClaims(
        sub=user_id,
        exp=now,
        iat=now,
        iss="backend.ai-webserver",
        access_key=access_key,
        role="user",
        domain_name="default",
        is_admin=False,
        is_superadmin=False,
    )

    assert claims.sub == user_id
    assert claims.access_key == access_key
    assert claims.role == "user"
    assert claims.iss == "backend.ai-webserver"


def test_jwt_claims_to_dict() -> None:
    """Test JWTClaims serialization to dictionary."""
    user_id = uuid4()
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(timezone.utc)

    claims = JWTClaims(
        sub=user_id,
        exp=now,
        iat=now,
        iss="backend.ai-webserver",
        access_key=access_key,
        role="admin",
        domain_name="test-domain",
        is_admin=True,
        is_superadmin=False,
    )

    claims_dict = claims.to_dict()

    assert claims_dict["sub"] == str(user_id)
    assert claims_dict["exp"] == int(now.timestamp())
    assert claims_dict["iat"] == int(now.timestamp())
    assert claims_dict["iss"] == "backend.ai-webserver"
    assert claims_dict["access_key"] == str(access_key)
    assert claims_dict["role"] == "admin"
    assert claims_dict["domain_name"] == "test-domain"
    assert claims_dict["is_admin"] is True
    assert claims_dict["is_superadmin"] is False


def test_jwt_claims_from_dict() -> None:
    """Test JWTClaims deserialization from dictionary."""
    user_id = uuid4()
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "exp": int(now.timestamp()),
        "iat": int(now.timestamp()),
        "iss": "backend.ai-webserver",
        "access_key": str(access_key),
        "role": "superadmin",
        "domain_name": "prod-domain",
        "is_admin": True,
        "is_superadmin": True,
    }

    claims = JWTClaims.from_dict(payload)

    assert claims.sub == user_id
    assert claims.access_key == access_key
    assert claims.role == "superadmin"
    assert claims.domain_name == "prod-domain"
    assert claims.is_admin is True
    assert claims.is_superadmin is True
    assert claims.iss == "backend.ai-webserver"


def test_jwt_claims_roundtrip() -> None:
    """Test that JWTClaims can be serialized and deserialized correctly."""
    user_id = uuid4()
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(timezone.utc)

    original_claims = JWTClaims(
        sub=user_id,
        exp=now,
        iat=now,
        iss="backend.ai-webserver",
        access_key=access_key,
        role="user",
        domain_name="default",
        is_admin=False,
        is_superadmin=False,
    )

    # Serialize to dict and back
    claims_dict = original_claims.to_dict()
    restored_claims = JWTClaims.from_dict(claims_dict)

    # Compare all fields
    assert restored_claims.sub == original_claims.sub
    assert restored_claims.access_key == original_claims.access_key
    assert restored_claims.role == original_claims.role
    assert restored_claims.domain_name == original_claims.domain_name
    assert restored_claims.is_admin == original_claims.is_admin
    assert restored_claims.is_superadmin == original_claims.is_superadmin
    assert restored_claims.iss == original_claims.iss


def test_jwt_claims_from_dict_missing_field() -> None:
    """Test that JWTClaims.from_dict raises error when required field is missing."""
    payload = {
        "sub": str(uuid4()),
        "exp": int(datetime.now(timezone.utc).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": "backend.ai-webserver",
        # Missing access_key, role, domain_name, etc.
    }

    with pytest.raises(KeyError):
        JWTClaims.from_dict(payload)


def test_jwt_claims_from_dict_invalid_uuid() -> None:
    """Test that JWTClaims.from_dict raises error for invalid UUID."""
    now = datetime.now(timezone.utc)

    payload = {
        "sub": "invalid-uuid",
        "exp": int(now.timestamp()),
        "iat": int(now.timestamp()),
        "iss": "backend.ai-webserver",
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "role": "user",
        "domain_name": "default",
        "is_admin": False,
        "is_superadmin": False,
    }

    with pytest.raises(ValueError):
        JWTClaims.from_dict(payload)
