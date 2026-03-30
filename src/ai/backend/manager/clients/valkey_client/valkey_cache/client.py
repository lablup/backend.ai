"""Valkey cache client for manager."""

from __future__ import annotations

import logging

from glide import GlideClient

from ai.backend.common.clients.valkey_client.client import AbstractValkeyClient
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ValkeyCache:
    """
    Valkey cache client for manager-level caching operations.
    Provides direct access to Glide client for cache operations.
    """

    _client: AbstractValkeyClient

    def __init__(
        self,
        client: AbstractValkeyClient,
    ) -> None:
        """
        Initialize the Valkey cache client.

        Args:
            client: Abstract Valkey client
        """
        self._client = client

    @classmethod
    async def create(
        cls,
        client: AbstractValkeyClient,
    ) -> ValkeyCache:
        """
        Create a ValkeyCache instance.

        Args:
            client: Abstract Valkey client

        Returns:
            ValkeyCache instance
        """
        return cls(client)

    @property
    def client(self) -> GlideClient:
        """Get the underlying Glide client for direct cache operations."""
        return self._client.client
