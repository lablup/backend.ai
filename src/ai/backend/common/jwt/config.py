"""JWT authentication configuration for GraphQL Federation."""

from __future__ import annotations

from datetime import timedelta

from pydantic import Field

from ai.backend.common.config import BaseConfigSchema


class JWTConfig(BaseConfigSchema):
    """
    Configuration for JWT-based authentication in GraphQL Federation.

    This configuration must be consistent between webserver (which generates tokens)
    and manager (which validates tokens).

    Note: JWT tokens are signed using per-user secret keys (from keypair table),
    not a shared system secret key. This maintains the same security model as HMAC authentication.

    JWT tokens are transmitted via X-BackendAI-Token HTTP header.

    Attributes:
        enabled: Whether JWT authentication is enabled
        algorithm: JWT signing algorithm (must be HS256)
        token_expiration_seconds: Token validity duration in seconds
    """

    enabled: bool = Field(
        default=True,
        description="Enable JWT authentication for GraphQL Federation requests",
    )

    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm (only HS256 is supported)",
    )

    token_expiration_seconds: int = Field(
        default=900,  # 15 minutes
        description="JWT token expiration time in seconds (default: 900 = 15 minutes)",
    )

    @property
    def token_expiration(self) -> timedelta:
        """
        Get token expiration as a timedelta object.

        Returns:
            Token expiration duration as timedelta
        """
        return timedelta(seconds=self.token_expiration_seconds)
