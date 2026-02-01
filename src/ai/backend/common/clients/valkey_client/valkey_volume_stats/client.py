"""Valkey client for volume stats caching operations."""

from __future__ import annotations

import logging
from typing import Final, Self

from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    BackoffStrategy,
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Resilience instance for valkey_volume_stats layer
valkey_volume_stats_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_VOLUME_STATS)),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)

_CACHE_KEY_PREFIX: Final[str] = "storage:volume_stats"


class ValkeyVolumeStatsClient:
    """
    Client for managing volume stats cache using Valkey.

    This client handles storing and retrieving cached volume performance metrics.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
    ) -> Self:
        """
        Create a ValkeyVolumeStatsClient instance.

        :param valkey_target: The target Valkey server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The name of the client.
        :return: An instance of ValkeyVolumeStatsClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_volume_stats_resilience.apply()
    async def close(self) -> None:
        """Close the ValkeyVolumeStatsClient connection."""
        if self._closed:
            log.debug("ValkeyVolumeStatsClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    async def ping(self) -> None:
        """Ping the Valkey server to check connection health."""
        await self._client.ping()

    def _make_cache_key(self, volume_name: str) -> str:
        """
        Generate cache key for a volume.

        :param volume_name: The volume name.
        :return: The generated cache key.
        """
        return f"{_CACHE_KEY_PREFIX}:{volume_name}"

    @valkey_volume_stats_resilience.apply()
    async def get_volume_stats(self, volume_name: str) -> bytes | None:
        """
        Get cached volume stats data.

        :param volume_name: The volume name.
        :return: The cached JSON data as bytes, or None if not found.
        """
        key = self._make_cache_key(volume_name)
        return await self._client.client.get(key)

    @valkey_volume_stats_resilience.apply()
    async def set_volume_stats(
        self,
        volume_name: str,
        data: str,
        ttl_seconds: int,
    ) -> None:
        """
        Cache volume stats data with TTL.

        :param volume_name: The volume name.
        :param data: The JSON data to cache.
        :param ttl_seconds: TTL in seconds.
        """
        key = self._make_cache_key(volume_name)
        await self._client.client.set(
            key,
            data,
            expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
        )
