"""JWT authentication configuration for GraphQL Federation."""

from __future__ import annotations

from datetime import timedelta

from pydantic import Field

from ai.backend.common.config import BaseConfigSchema


class JWTConfig(BaseConfigSchema):
    """
    Configuration for JWT-based authentication in GraphQL Federation.

    This configuration must be consistent between webserver (which generates tokens)
    and manager (which validates tokens). The secret_key must be kept secure and
    should be the same on both sides.

    Attributes:
        enabled: Whether JWT authentication is enabled
        secret_key: Secret key for HS256 signing and verification
        algorithm: JWT signing algorithm (must be HS256)
        token_expiration_seconds: Token validity duration in seconds
        issuer: JWT issuer claim value for validation
        header_name: HTTP header name for JWT token transmission
    """

    enabled: bool = Field(
        default=True,
        description="Enable JWT authentication for GraphQL Federation requests",
    )

    secret_key: str = Field(
        description="Secret key for HS256 signing and verification. "
        "MUST be the same between webserver and manager. "
        "Should be at least 32 bytes of random data.",
    )

    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm (only HS256 is supported)",
    )

    token_expiration_seconds: int = Field(
        default=900,  # 15 minutes
        description="JWT token expiration time in seconds (default: 900 = 15 minutes)",
    )

    issuer: str = Field(
        default="backend.ai-webserver",
        description="JWT issuer claim value for GraphQL Federation tokens",
    )

    header_name: str = Field(
        default="X-BackendAI-Token",
        description="Custom HTTP header name for JWT token transmission",
    )

    @property
    def token_expiration(self) -> timedelta:
        """
        Get token expiration as a timedelta object.

        Returns:
            Token expiration duration as timedelta
        """
        return timedelta(seconds=self.token_expiration_seconds)
