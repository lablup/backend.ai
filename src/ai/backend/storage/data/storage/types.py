from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ai.backend.common.artifact_storage import AbstractStorage, AbstractStoragePool
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.common.dto.storage.request import StorageMappingResolverData, VFolderStorageTarget
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.storages.volume_adapter import VolumeStorageAdapter

if TYPE_CHECKING:
    from ai.backend.storage.volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StorageTarget:
    """
    Wrapper for storage step mapping that can be either a storage name (str)
    or a storage instance (AbstractStorage).

    When str: resolved via storage_pool.get_storage(name)
    When AbstractStorage: used directly (e.g., VolumeStorageAdapter for VFolder imports)
    """

    _value: str | AbstractStorage

    def __init__(self, value: str | AbstractStorage) -> None:
        self._value = value

    @property
    def name(self) -> str:
        """Get the storage name from this mapping."""
        if isinstance(self._value, str):
            return self._value
        return self._value.name

    def resolve_storage(self, storage_pool: AbstractStoragePool) -> AbstractStorage:
        """
        Resolve this mapping to an AbstractStorage instance.

        Args:
            storage_pool: The storage pool to look up string mappings

        Returns:
            The resolved AbstractStorage instance
        """
        if isinstance(self._value, AbstractStorage):
            return self._value
        return storage_pool.get_storage(self._value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StorageTarget):
            return self._value == other._value
        return False

    def __hash__(self) -> int:
        if isinstance(self._value, str):
            return hash(self._value)
        return id(self._value)


@dataclass
class ImportStepContext:
    """Context shared across import steps"""

    model: ModelTarget
    registry_name: str
    storage_pool: AbstractStoragePool
    storage_step_mappings: dict[ArtifactStorageImportStep, StorageTarget]
    step_metadata: dict[str, Any]


class StorageMappingResolver:
    """
    Resolves raw storage step mappings to StorageTarget objects,
    optionally wrapping with VolumeStorageAdapter when vfolder_id is provided.
    """

    def __init__(
        self,
        volume_pool: VolumePool,
        storage_step_mappings: StorageMappingResolverData,
    ) -> None:
        self._volume_pool = volume_pool
        self._storage_step_mappings = storage_step_mappings

    def resolve(self) -> dict[ArtifactStorageImportStep, StorageTarget]:
        """
        Resolve storage targets to StorageTarget objects.

        For each import step:
        - If target is str: creates StorageTarget with storage name
        - If target is VFolderStorageTarget: creates StorageTarget with VolumeStorageAdapter

        Returns:
            Dict mapping import steps to StorageTarget objects
        """
        result: dict[ArtifactStorageImportStep, StorageTarget] = {}

        for step, target in self._storage_step_mappings.storage_step_mappings.items():
            if isinstance(target, VFolderStorageTarget):
                adapter_name = f"volume_storage_{step}_{current_request_id()}"
                volume = self._volume_pool.get_volume_by_name_direct(target.volume_name)
                adapter = VolumeStorageAdapter(
                    name=adapter_name,
                    volume=volume,
                    vfolder_id=target.vfolder_id,
                )

                log.info(
                    "Created VolumeStorageAdapter: name={}, vfolder_id={}, volume_name={}, volume_type={}",
                    adapter_name,
                    target.vfolder_id,
                    target.volume_name,
                    type(volume).__name__,
                )

                result[step] = StorageTarget(adapter)
            else:
                result[step] = StorageTarget(target)

        return result
