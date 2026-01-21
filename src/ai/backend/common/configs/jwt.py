"""JWT configuration schema for Backend.AI.

This module provides the shared JWT configuration used by both
manager and webserver for stateless authentication.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.jwt.config import JWTConfig as CoreJWTConfig
from ai.backend.common.meta import BackendAIConfigMeta, ConfigExample


class SharedJWTConfig(BaseConfigSchema):
    """JWT authentication configuration (shared between manager and webserver via etcd).

    Note: JWT tokens are signed using per-user secret keys (from keypair table),
    not a shared system secret key. This maintains the same security model as HMAC authentication.
    """

    algorithm: Annotated[
        str,
        Field(default="HS256"),
        BackendAIConfigMeta(
            description=(
                "Algorithm for JWT token signing. "
                "HS256 (HMAC-SHA256) is the default symmetric algorithm."
            ),
            added_version="25.16.0",
            example=ConfigExample(local="HS256", prod="HS256"),
        ),
    ]
    token_expiration_seconds: Annotated[
        int,
        Field(
            default=900,
            ge=60,
            le=86400,
            validation_alias=AliasChoices("token_expiration_seconds", "token-expiration-seconds"),
            serialization_alias="token-expiration-seconds",
        ),
        BackendAIConfigMeta(
            description=(
                "JWT token expiration time in seconds. "
                "Default is 900 seconds (15 minutes). "
                "Range: 60 seconds (1 minute) to 86400 seconds (24 hours). "
                "Shorter expiration times are more secure but may impact user experience."
            ),
            added_version="25.16.0",
            example=ConfigExample(local="900", prod="3600"),
        ),
    ]

    def to_jwt_config(self) -> CoreJWTConfig:
        """Convert to ai.backend.common.jwt.config.JWTConfig."""
        return CoreJWTConfig(
            algorithm=self.algorithm,
            token_expiration_seconds=self.token_expiration_seconds,
        )
