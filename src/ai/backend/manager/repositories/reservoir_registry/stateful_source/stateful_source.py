from __future__ import annotations

import logging
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    ValkeyArtifactRegistryClient,
)
from ai.backend.common.data.artifact_registry.types import ReservoirRegistrySharedData
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

    def to_dataclass(self, data: ReservoirRegistryData) -> ReservoirRegistrySharedData:
        """Convert ReservoirRegistryData to ReservoirRegistrySharedData."""
        return ReservoirRegistrySharedData(
            id=data.id,
            name=data.name,
            endpoint=data.endpoint,
            access_key=data.access_key,
            secret_key=data.secret_key,
            api_version=data.api_version,
        )

    def from_dataclass(self, data: ReservoirRegistrySharedData) -> ReservoirRegistryData:
        """Convert ReservoirRegistrySharedData to ReservoirRegistryData."""
        return ReservoirRegistryData(
            id=data.id,
            name=data.name,
            endpoint=data.endpoint,
            access_key=data.access_key,
            secret_key=data.secret_key,
            api_version=data.api_version,
        )

    async def get_registry(self, registry_name: str) -> Optional[ReservoirRegistryData]:
        """
        Get cached Reservoir registry data by registry name.

        :param registry_name: The name of the Reservoir registry.
        :return: The cached registry data or None if not found.
        """
        shared_data = await self._valkey_artifact_registry.get_reservoir_registry(registry_name)
        return self.from_dataclass(shared_data) if shared_data is not None else None

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
        shared_data = self.to_dataclass(registry_data)
        await self._valkey_artifact_registry.set_reservoir_registry(
            registry_name, shared_data, expiration
        )

    async def delete_registry(self, registry_name: str) -> bool:
        """
        Delete cached Reservoir registry data.

        :param registry_name: The name of the Reservoir registry.
        :return: True if the key was deleted, False otherwise.
        """
        return await self._valkey_artifact_registry.delete_reservoir_registry(registry_name)
