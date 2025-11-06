"""JWT configuration schema for Backend.AI.

This module provides the shared JWT configuration used by both
manager and webserver for stateless authentication.
"""

from __future__ import annotations

from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.jwt.config import JWTConfig as CoreJWTConfig


class SharedJWTConfig(BaseConfigSchema):
    """JWT authentication configuration (shared between manager and webserver via etcd).

    Note: JWT tokens are signed using per-user secret keys (from keypair table),
    not a shared system secret key. This maintains the same security model as HMAC authentication.
    """

    algorithm: str = Field(
        default="HS256",
        description="""
        Algorithm for JWT token signing.
        HS256 (HMAC-SHA256) is the default symmetric algorithm.
        """,
        examples=["HS256", "HS384", "HS512"],
    )
    token_expiration_seconds: int = Field(
        default=900,
        ge=60,
        le=86400,
        description="""
        JWT token expiration time in seconds.
        Default is 900 seconds (15 minutes).
        Range: 60 seconds (1 minute) to 86400 seconds (24 hours).
        Shorter expiration times are more secure but may impact user experience.
        """,
        examples=[900, 1800, 3600],
        validation_alias=AliasChoices("token_expiration_seconds", "token-expiration-seconds"),
        serialization_alias="token-expiration-seconds",
    )

    def to_jwt_config(self) -> CoreJWTConfig:
        """Convert to ai.backend.common.jwt.config.JWTConfig."""
        return CoreJWTConfig(
            algorithm=self.algorithm,
            token_expiration_seconds=self.token_expiration_seconds,
        )
