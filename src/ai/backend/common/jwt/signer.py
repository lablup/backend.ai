"""JWT token signer for generating authentication tokens."""

from __future__ import annotations

from datetime import datetime, timezone

import jwt

from .config import JWTConfig
from .exceptions import JWTError
from .types import JWTClaims, JWTUserContext


class JWTSigner:
    """
    JWT token generator for GraphQL Federation authentication.

    This class is used by the webserver to generate JWT tokens after successful
    HMAC authentication. The generated tokens are then forwarded to the manager
    via Hive Router using the X-BackendAI-Token header.

    Usage:
        from ai.backend.common.jwt import JWTSigner, JWTConfig, JWTUserContext

        config = JWTConfig(secret_key="your-secret-key")
        signer = JWTSigner(config)

        user_context = JWTUserContext(
            user_id=user_uuid,
            access_key=access_key,
            role="user",
            domain_name="default",
            is_admin=False,
            is_superadmin=False,
        )
        token = signer.generate_token(user_context)
    """

    _config: JWTConfig

    def __init__(self, config: JWTConfig) -> None:
        """
        Initialize JWT signer with configuration.

        Args:
            config: JWT configuration containing secret key and other settings
        """
        self._config = config

    def generate_token(self, user_context: JWTUserContext) -> str:
        """
        Generate a JWT token from authenticated user context.

        This method creates a JWT token containing all necessary user authentication
        information. The token is signed using HS256 with the configured secret key.

        Args:
            user_context: User context data containing authentication information

        Returns:
            Encoded JWT token string

        Raises:
            JWTError: If token generation fails
        """
        now = datetime.now(timezone.utc)

        claims = JWTClaims(
            sub=user_context.user_id,
            exp=now + self._config.token_expiration,
            iat=now,
            iss=self._config.issuer,
            access_key=user_context.access_key,
            role=user_context.role,
            domain_name=user_context.domain_name,
            is_admin=user_context.is_admin,
            is_superadmin=user_context.is_superadmin,
        )

        try:
            return jwt.encode(
                claims.to_dict(),
                self._config.secret_key,
                algorithm=self._config.algorithm,
            )
        except Exception as e:
            raise JWTError(f"JWT generation failed: {e}") from e
