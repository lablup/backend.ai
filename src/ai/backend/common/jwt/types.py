"""JWT token types and claims for GraphQL Federation authentication."""

from __future__ import annotations

import enum
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import AccessKey


class JWTPrincipalType(enum.StrEnum):
    """How a JWT names its caller."""

    USER = "user"
    ACCESS_KEY = "access_key"


@dataclass(frozen=True)
class JWTPrincipal(ABC):
    """Who a JWT authenticates and by which identifier."""

    @abstractmethod
    def to_claims(self) -> dict[str, Any]:
        """The principal's claims to embed in the JWT payload."""
        raise NotImplementedError


@dataclass(frozen=True)
class UserPrincipal(JWTPrincipal):
    """The token names the caller by user UUID."""

    user_id: UserID

    @override
    def to_claims(self) -> dict[str, Any]:
        return {
            "principal_type": JWTPrincipalType.USER.value,
            "user_id": str(self.user_id),
        }


@dataclass(frozen=True)
class AccessKeyPrincipal(JWTPrincipal):
    """The token names the caller by access key."""

    access_key: AccessKey

    @override
    def to_claims(self) -> dict[str, Any]:
        return {
            "principal_type": JWTPrincipalType.ACCESS_KEY.value,
            "access_key": str(self.access_key),
        }


def parse_jwt_principal(payload: dict[str, Any]) -> JWTPrincipal:
    """Read the principal claims out of a JWT payload.

    Tokens issued before the ``principal_type`` claim existed carry only an
    access key and are read as ``AccessKeyPrincipal``.

    Raises ``KeyError`` / ``ValueError`` on missing or malformed claims.
    """
    raw_type = payload.get("principal_type")
    if raw_type is None:
        principal_type = JWTPrincipalType.ACCESS_KEY
    else:
        principal_type = JWTPrincipalType(raw_type)
    match principal_type:
        case JWTPrincipalType.USER:
            return UserPrincipal(user_id=UserID(uuid.UUID(payload["user_id"])))
        case JWTPrincipalType.ACCESS_KEY:
            return AccessKeyPrincipal(access_key=AccessKey(payload["access_key"]))


@dataclass(frozen=True)
class JWTUserContext:
    """
    User context data for JWT token generation.

    This dataclass encapsulates minimal user information needed to generate
    a JWT token. Additional user information (domain_name, is_admin, is_superadmin)
    should be retrieved from the user table during authentication.

    Attributes:
        principal: Who the token authenticates and by which identifier.
        role: User's role ("admin", "user", or "superadmin")
    """

    principal: JWTPrincipal
    role: str


@dataclass(frozen=True)
class JWTClaims:
    """
    JWT token payload for GraphQL Federation authentication.

    This dataclass represents the claims contained in a JWT token used for
    authenticating GraphQL requests through Hive Router.

    Contains minimal user information. Additional user information (domain_name,
    is_admin, is_superadmin) should be retrieved from the user table during authentication.

    Attributes:
        exp: Expiration time (UTC)
        iat: Issued at time (UTC)
        role: User role ("admin", "user", or "superadmin")
        principal: Who the token authenticates and by which identifier.
    """

    # Standard JWT claims (RFC 7519)
    exp: datetime
    iat: datetime

    # Backend.AI specific claims
    role: str
    principal: JWTPrincipal

    def to_dict(self) -> dict[str, Any]:
        """
        Convert JWTClaims to a dictionary suitable for JWT payload.

        Datetime objects are converted to Unix timestamps (integers) as required
        by the JWT standard.

        Returns:
            Dictionary representation of claims with timestamps as integers.
        """
        payload: dict[str, Any] = {
            "exp": int(self.exp.timestamp()),
            "iat": int(self.iat.timestamp()),
            "role": self.role,
        }
        payload.update(self.principal.to_claims())
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> JWTClaims:
        """
        Parse JWT payload dictionary to JWTClaims.

        Converts Unix timestamps back to datetime objects and validates
        the structure of the payload.

        Args:
            payload: Dictionary containing JWT claims

        Returns:
            JWTClaims instance

        Raises:
            KeyError: If required claims are missing
            ValueError: If claim values are invalid
        """
        return cls(
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
            role=payload["role"],
            principal=parse_jwt_principal(payload),
        )
