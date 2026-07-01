"""
JWT authentication module for GraphQL Federation.

This module provides JWT-based authentication for GraphQL requests going through
Hive Router. It uses the X-BackendAI-Token custom header to avoid conflicts with
existing Bearer token usage in appproxy.

Supports both HS256 (symmetric, per-user secret keys) and RS256 (asymmetric,
RSA key pairs) signing algorithms, with JWKS utilities for distributed key
management.

Key components:
- JWTSigner: Generates JWT tokens from authenticated user context (webserver)
- JWTValidator: Validates JWT tokens and extracts user claims (manager)
- JWTConfig: Configuration for JWT authentication
- JWTClaims: Dataclass representing JWT payload claims
- JWKSKeySet: Public key set indexed by key ID for RS256 validation
- JWKSFetcher: Async JWKS endpoint fetcher with TTL caching
- Key utilities: RSA key generation, loading, serialization, and JWK conversion

Example usage (HS256):
    from ai.backend.common.jwt import JWTSigner, JWTConfig, JWTUserContext

    config = JWTConfig()
    signer = JWTSigner(config)

    user_context = JWTUserContext(
        access_key=access_key,
        role="user",
    )
    token = signer.generate_token(user_context, secret_key)

Example usage (RS256):
    from ai.backend.common.jwt import JWTSigner, JWTConfig, JWTUserContext
    from ai.backend.common.jwt.keys import load_private_key

    config = JWTConfig(algorithm="RS256")
    signer = JWTSigner(config)
    private_key = load_private_key(Path("/path/to/private.pem"))
    token = signer.generate_token(user_context, private_key=private_key, kid="key-1")
"""

from ai.backend.common.jwt.config import JWTAlgorithm, JWTConfig
from ai.backend.common.jwt.exceptions import (
    JWKSError,
    JWKSFetchError,
    JWKSKeyNotFoundError,
    JWTDecodeError,
    JWTError,
    JWTExpiredError,
    JWTInvalidClaimsError,
    JWTInvalidSignatureError,
)
from ai.backend.common.jwt.jwks import JWKSFetcher, JWKSKeySet
from ai.backend.common.jwt.keys import (
    generate_rsa_key_pair,
    load_private_key,
    load_public_key,
    private_key_to_pem,
    public_key_to_jwk,
    public_key_to_pem,
)
from ai.backend.common.jwt.signer import JWTSigner
from ai.backend.common.jwt.types import JWTClaims, JWTUserContext
from ai.backend.common.jwt.validator import JWTValidator

__all__ = [
    # Configuration
    "JWTAlgorithm",
    "JWTConfig",
    # Types
    "JWTClaims",
    "JWTUserContext",
    # Core classes
    "JWTSigner",
    "JWTValidator",
    # JWKS
    "JWKSKeySet",
    "JWKSFetcher",
    # Key management
    "generate_rsa_key_pair",
    "load_private_key",
    "load_public_key",
    "private_key_to_pem",
    "public_key_to_pem",
    "public_key_to_jwk",
    # Exceptions
    "JWTError",
    "JWTExpiredError",
    "JWTInvalidSignatureError",
    "JWTInvalidClaimsError",
    "JWTDecodeError",
    "JWKSError",
    "JWKSFetchError",
    "JWKSKeyNotFoundError",
]
