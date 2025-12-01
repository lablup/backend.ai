from __future__ import annotations

import logging
import uuid
from typing import Optional, Self, TypeVar

from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.data.artifact_registry.types import ArtifactRegistryStatefulData
from ai.backend.common.exception import BackendAIError
from ai.backend.common.json import dump_json_str, load_json
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

# Resilience instance for valkey_artifact_registries layer
valkey_artifact_registries_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_ARTIFACT_REGISTRIES)
        ),
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

_EXPIRATION = 60 * 60 * 24  # 24 hours

T = TypeVar("T", bound=ArtifactRegistryStatefulData)


class ValkeyArtifactRegistryClient:
    """
    Client for caching artifact registry information using Valkey.

    This client stores each registry as an individual key with independent expiry:
    - Key format: artifact_registries.{registry_id}
    - Value: JSON serialized registry data
    - Each key has its own TTL for independent expiry management
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
        Create a ValkeyArtifactRegistryClient instance.

        :param valkey_target: The target Valkey server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name of the client.
        :return: An instance of ValkeyArtifactRegistryClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_artifact_registries_resilience.apply()
    async def close(self) -> None:
        """
        Close the ValkeyArtifactRegistryClient connection.
        """
        if self._closed:
            log.debug("ValkeyArtifactRegistryClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    async def ping(self) -> None:
        """Ping the Valkey server to check connection health."""
        await self._client.ping()

    def _make_registry_key(self, registry_id: uuid.UUID) -> str:
        """
        Generate a cache key for individual artifact registry.

        :param registry_id: The UUID of the registry.
        :return: The formatted cache key.
        """
        return f"artifact_registries.{registry_id}"

    @valkey_artifact_registries_resilience.apply()
    async def set_registry(
        self,
        registry_id: uuid.UUID,
        registry_data: T,
    ) -> None:
        """
        Cache registry data with independent expiry.

        :param registry_id: The UUID of the registry.
        :param registry_data: The registry data to cache.
        """
        key = self._make_registry_key(registry_id)
        value = dump_json_str(registry_data.to_dict())
        await self._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, _EXPIRATION),
        )
        log.debug("Cached registry data for registry_id={}", registry_id)

    @valkey_artifact_registries_resilience.apply()
    async def get_registry(
        self,
        registry_id: uuid.UUID,
        data_class: type[T],
    ) -> Optional[T]:
        """
        Get cached registry data.

        :param registry_id: The UUID of the registry.
        :param data_class: The data class to deserialize into.
        :return: The cached registry data or None if not found.
        """
        key = self._make_registry_key(registry_id)
        value = await self._client.client.get(key)
        if value is None:
            log.debug("Cache miss for registry_id={}", registry_id)
            return None

        json_value = value.decode()
        data = load_json(json_value)
        return data_class.from_dict(data)

    @valkey_artifact_registries_resilience.apply()
    async def delete_registry(
        self,
        registry_id: uuid.UUID,
    ) -> bool:
        """
        Delete cached registry data.

        :param registry_id: The UUID of the registry.
        :return: True if the key was deleted, False otherwise.
        """
        key = self._make_registry_key(registry_id)
        result = await self._client.client.delete([key])
        deleted = result > 0
        if deleted:
            log.debug("Deleted cached registry data for registry_id={}", registry_id)
        return deleted

    @valkey_artifact_registries_resilience.apply()
    async def flush_database(self) -> None:
        """
        Flush all keys in the current database.
        """
        await self._client.client.flushdb()
