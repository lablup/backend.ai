"""JWT token types and claims for GraphQL Federation authentication."""

from __future__ import annotations

import enum
import uuid
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final, Self, override

from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import AccessKey


class JWTPrincipalType(enum.StrEnum):
    """How a JWT names its caller."""

    USER = "user"
    ACCESS_KEY = "access_key"


@dataclass(frozen=True)
class JWTPrincipal(ABC):
    """Who a JWT authenticates and by which identifier."""

    @classmethod
    @abstractmethod
    def principal_type(cls) -> JWTPrincipalType:
        """The discriminant this principal serializes under."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_claims(cls, payload: Mapping[str, Any]) -> Self:
        """Build the principal from its claims in a JWT payload."""
        raise NotImplementedError

    @abstractmethod
    def to_claims(self) -> dict[str, Any]:
        """The principal's claims to embed in the JWT payload."""
        raise NotImplementedError


@dataclass(frozen=True)
class UserPrincipal(JWTPrincipal):
    """The token names the caller by user UUID."""

    user_id: UserID

    @override
    @classmethod
    def principal_type(cls) -> JWTPrincipalType:
        return JWTPrincipalType.USER

    @override
    @classmethod
    def from_claims(cls, payload: Mapping[str, Any]) -> Self:
        return cls(user_id=UserID(uuid.UUID(payload["user_id"])))

    @override
    def to_claims(self) -> dict[str, Any]:
        return {
            "principal_type": self.principal_type().value,
            "user_id": str(self.user_id),
        }


@dataclass(frozen=True)
class AccessKeyPrincipal(JWTPrincipal):
    """The token names the caller by access key."""

    access_key: AccessKey

    @override
    @classmethod
    def principal_type(cls) -> JWTPrincipalType:
        return JWTPrincipalType.ACCESS_KEY

    @override
    @classmethod
    def from_claims(cls, payload: Mapping[str, Any]) -> Self:
        return cls(access_key=AccessKey(payload["access_key"]))

    @override
    def to_claims(self) -> dict[str, Any]:
        return {
            "principal_type": self.principal_type().value,
            "access_key": str(self.access_key),
        }


_PRINCIPAL_CLASSES: Final[Mapping[JWTPrincipalType, type[JWTPrincipal]]] = {
    cls.principal_type(): cls for cls in (UserPrincipal, AccessKeyPrincipal)
}


def parse_jwt_principal(payload: Mapping[str, Any]) -> JWTPrincipal:
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
    return _PRINCIPAL_CLASSES[principal_type].from_claims(payload)


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
