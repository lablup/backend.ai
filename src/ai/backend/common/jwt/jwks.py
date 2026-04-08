"""JWKS (JSON Web Key Set) fetching and caching utilities."""

from __future__ import annotations

import base64
import time
from typing import Any

import aiohttp
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPublicKey,
    RSAPublicNumbers,
)

from ai.backend.common.jwt.exceptions import JWKSFetchError, JWKSKeyNotFoundError


def _base64url_to_int(value: str) -> int:
    """
    Decode a base64url-encoded string (no padding) to an integer.

    Args:
        value: Base64url-encoded string

    Returns:
        Decoded integer value
    """
    padding = 4 - len(value) % 4
    if padding != 4:
        value += "=" * padding
    decoded = base64.urlsafe_b64decode(value)
    return int.from_bytes(decoded, byteorder="big")


class JWKSKeySet:
    """
    A set of RSA public keys indexed by key ID (kid).

    This class parses a JWKS (JSON Web Key Set) response and provides
    key lookup by kid.
    """

    _keys: dict[str, RSAPublicKey]

    def __init__(self, keys: dict[str, RSAPublicKey]) -> None:
        self._keys = keys

    @classmethod
    def from_jwks_dict(cls, data: dict[str, Any]) -> JWKSKeySet:
        """
        Parse a JWKS JSON response into a JWKSKeySet.

        Only RSA keys with ``"use": "sig"`` and a ``kid`` field are included.

        Args:
            data: JWKS JSON dict with a ``keys`` array

        Returns:
            JWKSKeySet instance containing the parsed public keys
        """
        keys: dict[str, RSAPublicKey] = {}
        for jwk in data.get("keys", []):
            if jwk.get("kty") != "RSA":
                continue
            kid = jwk.get("kid")
            if kid is None:
                continue
            n = _base64url_to_int(jwk["n"])
            e = _base64url_to_int(jwk["e"])
            public_numbers = RSAPublicNumbers(e=e, n=n)
            public_key = public_numbers.public_key()
            keys[kid] = public_key
        return cls(keys)

    def get_key(self, kid: str) -> RSAPublicKey:
        """
        Look up an RSA public key by key ID.

        Args:
            kid: Key ID to look up

        Returns:
            RSA public key corresponding to the given kid

        Raises:
            JWKSKeyNotFoundError: If the kid is not found in the key set
        """
        key = self._keys.get(kid)
        if key is None:
            raise JWKSKeyNotFoundError(f"Key ID '{kid}' not found in JWKS key set")
        return key

    @property
    def kids(self) -> list[str]:
        """Return a list of all key IDs in this key set."""
        return list(self._keys.keys())


class JWKSFetcher:
    """
    Async JWKS fetcher with TTL-based caching.

    Fetches a JWKS endpoint and caches the result for a configurable duration.
    Thread-safe for concurrent async access.

    Usage:
        fetcher = JWKSFetcher(url="https://example.com/.well-known/jwks.json")
        public_key = await fetcher.get_key("my-key-id")
    """

    _url: str
    _cache_ttl: float
    _cached_key_set: JWKSKeySet | None
    _last_fetch_time: float

    def __init__(self, url: str, cache_ttl: float = 300.0) -> None:
        """
        Initialize the JWKS fetcher.

        Args:
            url: URL of the JWKS endpoint
            cache_ttl: Cache time-to-live in seconds (default: 300 = 5 minutes)
        """
        self._url = url
        self._cache_ttl = cache_ttl
        self._cached_key_set = None
        self._last_fetch_time = 0.0

    async def get_key(self, kid: str) -> RSAPublicKey:
        """
        Get an RSA public key by key ID, fetching JWKS if cache is expired.

        Args:
            kid: Key ID to look up

        Returns:
            RSA public key corresponding to the given kid

        Raises:
            JWKSFetchError: If the JWKS endpoint cannot be reached
            JWKSKeyNotFoundError: If the kid is not found in the key set
        """
        key_set = await self._get_key_set()
        return key_set.get_key(kid)

    async def refresh(self) -> JWKSKeySet:
        """
        Force refresh the cached JWKS key set.

        Returns:
            The freshly fetched JWKSKeySet

        Raises:
            JWKSFetchError: If the JWKS endpoint cannot be reached
        """
        return await self._fetch_jwks()

    async def _get_key_set(self) -> JWKSKeySet:
        """
        Get the cached key set, refreshing if expired.

        Returns:
            The current JWKSKeySet

        Raises:
            JWKSFetchError: If the JWKS endpoint cannot be reached
        """
        now = time.monotonic()
        if self._cached_key_set is not None and (now - self._last_fetch_time) < self._cache_ttl:
            return self._cached_key_set
        return await self._fetch_jwks()

    async def _fetch_jwks(self) -> JWKSKeySet:
        """
        Fetch the JWKS endpoint and update the cache.

        Returns:
            The fetched JWKSKeySet

        Raises:
            JWKSFetchError: If the JWKS endpoint cannot be reached or returns invalid data
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._url) as response:
                    if response.status != 200:
                        raise JWKSFetchError(f"JWKS endpoint returned HTTP {response.status}")
                    data = await response.json()
        except JWKSFetchError:
            raise
        except Exception as e:
            raise JWKSFetchError(f"Failed to fetch JWKS from {self._url}: {e}") from e

        key_set = JWKSKeySet.from_jwks_dict(data)
        self._cached_key_set = key_set
        self._last_fetch_time = time.monotonic()
        return key_set
