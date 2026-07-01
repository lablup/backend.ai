"""JWT authentication configuration for GraphQL Federation."""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum
from pathlib import Path

from pydantic import Field

from ai.backend.common.config import BaseConfigSchema


class JWTAlgorithm(StrEnum):
    """Supported JWT signing algorithms."""

    HS256 = "HS256"
    RS256 = "RS256"


class JWTConfig(BaseConfigSchema):
    """
    Configuration for JWT-based authentication in GraphQL Federation.

    This configuration must be consistent between webserver (which generates tokens)
    and manager (which validates tokens).

    Supports both HS256 (symmetric, per-user secret keys) and RS256 (asymmetric,
    RSA key pairs) signing algorithms.

    JWT tokens are transmitted via X-BackendAI-Token HTTP header.

    Attributes:
        enabled: Whether JWT authentication is enabled
        algorithm: JWT signing algorithm (HS256 or RS256)
        token_expiration_seconds: Token validity duration in seconds
        private_key_path: Path to PEM-encoded RSA private key (RS256 only)
        public_key_path: Path to PEM-encoded RSA public key (RS256 only)
    """

    enabled: bool = Field(
        default=True,
        description="Enable JWT authentication for GraphQL Federation requests",
    )

    algorithm: JWTAlgorithm = Field(
        default=JWTAlgorithm.HS256,
        description="JWT signing algorithm (HS256 or RS256)",
    )

    token_expiration_seconds: int = Field(
        default=900,  # 15 minutes
        description="JWT token expiration time in seconds (default: 900 = 15 minutes)",
    )

    private_key_path: Path | None = Field(
        default=None,
        description="Path to PEM-encoded RSA private key file (required for RS256 signing)",
    )

    public_key_path: Path | None = Field(
        default=None,
        description="Path to PEM-encoded RSA public key file (required for RS256 validation)",
    )

    @property
    def token_expiration(self) -> timedelta:
        """
        Get token expiration as a timedelta object.

        Returns:
            Token expiration duration as timedelta
        """
        return timedelta(seconds=self.token_expiration_seconds)
