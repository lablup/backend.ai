from __future__ import annotations

import logging
import uuid

from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    ValkeyArtifactRegistryClient,
)
from ai.backend.common.data.artifact_registry.types import ReservoirRegistryStatefulData
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError

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

    async def get_registry(self, registry_id: uuid.UUID) -> ReservoirRegistryStatefulData:
        """
        Get cached Reservoir registry data by registry ID.

        Stateful view assumes the value always exists in cache.
        If not found, raises an error.

        :param registry_id: The UUID of the artifact registry.
        :return: The cached registry data.
        :raises ArtifactRegistryNotFoundError: If the registry is not found in cache.
        """
        data = await self._valkey_artifact_registry.get_registry(registry_id)
        if data is None:
            raise ArtifactRegistryNotFoundError(
                f"Reservoir registry with ID '{registry_id}' not found in cache"
            )

        return ReservoirRegistryStatefulData.from_dict(data)

    async def set_registry(
        self,
        registry_data: ReservoirRegistryStatefulData,
    ) -> None:
        """
        Cache Reservoir registry data.

        :param registry_data: The registry data to cache.
        """
        data = registry_data.to_dict()
        await self._valkey_artifact_registry.set_registry(
            registry_id=registry_data.id,
            registry_data=data,
        )

    async def delete_registry(self, registry_id: uuid.UUID) -> bool:
        """
        Delete cached Reservoir registry data.

        :param registry_id: The UUID of the artifact registry.
        :return: True if the key was deleted, False otherwise.
        """
        return await self._valkey_artifact_registry.delete_registry(registry_id)
