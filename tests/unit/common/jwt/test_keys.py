"""Tests for RSA key management utilities."""

from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)

from ai.backend.common.jwt.keys import (
    generate_rsa_key_pair,
    load_private_key,
    load_public_key,
    private_key_to_pem,
    public_key_to_jwk,
    public_key_to_pem,
)


class TestGenerateRSAKeyPair:
    """Tests for generate_rsa_key_pair."""

    def test_generates_valid_key_pair(self) -> None:
        """Test that a valid RSA key pair is generated."""
        private_key, public_key = generate_rsa_key_pair()
        assert isinstance(private_key, RSAPrivateKey)
        assert isinstance(public_key, RSAPublicKey)

    def test_default_key_size_is_2048(self) -> None:
        """Test that the default key size is 2048 bits."""
        private_key, _ = generate_rsa_key_pair()
        assert private_key.key_size == 2048

    def test_custom_key_size(self) -> None:
        """Test generating keys with a custom key size."""
        private_key, _ = generate_rsa_key_pair(key_size=4096)
        assert private_key.key_size == 4096

    def test_public_key_matches_private_key(self) -> None:
        """Test that the public key corresponds to the private key."""
        private_key, public_key = generate_rsa_key_pair()
        derived_public_key = private_key.public_key()
        assert public_key.public_numbers().n == derived_public_key.public_numbers().n
        assert public_key.public_numbers().e == derived_public_key.public_numbers().e


class TestPEMSerialization:
    """Tests for PEM serialization and loading."""

    def test_private_key_pem_roundtrip(self, tmp_path: Path) -> None:
        """Test private key serialization and loading roundtrip."""
        private_key, _ = generate_rsa_key_pair()
        pem_bytes = private_key_to_pem(private_key)

        key_file = tmp_path / "private.pem"
        key_file.write_bytes(pem_bytes)

        loaded_key = load_private_key(key_file)
        assert isinstance(loaded_key, RSAPrivateKey)
        assert (
            loaded_key.private_numbers().public_numbers.n
            == private_key.private_numbers().public_numbers.n
        )

    def test_public_key_pem_roundtrip(self, tmp_path: Path) -> None:
        """Test public key serialization and loading roundtrip."""
        _, public_key = generate_rsa_key_pair()
        pem_bytes = public_key_to_pem(public_key)

        key_file = tmp_path / "public.pem"
        key_file.write_bytes(pem_bytes)

        loaded_key = load_public_key(key_file)
        assert isinstance(loaded_key, RSAPublicKey)
        assert loaded_key.public_numbers().n == public_key.public_numbers().n

    def test_private_key_pem_starts_with_header(self) -> None:
        """Test that PEM-encoded private key has correct header."""
        private_key, _ = generate_rsa_key_pair()
        pem_bytes = private_key_to_pem(private_key)
        assert pem_bytes.startswith(b"-----BEGIN PRIVATE KEY-----")

    def test_public_key_pem_starts_with_header(self) -> None:
        """Test that PEM-encoded public key has correct header."""
        _, public_key = generate_rsa_key_pair()
        pem_bytes = public_key_to_pem(public_key)
        assert pem_bytes.startswith(b"-----BEGIN PUBLIC KEY-----")


class TestPublicKeyToJWK:
    """Tests for public_key_to_jwk conversion."""

    def test_jwk_has_required_fields(self) -> None:
        """Test that JWK output contains all required fields."""
        _, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="test-key-1")

        assert jwk["kty"] == "RSA"
        assert jwk["kid"] == "test-key-1"
        assert jwk["use"] == "sig"
        assert jwk["alg"] == "RS256"
        assert "n" in jwk
        assert "e" in jwk

    def test_jwk_n_and_e_are_strings(self) -> None:
        """Test that n and e values are base64url-encoded strings."""
        _, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="test-key-1")

        assert isinstance(jwk["n"], str)
        assert isinstance(jwk["e"], str)
        # Base64url should not contain padding
        assert "=" not in jwk["n"]
        assert "=" not in jwk["e"]

    def test_jwk_different_kid(self) -> None:
        """Test that different kid values are correctly set."""
        _, public_key = generate_rsa_key_pair()
        jwk_a = public_key_to_jwk(public_key, kid="key-a")
        jwk_b = public_key_to_jwk(public_key, kid="key-b")

        assert jwk_a["kid"] == "key-a"
        assert jwk_b["kid"] == "key-b"
        # Same key, so n and e should be identical
        assert jwk_a["n"] == jwk_b["n"]


class TestLoadKeyErrors:
    """Tests for key loading error cases."""

    def test_load_private_key_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that loading from a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_private_key(tmp_path / "nonexistent.pem")

    def test_load_public_key_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that loading from a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_public_key(tmp_path / "nonexistent.pem")
