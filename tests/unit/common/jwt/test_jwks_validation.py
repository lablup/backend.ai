"""Tests for JWKS-based token validation and key rotation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from ai.backend.common.jwt.config import JWTAlgorithm, JWTConfig
from ai.backend.common.jwt.exceptions import JWKSKeyNotFoundError, JWTDecodeError
from ai.backend.common.jwt.jwks import JWKSKeySet
from ai.backend.common.jwt.keys import generate_rsa_key_pair, public_key_to_jwk
from ai.backend.common.jwt.signer import JWTSigner
from ai.backend.common.jwt.types import JWTClaims, JWTUserContext
from ai.backend.common.jwt.validator import JWTValidator
from ai.backend.common.types import AccessKey


@pytest.fixture
def rs256_config() -> JWTConfig:
    """Create RS256 JWT configuration."""
    return JWTConfig(
        algorithm=JWTAlgorithm.RS256,
        token_expiration_seconds=900,
    )


@pytest.fixture
def user_context() -> JWTUserContext:
    """Create test user context."""
    return JWTUserContext(
        access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
        role="user",
    )


class TestJWKSValidation:
    """Tests for validate_token_with_jwks."""

    def test_validate_with_jwks_key_set(
        self,
        rs256_config: JWTConfig,
        user_context: JWTUserContext,
    ) -> None:
        """Test token validation using a JWKS key set."""
        private_key, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="key-1")
        key_set = JWKSKeySet.from_jwks_dict({"keys": [jwk]})

        signer = JWTSigner(rs256_config)
        validator = JWTValidator(rs256_config)

        token = signer.generate_token(user_context, private_key=private_key, kid="key-1")
        claims = validator.validate_token_with_jwks(token, key_set)

        assert claims.access_key == user_context.access_key
        assert claims.role == user_context.role

    def test_validate_with_jwks_kid_not_found(
        self,
        rs256_config: JWTConfig,
        user_context: JWTUserContext,
    ) -> None:
        """Test that missing kid in JWKS raises JWKSKeyNotFoundError."""
        private_key, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="key-1")
        key_set = JWKSKeySet.from_jwks_dict({"keys": [jwk]})

        signer = JWTSigner(rs256_config)
        validator = JWTValidator(rs256_config)

        token = signer.generate_token(user_context, private_key=private_key, kid="key-unknown")

        with pytest.raises(JWKSKeyNotFoundError):
            validator.validate_token_with_jwks(token, key_set)

    def test_validate_with_jwks_no_kid_in_header(
        self,
        rs256_config: JWTConfig,
        user_context: JWTUserContext,
    ) -> None:
        """Test that token without kid header raises JWTDecodeError."""
        private_key, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="key-1")
        key_set = JWKSKeySet.from_jwks_dict({"keys": [jwk]})

        signer = JWTSigner(rs256_config)
        validator = JWTValidator(rs256_config)

        # Generate token without kid
        token = signer.generate_token(user_context, private_key=private_key)

        with pytest.raises(JWTDecodeError, match="kid"):
            validator.validate_token_with_jwks(token, key_set)


class TestKeyRotation:
    """Tests for key rotation scenarios."""

    def test_old_token_still_valid_after_adding_new_key(
        self,
        rs256_config: JWTConfig,
        user_context: JWTUserContext,
    ) -> None:
        """Test that tokens signed with key A still verify after adding key B."""
        private_key_a, public_key_a = generate_rsa_key_pair()
        private_key_b, public_key_b = generate_rsa_key_pair()

        signer = JWTSigner(rs256_config)
        validator = JWTValidator(rs256_config)

        # Sign with key A
        token_a = signer.generate_token(user_context, private_key=private_key_a, kid="key-a")

        # Create JWKS with both keys (simulating key rotation)
        jwk_a = public_key_to_jwk(public_key_a, kid="key-a")
        jwk_b = public_key_to_jwk(public_key_b, kid="key-b")
        key_set = JWKSKeySet.from_jwks_dict({"keys": [jwk_a, jwk_b]})

        # Old token should still validate
        claims = validator.validate_token_with_jwks(token_a, key_set)
        assert claims.access_key == user_context.access_key

    def test_new_token_with_new_key_validates(
        self,
        rs256_config: JWTConfig,
        user_context: JWTUserContext,
    ) -> None:
        """Test that tokens signed with key B validate with updated JWKS."""
        private_key_a, public_key_a = generate_rsa_key_pair()
        private_key_b, public_key_b = generate_rsa_key_pair()

        signer = JWTSigner(rs256_config)
        validator = JWTValidator(rs256_config)

        # Sign with key B
        token_b = signer.generate_token(user_context, private_key=private_key_b, kid="key-b")

        # JWKS with both keys
        jwk_a = public_key_to_jwk(public_key_a, kid="key-a")
        jwk_b = public_key_to_jwk(public_key_b, kid="key-b")
        key_set = JWKSKeySet.from_jwks_dict({"keys": [jwk_a, jwk_b]})

        claims = validator.validate_token_with_jwks(token_b, key_set)
        assert claims.access_key == user_context.access_key

    def test_token_fails_after_key_removal(
        self,
        rs256_config: JWTConfig,
        user_context: JWTUserContext,
    ) -> None:
        """Test that tokens fail after their signing key is removed from JWKS."""
        private_key_a, public_key_a = generate_rsa_key_pair()
        private_key_b, public_key_b = generate_rsa_key_pair()

        signer = JWTSigner(rs256_config)
        validator = JWTValidator(rs256_config)

        # Sign with key A
        token_a = signer.generate_token(user_context, private_key=private_key_a, kid="key-a")

        # JWKS with only key B (key A removed)
        jwk_b = public_key_to_jwk(public_key_b, kid="key-b")
        key_set = JWKSKeySet.from_jwks_dict({"keys": [jwk_b]})

        with pytest.raises(JWKSKeyNotFoundError):
            validator.validate_token_with_jwks(token_a, key_set)


class TestOAuth2Claims:
    """Tests for OAuth2-style claims round-trip."""

    def test_oauth2_claims_roundtrip_rs256(
        self,
        rs256_config: JWTConfig,
    ) -> None:
        """Test that OAuth2 claims (iss, aud, sub, scope, jti) survive round-trip."""
        private_key, public_key = generate_rsa_key_pair()

        now = datetime.now(UTC)
        payload = {
            "exp": int((now + timedelta(seconds=900)).timestamp()),
            "iat": int(now.timestamp()),
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "role": "user",
            "iss": "https://auth.example.com",
            "aud": "https://api.example.com",
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "scope": "read write admin",
            "jti": "unique-token-id-123",
        }

        token = pyjwt.encode(
            payload,
            private_key,
            algorithm="RS256",
            headers={"kid": "key-1"},
        )

        validator = JWTValidator(rs256_config)
        claims = validator.validate_token(token, public_key=public_key)

        assert claims.iss == "https://auth.example.com"
        assert claims.aud == "https://api.example.com"
        assert claims.sub == "550e8400-e29b-41d4-a716-446655440000"
        assert claims.scope == "read write admin"
        assert claims.jti == "unique-token-id-123"

    def test_oauth2_claims_optional_fields(
        self,
        rs256_config: JWTConfig,
    ) -> None:
        """Test that OAuth2 claims are optional (backward compat)."""
        private_key, public_key = generate_rsa_key_pair()

        now = datetime.now(UTC)
        payload = {
            "exp": int((now + timedelta(seconds=900)).timestamp()),
            "iat": int(now.timestamp()),
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "role": "user",
        }

        token = pyjwt.encode(
            payload,
            private_key,
            algorithm="RS256",
        )

        validator = JWTValidator(rs256_config)
        claims = validator.validate_token(token, public_key=public_key)

        assert claims.iss is None
        assert claims.aud is None
        assert claims.sub is None
        assert claims.scope is None
        assert claims.jti is None

    def test_oauth2_claims_to_dict_includes_set_fields(self) -> None:
        """Test that to_dict includes OAuth2 fields when set."""
        now = datetime.now(UTC)
        claims = JWTClaims(
            exp=now,
            iat=now,
            access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
            role="user",
            iss="https://auth.example.com",
            sub="user-id-123",
            scope="read",
        )
        d = claims.to_dict()
        assert d["iss"] == "https://auth.example.com"
        assert d["sub"] == "user-id-123"
        assert d["scope"] == "read"
        assert "aud" not in d
        assert "jti" not in d
