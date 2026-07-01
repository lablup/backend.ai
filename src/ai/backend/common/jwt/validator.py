"""JWT token validator for verifying authentication tokens."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

import jwt
from ai.backend.common.jwt.config import JWTAlgorithm, JWTConfig
from ai.backend.common.jwt.exceptions import (
    JWTDecodeError,
    JWTExpiredError,
    JWTInvalidClaimsError,
    JWTInvalidSignatureError,
)
from ai.backend.common.jwt.types import JWTClaims
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
)

if TYPE_CHECKING:
    from ai.backend.common.jwt.jwks import JWKSKeySet


class JWTValidator:
    """
    JWT token validator for GraphQL Federation authentication.

    This class is used by the manager to validate JWT tokens received from
    Hive Router via the X-BackendAI-Token header. It verifies the token's
    signature, expiration, and claims.

    Supports both HS256 (symmetric) and RS256 (asymmetric) validation.

    Usage (HS256):
        config = JWTConfig()
        validator = JWTValidator(config)
        claims = validator.validate_token(token_string, secret_key="my-secret")

    Usage (RS256):
        config = JWTConfig(algorithm="RS256")
        validator = JWTValidator(config)
        claims = validator.validate_token(token_string, public_key=rsa_public_key)

    Usage (JWKS):
        config = JWTConfig(algorithm="RS256")
        validator = JWTValidator(config)
        claims = validator.validate_token_with_jwks(token_string, jwks_key_set)
    """

    _config: JWTConfig

    def __init__(self, config: JWTConfig) -> None:
        """
        Initialize JWT validator with configuration.

        Args:
            config: JWT configuration containing algorithm and validation settings
        """
        self._config = config

    def validate_token(
        self,
        token: str,
        secret_key: str | None = None,
        *,
        public_key: RSAPublicKey | None = None,
    ) -> JWTClaims:
        """
        Validate JWT token and extract claims.

        This method performs comprehensive validation:
        1. Verifies the token signature using the provided key
        2. Checks token expiration
        3. Ensures all required claims are present and valid

        For HS256, provide ``secret_key``. For RS256, provide ``public_key``.

        Args:
            token: Encoded JWT token string
            secret_key: Secret key string for HS256 signature verification
            public_key: RSA public key object for RS256 signature verification

        Returns:
            JWTClaims object containing validated user information

        Raises:
            JWTExpiredError: If the token has expired
            JWTInvalidSignatureError: If signature verification fails
            JWTInvalidClaimsError: If claims are missing or invalid
            JWTDecodeError: If the token cannot be decoded
        """
        if self._config.algorithm == JWTAlgorithm.RS256:
            if public_key is None:
                raise JWTDecodeError("RS256 algorithm requires a public_key argument")
            key: str | RSAPublicKey = public_key
        else:
            if secret_key is None:
                raise JWTDecodeError("HS256 algorithm requires a secret_key argument")
            key = secret_key

        return self._decode_and_validate(token, key)

    def validate_token_with_jwks(
        self,
        token: str,
        jwks_key_set: JWKSKeySet,
    ) -> JWTClaims:
        """
        Validate JWT token using a JWKS key set.

        Extracts the ``kid`` (key ID) from the token header, looks up the
        corresponding public key in the JWKS key set, and validates the token.

        Args:
            token: Encoded JWT token string
            jwks_key_set: JWKS key set containing public keys indexed by kid

        Returns:
            JWTClaims object containing validated user information

        Raises:
            JWTExpiredError: If the token has expired
            JWTInvalidSignatureError: If signature verification fails
            JWTInvalidClaimsError: If claims are missing or invalid
            JWTDecodeError: If the token cannot be decoded or has no kid header
            JWKSKeyNotFoundError: If the kid is not found in the key set
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
        except DecodeError as e:
            raise JWTDecodeError(f"Failed to decode JWT header: {e}") from e

        kid = unverified_header.get("kid")
        if kid is None:
            raise JWTDecodeError("JWT token header does not contain a 'kid' field")

        public_key = jwks_key_set.get_key(kid)
        return self._decode_and_validate(token, public_key)

    def _decode_and_validate(
        self,
        token: str,
        key: str | RSAPublicKey,
    ) -> JWTClaims:
        """
        Decode a JWT token, verify its signature, and validate claims.

        Args:
            token: Encoded JWT token string
            key: Key for signature verification (str for HS256, RSAPublicKey for RS256)

        Returns:
            JWTClaims object containing validated user information

        Raises:
            JWTExpiredError: If the token has expired
            JWTInvalidSignatureError: If signature verification fails
            JWTInvalidClaimsError: If claims are missing or invalid
            JWTDecodeError: If the token cannot be decoded
        """
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=[self._config.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": False,
                },
            )

            claims = JWTClaims.from_dict(payload)
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
        valid_roles = {"admin", "user", "superadmin"}
        if claims.role not in valid_roles:
            raise JWTInvalidClaimsError(
                f"Invalid role: {claims.role}. Must be one of {valid_roles}"
            )
