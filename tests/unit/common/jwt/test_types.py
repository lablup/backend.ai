"""Tests for JWT types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from ai.backend.common.identifier.user import UserID
from ai.backend.common.jwt.types import (
    AccessKeyPrincipal,
    JWTClaims,
    JWTUserContext,
    UserPrincipal,
    parse_jwt_principal,
)
from ai.backend.common.types import AccessKey


def test_jwt_user_context_creation() -> None:
    """Test JWTUserContext dataclass creation."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")

    context = JWTUserContext(
        principal=AccessKeyPrincipal(access_key=access_key),
        role="user",
    )

    assert context.principal == AccessKeyPrincipal(access_key=access_key)
    assert context.role == "user"


def test_jwt_user_context_immutable() -> None:
    """Test that JWTUserContext is immutable."""
    context = JWTUserContext(
        principal=AccessKeyPrincipal(access_key=AccessKey("AKIAIOSFODNN7EXAMPLE")),
        role="user",
    )

    with pytest.raises(AttributeError):
        context.role = "admin"  # type: ignore


def test_jwt_claims_creation() -> None:
    """Test JWTClaims dataclass creation."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(UTC)

    claims = JWTClaims(
        exp=now,
        iat=now,
        role="user",
        principal=AccessKeyPrincipal(access_key=access_key),
    )

    assert claims.principal == AccessKeyPrincipal(access_key=access_key)
    assert claims.role == "user"


def test_jwt_claims_to_dict_access_key_principal() -> None:
    """Test JWTClaims serialization for an access-key principal."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(UTC)

    claims = JWTClaims(
        exp=now,
        iat=now,
        role="admin",
        principal=AccessKeyPrincipal(access_key=access_key),
    )

    claims_dict = claims.to_dict()

    assert claims_dict["exp"] == int(now.timestamp())
    assert claims_dict["iat"] == int(now.timestamp())
    assert claims_dict["principal_type"] == "access_key"
    assert claims_dict["access_key"] == str(access_key)
    assert claims_dict["role"] == "admin"


def test_jwt_claims_to_dict_user_principal() -> None:
    """Test JWTClaims serialization for a user principal."""
    user_id = UserID(uuid.uuid4())
    now = datetime.now(UTC)

    claims = JWTClaims(
        exp=now,
        iat=now,
        role="user",
        principal=UserPrincipal(user_id=user_id),
    )

    claims_dict = claims.to_dict()

    assert claims_dict["principal_type"] == "user"
    assert claims_dict["user_id"] == str(user_id)
    assert "access_key" not in claims_dict


def test_jwt_claims_from_dict() -> None:
    """Test JWTClaims deserialization from dictionary."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    now = datetime.now(UTC)

    payload = {
        "exp": int(now.timestamp()),
        "iat": int(now.timestamp()),
        "principal_type": "access_key",
        "access_key": str(access_key),
        "role": "superadmin",
    }

    claims = JWTClaims.from_dict(payload)

    assert claims.principal == AccessKeyPrincipal(access_key=access_key)
    assert claims.role == "superadmin"


def test_jwt_claims_roundtrip() -> None:
    """Test that JWTClaims can be serialized and deserialized correctly."""
    user_id = UserID(uuid.uuid4())
    now = datetime.now(UTC)

    original_claims = JWTClaims(
        exp=now,
        iat=now,
        role="user",
        principal=UserPrincipal(user_id=user_id),
    )

    # Serialize to dict and back
    claims_dict = original_claims.to_dict()
    restored_claims = JWTClaims.from_dict(claims_dict)

    # Compare all fields
    assert restored_claims.principal == original_claims.principal
    assert restored_claims.role == original_claims.role


def test_parse_jwt_principal_without_type_reads_access_key() -> None:
    """Tokens issued before the principal_type claim carry only an access key."""
    access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")

    principal = parse_jwt_principal({"access_key": str(access_key)})

    assert principal == AccessKeyPrincipal(access_key=access_key)


def test_parse_jwt_principal_unknown_type_raises() -> None:
    with pytest.raises(ValueError):
        parse_jwt_principal({"principal_type": "banana"})


def test_jwt_claims_from_dict_missing_field() -> None:
    """Test that JWTClaims.from_dict raises error when required field is missing."""
    payload = {
        "exp": int(datetime.now(UTC).timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
        # Missing principal claims, role
    }

    with pytest.raises(KeyError):
        JWTClaims.from_dict(payload)
