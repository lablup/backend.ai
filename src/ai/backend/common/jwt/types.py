"""JWT token types and claims for GraphQL Federation authentication."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ai.backend.common.types import AccessKey


@dataclass(frozen=True)
class JWTUserContext:
    """
    User context data for JWT token generation.

    This dataclass encapsulates all user information needed to generate
    a JWT token. It provides a structured way to pass user data from
    the authentication layer to the JWT signer.

    Attributes:
        user_id: User's UUID
        access_key: User's access key
        role: User's role ("admin", "user", or "superadmin")
        domain_name: User's domain name
        is_admin: Whether the user has admin privileges
        is_superadmin: Whether the user has superadmin privileges
    """

    user_id: UUID
    access_key: AccessKey
    role: str
    domain_name: str
    is_admin: bool
    is_superadmin: bool


@dataclass(frozen=True)
class JWTClaims:
    """
    JWT token payload for GraphQL Federation authentication.

    This dataclass represents the claims contained in a JWT token used for
    authenticating GraphQL requests through Hive Router. The token is distinguished
    from other JWT uses (like appproxy) by the 'iss' (issuer) claim.

    Attributes:
        sub: Subject - User UUID
        exp: Expiration time (UTC)
        iat: Issued at time (UTC)
        iss: Issuer identifier (e.g., "backend.ai-webserver")
        access_key: User's access key
        role: User role ("admin", "user", or "superadmin")
        domain_name: User's domain
        is_admin: Whether user has admin privileges
        is_superadmin: Whether user has superadmin privileges
    """

    # Standard JWT claims (RFC 7519)
    sub: UUID
    exp: datetime
    iat: datetime
    iss: str

    # Backend.AI specific claims
    access_key: AccessKey
    role: str
    domain_name: str
    is_admin: bool
    is_superadmin: bool

    def to_dict(self) -> dict[str, Any]:
        """
        Convert JWTClaims to a dictionary suitable for JWT payload.

        Datetime objects are converted to Unix timestamps (integers) as required
        by the JWT standard.

        Returns:
            Dictionary representation of claims with timestamps as integers.
        """
        return {
            "sub": str(self.sub),
            "exp": int(self.exp.timestamp()),
            "iat": int(self.iat.timestamp()),
            "iss": self.iss,
            "access_key": str(self.access_key),
            "role": self.role,
            "domain_name": self.domain_name,
            "is_admin": self.is_admin,
            "is_superadmin": self.is_superadmin,
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
            sub=UUID(payload["sub"]),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            iss=payload["iss"],
            access_key=AccessKey(payload["access_key"]),
            role=payload["role"],
            domain_name=payload["domain_name"],
            is_admin=payload["is_admin"],
            is_superadmin=payload["is_superadmin"],
        )
