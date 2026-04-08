"""JWT token signer for generating authentication tokens."""

from __future__ import annotations

from datetime import UTC, datetime

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

import jwt
from ai.backend.common.jwt.config import JWTAlgorithm, JWTConfig
from ai.backend.common.jwt.exceptions import JWTError
from ai.backend.common.jwt.types import JWTClaims, JWTUserContext


class JWTSigner:
    """
    JWT token generator for GraphQL Federation authentication.

    This class is used by the webserver to generate JWT tokens after successful
    HMAC authentication. The generated tokens are then forwarded to the manager
    via Hive Router using the X-BackendAI-Token header.

    Supports both HS256 (symmetric, per-user secret keys) and RS256 (asymmetric,
    RSA key pairs) signing algorithms.

    Usage (HS256):
        config = JWTConfig()
        signer = JWTSigner(config)
        token = signer.generate_token(user_context, secret_key="my-secret")

    Usage (RS256):
        config = JWTConfig(algorithm="RS256")
        signer = JWTSigner(config)
        token = signer.generate_token(user_context, private_key=rsa_private_key, kid="key-1")
    """

    _config: JWTConfig

    def __init__(self, config: JWTConfig) -> None:
        """
        Initialize JWT signer with configuration.

        Args:
            config: JWT configuration containing algorithm and expiration settings
        """
        self._config = config

    def generate_token(
        self,
        user_context: JWTUserContext,
        secret_key: str | None = None,
        *,
        private_key: RSAPrivateKey | None = None,
        kid: str | None = None,
    ) -> str:
        """
        Generate a JWT token from authenticated user context.

        For HS256, provide ``secret_key``. For RS256, provide ``private_key``
        and optionally ``kid`` (key ID included in the JWT header).

        Args:
            user_context: User context data containing authentication information
            secret_key: Secret key string for HS256 signing
            private_key: RSA private key object for RS256 signing
            kid: Key ID to include in the JWT header (RS256 only)

        Returns:
            Encoded JWT token string

        Raises:
            JWTError: If token generation fails or invalid key arguments are provided
        """
        now = datetime.now(UTC)

        claims = JWTClaims(
            exp=now + self._config.token_expiration,
            iat=now,
            access_key=user_context.access_key,
            role=user_context.role,
            kid=kid,
        )

        try:
            if self._config.algorithm == JWTAlgorithm.RS256:
                if private_key is None:
                    raise JWTError("RS256 algorithm requires a private_key argument")
                headers: dict[str, str] = {}
                if kid is not None:
                    headers["kid"] = kid
                return jwt.encode(
                    claims.to_dict(),
                    private_key,
                    algorithm=self._config.algorithm,
                    headers=headers if headers else None,
                )
            if secret_key is None:
                raise JWTError("HS256 algorithm requires a secret_key argument")
            return jwt.encode(
                claims.to_dict(),
                secret_key,
                algorithm=self._config.algorithm,
            )
        except JWTError:
            raise
        except Exception as e:
            raise JWTError(f"JWT generation failed: {e}") from e
