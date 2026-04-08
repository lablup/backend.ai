"""JWT token types and claims for GraphQL Federation authentication."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
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
        kid: Key ID used to sign this token (optional, for RS256/JWKS)
        iss: Issuer identifier (optional, for OAuth2)
        aud: Audience identifier (optional, for OAuth2)
        sub: Subject identifier (optional, for OAuth2)
        scope: Space-separated scope string (optional, for OAuth2)
        jti: JWT ID / token identifier (optional, for OAuth2)
    """

    # Standard JWT claims (RFC 7519)
    exp: datetime
    iat: datetime

    # Backend.AI specific claims
    access_key: AccessKey
    role: str

    # Optional claims for RS256/JWKS and OAuth2
    kid: str | None = field(default=None)
    iss: str | None = field(default=None)
    aud: str | None = field(default=None)
    sub: str | None = field(default=None)
    scope: str | None = field(default=None)
    jti: str | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert JWTClaims to a dictionary suitable for JWT payload.

        Datetime objects are converted to Unix timestamps (integers) as required
        by the JWT standard. Optional fields are only included when set.

        Returns:
            Dictionary representation of claims with timestamps as integers.
        """
        result: dict[str, Any] = {
            "exp": int(self.exp.timestamp()),
            "iat": int(self.iat.timestamp()),
            "access_key": str(self.access_key),
            "role": self.role,
        }
        if self.kid is not None:
            result["kid"] = self.kid
        if self.iss is not None:
            result["iss"] = self.iss
        if self.aud is not None:
            result["aud"] = self.aud
        if self.sub is not None:
            result["sub"] = self.sub
        if self.scope is not None:
            result["scope"] = self.scope
        if self.jti is not None:
            result["jti"] = self.jti
        return result

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
            access_key=AccessKey(payload["access_key"]),
            role=payload["role"],
            kid=payload.get("kid"),
            iss=payload.get("iss"),
            aud=payload.get("aud"),
            sub=payload.get("sub"),
            scope=payload.get("scope"),
            jti=payload.get("jti"),
        )
