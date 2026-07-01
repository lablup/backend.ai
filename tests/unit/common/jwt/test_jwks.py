"""Tests for JWKS key set and fetcher."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from ai.backend.common.jwt.exceptions import JWKSFetchError, JWKSKeyNotFoundError
from ai.backend.common.jwt.jwks import JWKSFetcher, JWKSKeySet
from ai.backend.common.jwt.keys import generate_rsa_key_pair, public_key_to_jwk


@pytest.fixture
def rsa_keys_with_jwks() -> dict[str, dict[str, str] | RSAPublicKey]:
    """Generate RSA keys and their JWK representations."""
    private_key_a, public_key_a = generate_rsa_key_pair()
    private_key_b, public_key_b = generate_rsa_key_pair()
    jwk_a = public_key_to_jwk(public_key_a, kid="key-a")
    jwk_b = public_key_to_jwk(public_key_b, kid="key-b")
    return {
        "jwk_a": jwk_a,
        "jwk_b": jwk_b,
        "public_key_a": public_key_a,
        "public_key_b": public_key_b,
    }


class TestJWKSKeySet:
    """Tests for JWKSKeySet parsing and key lookup."""

    def test_from_jwks_dict_parses_keys(self) -> None:
        """Test parsing a JWKS dict with multiple keys."""
        _, public_key_a = generate_rsa_key_pair()
        _, public_key_b = generate_rsa_key_pair()
        jwk_a = public_key_to_jwk(public_key_a, kid="key-a")
        jwk_b = public_key_to_jwk(public_key_b, kid="key-b")

        jwks_dict = {"keys": [jwk_a, jwk_b]}
        key_set = JWKSKeySet.from_jwks_dict(jwks_dict)

        assert "key-a" in key_set.kids
        assert "key-b" in key_set.kids
        assert len(key_set.kids) == 2

    def test_get_key_returns_correct_key(self) -> None:
        """Test that get_key returns the correct public key by kid."""
        _, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="my-key")

        key_set = JWKSKeySet.from_jwks_dict({"keys": [jwk]})
        retrieved_key = key_set.get_key("my-key")

        assert isinstance(retrieved_key, RSAPublicKey)
        assert retrieved_key.public_numbers().n == public_key.public_numbers().n

    def test_get_key_not_found_raises_error(self) -> None:
        """Test that get_key raises JWKSKeyNotFoundError for unknown kid."""
        key_set = JWKSKeySet.from_jwks_dict({"keys": []})

        with pytest.raises(JWKSKeyNotFoundError):
            key_set.get_key("nonexistent-key")

    def test_from_jwks_dict_ignores_non_rsa_keys(self) -> None:
        """Test that non-RSA keys in the JWKS are ignored."""
        _, public_key = generate_rsa_key_pair()
        rsa_jwk = public_key_to_jwk(public_key, kid="rsa-key")
        ec_jwk = {"kty": "EC", "kid": "ec-key", "crv": "P-256", "x": "abc", "y": "def"}

        key_set = JWKSKeySet.from_jwks_dict({"keys": [rsa_jwk, ec_jwk]})
        assert key_set.kids == ["rsa-key"]

    def test_from_jwks_dict_ignores_keys_without_kid(self) -> None:
        """Test that keys without a kid field are ignored."""
        _, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="has-kid")
        jwk_no_kid = public_key_to_jwk(public_key, kid="temp")
        del jwk_no_kid["kid"]

        key_set = JWKSKeySet.from_jwks_dict({"keys": [jwk, jwk_no_kid]})
        assert key_set.kids == ["has-kid"]

    def test_from_jwks_dict_empty_keys(self) -> None:
        """Test parsing a JWKS dict with no keys."""
        key_set = JWKSKeySet.from_jwks_dict({"keys": []})
        assert key_set.kids == []

    def test_from_jwks_dict_missing_keys_field(self) -> None:
        """Test parsing a JWKS dict with no 'keys' field."""
        key_set = JWKSKeySet.from_jwks_dict({})
        assert key_set.kids == []


class TestJWKSFetcher:
    """Tests for JWKSFetcher caching and fetching."""

    async def test_get_key_fetches_on_first_call(self) -> None:
        """Test that the first call to get_key fetches the JWKS endpoint."""
        _, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="key-1")
        jwks_response = {"keys": [jwk]}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=jwks_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("ai.backend.common.jwt.jwks.aiohttp.ClientSession", return_value=mock_session):
            fetcher = JWKSFetcher(url="https://example.com/.well-known/jwks.json")
            result = await fetcher.get_key("key-1")

        assert isinstance(result, RSAPublicKey)
        mock_session.get.assert_called_once_with("https://example.com/.well-known/jwks.json")

    async def test_get_key_uses_cache_within_ttl(self) -> None:
        """Test that subsequent calls use the cache within TTL."""
        _, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="key-1")
        jwks_response = {"keys": [jwk]}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=jwks_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("ai.backend.common.jwt.jwks.aiohttp.ClientSession", return_value=mock_session):
            fetcher = JWKSFetcher(
                url="https://example.com/.well-known/jwks.json",
                cache_ttl=300.0,
            )
            # First call fetches
            await fetcher.get_key("key-1")
            # Second call should use cache
            await fetcher.get_key("key-1")

        # Should only have fetched once
        assert mock_session.get.call_count == 1

    async def test_get_key_refetches_after_ttl(self) -> None:
        """Test that the cache is refreshed after TTL expires."""
        _, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="key-1")
        jwks_response = {"keys": [jwk]}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=jwks_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("ai.backend.common.jwt.jwks.aiohttp.ClientSession", return_value=mock_session):
            fetcher = JWKSFetcher(
                url="https://example.com/.well-known/jwks.json",
                cache_ttl=0.0,  # Immediate expiry
            )
            await fetcher.get_key("key-1")
            # With TTL=0, next call should refetch
            await fetcher.get_key("key-1")

        assert mock_session.get.call_count == 2

    async def test_refresh_forces_fetch(self) -> None:
        """Test that refresh() forces a new fetch regardless of TTL."""
        _, public_key = generate_rsa_key_pair()
        jwk = public_key_to_jwk(public_key, kid="key-1")
        jwks_response = {"keys": [jwk]}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=jwks_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("ai.backend.common.jwt.jwks.aiohttp.ClientSession", return_value=mock_session):
            fetcher = JWKSFetcher(
                url="https://example.com/.well-known/jwks.json",
                cache_ttl=9999.0,
            )
            await fetcher.get_key("key-1")
            await fetcher.refresh()

        assert mock_session.get.call_count == 2

    async def test_fetch_error_raises_jwks_fetch_error(self) -> None:
        """Test that HTTP errors raise JWKSFetchError."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("ai.backend.common.jwt.jwks.aiohttp.ClientSession", return_value=mock_session):
            fetcher = JWKSFetcher(url="https://example.com/.well-known/jwks.json")
            with pytest.raises(JWKSFetchError):
                await fetcher.get_key("key-1")

    async def test_connection_error_raises_jwks_fetch_error(self) -> None:
        """Test that connection errors raise JWKSFetchError."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=ConnectionError("Connection refused"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("ai.backend.common.jwt.jwks.aiohttp.ClientSession", return_value=mock_session):
            fetcher = JWKSFetcher(url="https://example.com/.well-known/jwks.json")
            with pytest.raises(JWKSFetchError):
                await fetcher.get_key("key-1")
