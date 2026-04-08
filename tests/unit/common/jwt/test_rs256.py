"""Tests for RS256 signing and validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)

from ai.backend.common.jwt.config import JWTAlgorithm, JWTConfig
from ai.backend.common.jwt.exceptions import (
    JWTExpiredError,
    JWTInvalidSignatureError,
)
from ai.backend.common.jwt.keys import generate_rsa_key_pair
from ai.backend.common.jwt.signer import JWTSigner
from ai.backend.common.jwt.types import JWTUserContext
from ai.backend.common.jwt.validator import JWTValidator
from ai.backend.common.types import AccessKey


@pytest.fixture
def rsa_key_pair() -> tuple[RSAPrivateKey, RSAPublicKey]:
    """Generate an RSA key pair for testing."""
    return generate_rsa_key_pair()


@pytest.fixture
def rs256_config() -> JWTConfig:
    """Create RS256 JWT configuration."""
    return JWTConfig(
        algorithm=JWTAlgorithm.RS256,
        token_expiration_seconds=900,
    )


@pytest.fixture
def rs256_signer(rs256_config: JWTConfig) -> JWTSigner:
    """Create RS256 JWT signer."""
    return JWTSigner(rs256_config)


@pytest.fixture
def rs256_validator(rs256_config: JWTConfig) -> JWTValidator:
    """Create RS256 JWT validator."""
    return JWTValidator(rs256_config)


@pytest.fixture
def user_context() -> JWTUserContext:
    """Create test user context."""
    return JWTUserContext(
        access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        role="user",
    )


class TestRS256SignAndVerify:
    """Tests for RS256 sign and verify round-trip."""

    def test_rs256_roundtrip(
        self,
        rs256_signer: JWTSigner,
        rs256_validator: JWTValidator,
        rsa_key_pair: tuple[RSAPrivateKey, RSAPublicKey],
        user_context: JWTUserContext,
    ) -> None:
        """Test RS256 sign -> verify round-trip."""
        private_key, public_key = rsa_key_pair
        token = rs256_signer.generate_token(user_context, private_key=private_key, kid="test-key-1")
        claims = rs256_validator.validate_token(token, public_key=public_key)

        assert claims.access_key == user_context.access_key
        assert claims.role == user_context.role

    def test_rs256_token_has_kid_header(
        self,
        rs256_signer: JWTSigner,
        rsa_key_pair: tuple[RSAPrivateKey, RSAPublicKey],
        user_context: JWTUserContext,
    ) -> None:
        """Test that RS256 token includes kid in header."""
        private_key, _ = rsa_key_pair
        token = rs256_signer.generate_token(user_context, private_key=private_key, kid="my-kid")
        header = pyjwt.get_unverified_header(token)
        assert header["kid"] == "my-kid"
        assert header["alg"] == "RS256"

    def test_rs256_token_without_kid(
        self,
        rs256_signer: JWTSigner,
        rs256_validator: JWTValidator,
        rsa_key_pair: tuple[RSAPrivateKey, RSAPublicKey],
        user_context: JWTUserContext,
    ) -> None:
        """Test RS256 token without kid still works for direct validation."""
        private_key, public_key = rsa_key_pair
        token = rs256_signer.generate_token(user_context, private_key=private_key)
        claims = rs256_validator.validate_token(token, public_key=public_key)
        assert claims.access_key == user_context.access_key

    def test_rs256_with_wrong_key_fails(
        self,
        rs256_signer: JWTSigner,
        rs256_validator: JWTValidator,
        rsa_key_pair: tuple[RSAPrivateKey, RSAPublicKey],
        user_context: JWTUserContext,
    ) -> None:
        """Test that RS256 verification fails with a different key pair."""
        private_key, _ = rsa_key_pair
        _, wrong_public_key = generate_rsa_key_pair()

        token = rs256_signer.generate_token(user_context, private_key=private_key, kid="key-1")

        with pytest.raises(JWTInvalidSignatureError):
            rs256_validator.validate_token(token, public_key=wrong_public_key)

    def test_rs256_expired_token(
        self,
        rs256_config: JWTConfig,
        rs256_validator: JWTValidator,
        rsa_key_pair: tuple[RSAPrivateKey, RSAPublicKey],
        user_context: JWTUserContext,
    ) -> None:
        """Test that expired RS256 token raises JWTExpiredError."""
        private_key, public_key = rsa_key_pair
        past_time = datetime.now(UTC) - timedelta(hours=1)

        payload = {
            "exp": int((past_time + timedelta(seconds=900)).timestamp()),
            "iat": int(past_time.timestamp()),
            "access_key": str(user_context.access_key),
            "role": user_context.role,
        }

        expired_token = pyjwt.encode(
            payload,
            private_key,
            algorithm="RS256",
            headers={"kid": "key-1"},
        )

        with pytest.raises(JWTExpiredError):
            rs256_validator.validate_token(expired_token, public_key=public_key)


class TestHS256BackwardCompat:
    """Tests that HS256 still works after RS256 additions."""

    def test_hs256_roundtrip_still_works(self) -> None:
        """Test that HS256 sign/verify still works."""
        config = JWTConfig(algorithm=JWTAlgorithm.HS256, token_expiration_seconds=900)
        signer = JWTSigner(config)
        validator = JWTValidator(config)
        context = JWTUserContext(
            access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
            role="admin",
        )
        secret = "test-secret-key-at-least-32-bytes-long"

        token = signer.generate_token(context, secret)
        claims = validator.validate_token(token, secret)

        assert claims.access_key == context.access_key
        assert claims.role == context.role

    def test_hs256_default_config(self) -> None:
        """Test that default config is HS256."""
        config = JWTConfig()
        assert config.algorithm == JWTAlgorithm.HS256
