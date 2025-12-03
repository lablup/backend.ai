from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from typing import Optional

from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    ValkeyArtifactRegistryClient,
)
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReservoirStatefulSource:
    """
    Stateful source for Reservoir registry operations.
    Provides access to cached registry data stored in Valkey.
    """

    _valkey_artifact_registry: ValkeyArtifactRegistryClient

    def __init__(self, valkey_artifact_registry: ValkeyArtifactRegistryClient) -> None:
        """
        Initialize ReservoirStatefulSource.

        :param valkey_artifact_registry: Valkey client for artifact registry operations.
        """
        self._valkey_artifact_registry = valkey_artifact_registry

    def _make_cache_key(self, registry_name: str) -> str:
        """Generate cache key for reservoir registry by name."""
        return f"artifact_registries.reservoir.{registry_name}"

    async def get_registry(self, registry_name: str) -> Optional[ReservoirRegistryData]:
        """
        Get cached Reservoir registry data by registry name.

        :param registry_name: The name of the Reservoir registry.
        :return: The cached registry data or None if not found.
        """
        key = self._make_cache_key(registry_name)
        value = await self._valkey_artifact_registry._client.client.get(key)
        if value is None:
            return None

        data = load_json(value.decode())
        # Convert string UUID back to UUID
        if isinstance(data.get("id"), str):
            data["id"] = uuid.UUID(data["id"])
        return ReservoirRegistryData(**data)

    async def set_registry(
        self,
        registry_name: str,
        registry_data: ReservoirRegistryData,
        expiration: int = 3600,
    ) -> None:
        """
        Cache Reservoir registry data.

        :param registry_name: The name of the Reservoir registry.
        :param registry_data: The registry data to cache.
        :param expiration: The cache expiration time in seconds (default: 1 hour).
        """
        key = self._make_cache_key(registry_name)
        data = asdict(registry_data)
        # Convert UUID to string for JSON serialization
        data["id"] = str(data["id"])
        value = dump_json_str(data)
        await self._valkey_artifact_registry._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, expiration),
        )

    async def delete_registry(self, registry_name: str) -> bool:
        """
        Delete cached Reservoir registry data.

        :param registry_name: The name of the Reservoir registry.
        :return: True if the key was deleted, False otherwise.
        """
        key = self._make_cache_key(registry_name)
        result = await self._valkey_artifact_registry._client.client.delete([key])
        return result > 0
