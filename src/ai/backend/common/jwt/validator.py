"""JWT token validator for verifying authentication tokens."""

from __future__ import annotations

import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
)

from .config import JWTConfig
from .exceptions import (
    JWTDecodeError,
    JWTExpiredError,
    JWTInvalidClaimsError,
    JWTInvalidSignatureError,
)
from .types import JWTClaims


class JWTValidator:
    """
    JWT token validator for GraphQL Federation authentication.

    This class is used by the manager to validate JWT tokens received from
    Hive Router via the X-BackendAI-Token header. It verifies the token's
    signature, expiration, and claims.

    Note: JWT tokens are signed using per-user secret keys (from keypair table),
    not a shared system secret key. This maintains the same security model as HMAC authentication.

    Usage:
        config = JWTConfig()
        validator = JWTValidator(config)
        # Get user's secret key from keypair table after extracting access_key from token
        claims = validator.validate_token(token_string, secret_key)
    """

    _config: JWTConfig

    def __init__(self, config: JWTConfig) -> None:
        """
        Initialize JWT validator with configuration.

        Args:
            config: JWT configuration containing algorithm and validation settings
        """
        self._config = config

    def validate_token(self, token: str, secret_key: str) -> JWTClaims:
        """
        Validate JWT token and extract claims.

        This method performs comprehensive validation:
        1. Verifies the token signature using the user's secret key
        2. Checks token expiration
        3. Ensures all required claims are present and valid

        Args:
            token: Encoded JWT token string
            secret_key: User's secret key from keypair table for signature verification

        Returns:
            JWTClaims object containing validated user information

        Raises:
            JWTExpiredError: If the token has expired
            JWTInvalidSignatureError: If signature verification fails
            JWTInvalidClaimsError: If claims are missing or invalid
            JWTDecodeError: If the token cannot be decoded
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[self._config.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                },
            )

            # Parse claims from payload
            claims = JWTClaims.from_dict(payload)

            # Validate claim values
            self._validate_claims(claims)

            return claims

        except ExpiredSignatureError as e:
            raise JWTExpiredError("JWT token has expired") from e
        except InvalidSignatureError as e:
            raise JWTInvalidSignatureError("JWT signature verification failed") from e
        except (KeyError, ValueError, TypeError) as e:
            raise JWTInvalidClaimsError(f"JWT claims are invalid: {e}") from e
        except DecodeError as e:
            raise JWTDecodeError(f"Failed to decode JWT token: {e}") from e

    def _validate_claims(self, claims: JWTClaims) -> None:
        """
        Validate claim values meet requirements.

        Ensures that role is one of the expected values.

        Args:
            claims: Parsed JWT claims to validate

        Raises:
            JWTInvalidClaimsError: If validation fails
        """
        # Validate role is one of expected values
        valid_roles = {"admin", "user", "superadmin"}
        if claims.role not in valid_roles:
            raise JWTInvalidClaimsError(
                f"Invalid role: {claims.role}. Must be one of {valid_roles}"
            )
