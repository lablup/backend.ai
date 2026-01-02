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

    Note: JWT tokens are signed using per-user secret keys (from keypair table),
    not a shared system secret key. This maintains the same security model as HMAC authentication.

    Usage:
        from ai.backend.common.jwt import JWTSigner, JWTConfig, JWTUserContext

        config = JWTConfig()
        signer = JWTSigner(config)

        user_context = JWTUserContext(
            user_id=user_uuid,
            access_key=access_key,
            role="user",
        )
        # Get user's secret key from keypair table
        secret_key = keypair.secret_key
        token = signer.generate_token(user_context, secret_key)
    """

    _config: JWTConfig

    def __init__(self, config: JWTConfig) -> None:
        """
        Initialize JWT signer with configuration.

        Args:
            config: JWT configuration containing algorithm and expiration settings
        """
        self._config = config

    def generate_token(self, user_context: JWTUserContext, secret_key: str) -> str:
        """
        Generate a JWT token from authenticated user context.

        This method creates a JWT token containing minimal user authentication
        information. The token is signed using HS256 with the user's secret key.

        Args:
            user_context: User context data containing authentication information
            secret_key: User's secret key from keypair table for signing the token

        Returns:
            Encoded JWT token string

        Raises:
            JWTError: If token generation fails
        """
        now = datetime.now(timezone.utc)

        claims = JWTClaims(
            exp=now + self._config.token_expiration,
            iat=now,
            access_key=user_context.access_key,
            role=user_context.role,
        )

        try:
            return jwt.encode(
                claims.to_dict(),
                secret_key,
                algorithm=self._config.algorithm,
            )
        except Exception as e:
            raise JWTError(f"JWT generation failed: {e}") from e
