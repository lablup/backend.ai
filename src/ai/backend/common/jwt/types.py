"""JWT token types and claims for GraphQL Federation authentication."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import AccessKey


@dataclass(frozen=True)
class JWTUserContext:
    """
    User context data for JWT token generation.

    This dataclass encapsulates minimal user information needed to generate
    a JWT token. Additional user information (domain_name, is_admin, is_superadmin)
    should be retrieved from the user table during authentication.

    Attributes:
        access_key: User's access key
        role: User's role ("admin", "user", or "superadmin")
        user_id: UUID of the user the token authenticates, when known.
            Sessions created before the field existed cannot provide it.
    """

    access_key: AccessKey
    role: str
    user_id: UserID | None = None


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
        access_key: User's access key
        role: User role ("admin", "user", or "superadmin")
        user_id: UUID of the user the token authenticates; absent in tokens
            issued from sessions that predate the claim.
    """

    # Standard JWT claims (RFC 7519)
    exp: datetime
    iat: datetime

    # Backend.AI specific claims
    access_key: AccessKey
    role: str
    user_id: UserID | None = None

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
            "access_key": str(self.access_key),
            "role": self.role,
        }
        if self.user_id is not None:
            payload["user_id"] = str(self.user_id)
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
        raw_user_id = payload.get("user_id")
        return cls(
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
            access_key=AccessKey(payload["access_key"]),
            role=payload["role"],
            user_id=UserID(uuid.UUID(raw_user_id)) if raw_user_id is not None else None,
        )
