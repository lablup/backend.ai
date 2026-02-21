from __future__ import annotations

import logging
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    ValkeyArtifactRegistryClient,
)
from ai.backend.common.data.artifact_registry.types import HuggingFaceRegistryData
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class HuggingFaceStatefulSource:
    """
    Stateful source for HuggingFace registry operations.
    Provides access to cached registry data stored in Valkey.
    """

    _valkey_artifact_registry: ValkeyArtifactRegistryClient

    def __init__(self, valkey_artifact_registry: ValkeyArtifactRegistryClient) -> None:
        """
        Initialize HuggingFaceStatefulSource.

        :param valkey_artifact_registry: Valkey client for artifact registry operations.
        """
        self._valkey_artifact_registry = valkey_artifact_registry

    async def get_registry(self, registry_name: str) -> Optional[HuggingFaceRegistryData]:
        """
        Get cached HuggingFace registry data by registry name.

        :param registry_name: The name of the HuggingFace registry.
        :return: The cached registry data or None if not found.
        """
        return await self._valkey_artifact_registry.get_huggingface_registry(registry_name)

    async def set_registry(
        self,
        registry_name: str,
        registry_data: HuggingFaceRegistryData,
        expiration: int = 3600,
    ) -> None:
        """
        Cache HuggingFace registry data.

        :param registry_name: The name of the HuggingFace registry.
        :param registry_data: The registry data to cache.
        :param expiration: The cache expiration time in seconds (default: 1 hour).
        """
        await self._valkey_artifact_registry.set_huggingface_registry(
            registry_name, registry_data, expiration
        )

    async def delete_registry(self, registry_name: str) -> bool:
        """
        Delete cached HuggingFace registry data.

        :param registry_name: The name of the HuggingFace registry.
        :return: True if the key was deleted, False otherwise.
        """
        return await self._valkey_artifact_registry.delete_huggingface_registry(registry_name)
