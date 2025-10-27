"""JWT token types and claims for GraphQL Federation authentication."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ai.backend.common.types import AccessKey


@dataclass(frozen=True)
class JWTUserContext:
    """
    User context data for JWT token generation.

    This dataclass encapsulates minimal user information needed to generate
    a JWT token. Additional user information (user_id, domain_name, is_admin, is_superadmin)
    should be retrieved from the user table during authentication.

    Attributes:
        access_key: User's access key
        role: User's role ("admin", "user", or "superadmin")
    """

    access_key: AccessKey
    role: str


@dataclass(frozen=True)
class JWTClaims:
    """
    JWT token payload for GraphQL Federation authentication.

    This dataclass represents the claims contained in a JWT token used for
    authenticating GraphQL requests through Hive Router.

    Contains minimal user information. Additional user information (user_id, domain_name,
    is_admin, is_superadmin) should be retrieved from the user table during authentication.

    Attributes:
        exp: Expiration time (UTC)
        iat: Issued at time (UTC)
        access_key: User's access key
        role: User role ("admin", "user", or "superadmin")
    """

    # Standard JWT claims (RFC 7519)
    exp: datetime
    iat: datetime

    # Backend.AI specific claims
    access_key: AccessKey
    role: str

    def to_dict(self) -> dict[str, Any]:
        """
        Convert JWTClaims to a dictionary suitable for JWT payload.

        Datetime objects are converted to Unix timestamps (integers) as required
        by the JWT standard.

        Returns:
            Dictionary representation of claims with timestamps as integers.
        """
        return {
            "exp": int(self.exp.timestamp()),
            "iat": int(self.iat.timestamp()),
            "access_key": str(self.access_key),
            "role": self.role,
        }

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
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            access_key=AccessKey(payload["access_key"]),
            role=payload["role"],
        )
