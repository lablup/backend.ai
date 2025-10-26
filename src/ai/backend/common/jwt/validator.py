"""JWT token validator for verifying authentication tokens."""

from __future__ import annotations

import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidIssuerError,
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

    Usage:
        config = JWTConfig(secret_key="your-secret-key")
        validator = JWTValidator(config)
        claims = validator.validate_token(token_string)
    """

    _config: JWTConfig

    def __init__(self, config: JWTConfig) -> None:
        """
        Initialize JWT validator with configuration.

        Args:
            config: JWT configuration containing secret key and validation settings
        """
        self._config = config

    def validate_token(self, token: str) -> JWTClaims:
        """
        Validate JWT token and extract claims.

        This method performs comprehensive validation:
        1. Verifies the token signature using the configured secret key
        2. Checks token expiration
        3. Validates the issuer claim
        4. Ensures all required claims are present and valid

        Args:
            token: Encoded JWT token string

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
                self._config.secret_key,
                algorithms=[self._config.algorithm],
                issuer=self._config.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
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
        except InvalidIssuerError as e:
            raise JWTInvalidClaimsError(f"Invalid issuer: {e}") from e
        except (KeyError, ValueError, TypeError) as e:
            raise JWTInvalidClaimsError(f"JWT claims are invalid: {e}") from e
        except DecodeError as e:
            raise JWTDecodeError(f"Failed to decode JWT token: {e}") from e

    def _validate_claims(self, claims: JWTClaims) -> None:
        """
        Validate claim values meet requirements.

        Ensures that role is one of the expected values and that the issuer
        matches the configured value.

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

        # Validate issuer matches expected value
        if claims.iss != self._config.issuer:
            raise JWTInvalidClaimsError(
                f"Invalid issuer: expected '{self._config.issuer}', got '{claims.iss}'"
            )
