"""
JWT authentication module for GraphQL Federation.

This module provides JWT-based authentication for GraphQL requests going through
Hive Router. It uses the X-BackendAI-Token custom header to avoid conflicts with
existing Bearer token usage in appproxy.

Key components:
- JWTSigner: Generates JWT tokens from authenticated user context (webserver)
- JWTValidator: Validates JWT tokens and extracts user claims (manager)
- JWTConfig: Configuration for JWT authentication
- JWTClaims: Dataclass representing JWT payload claims

Example usage in webserver:
    from ai.backend.common.jwt import JWTSigner, JWTConfig, JWTUserContext

    config = JWTConfig(secret_key=os.environ["JWT_SECRET_KEY"])
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

    # Add to request headers
    headers["X-BackendAI-Token"] = token

Example usage in manager:
    from ai.backend.common.jwt import JWTValidator, JWTConfig

    config = JWTConfig(secret_key=os.environ["JWT_SECRET_KEY"])
    validator = JWTValidator(config)

    token = request.headers.get("X-BackendAI-Token")
    claims = validator.validate_token(token)

    # Use claims for authentication
    user_id = claims.sub
    access_key = claims.access_key
"""

from .config import JWTConfig
from .exceptions import (
    JWTDecodeError,
    JWTError,
    JWTExpiredError,
    JWTInvalidClaimsError,
    JWTInvalidSignatureError,
)
from .signer import JWTSigner
from .types import JWTClaims, JWTUserContext
from .validator import JWTValidator

__all__ = [
    # Configuration
    "JWTConfig",
    # Types
    "JWTClaims",
    "JWTUserContext",
    # Core classes
    "JWTSigner",
    "JWTValidator",
    # Exceptions
    "JWTError",
    "JWTExpiredError",
    "JWTInvalidSignatureError",
    "JWTInvalidClaimsError",
    "JWTDecodeError",
]
