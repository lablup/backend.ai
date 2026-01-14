from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ai.backend.common.artifact_storage import AbstractStorage, AbstractStoragePool
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.errors.common import InvalidStorageTargetError

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StorageTarget:
    """
    Wrapper for storage step mapping that can be either a storage name (str)
    or a storage instance (AbstractStorage).

    When str: resolved via storage_pool.get_storage(name)
    When AbstractStorage: used directly (e.g., VolumeStorageAdapter for VFolder imports)

    Use class methods to create instances:
        - StorageTarget.from_storage_name(name) for string-based storage names
        - StorageTarget.from_storage(storage) for AbstractStorage instances
    """

    _storage_name: str | None
    _storage: AbstractStorage | None

    def __init__(
        self,
        storage_name: str | None = None,
        storage: AbstractStorage | None = None,
    ) -> None:
        if storage_name is None and storage is None:
            raise InvalidStorageTargetError("Either storage_name or storage must be provided")
        if storage_name is not None and storage is not None:
            raise InvalidStorageTargetError(
                "Only one of storage_name or storage should be provided"
            )
        self._storage_name = storage_name
        self._storage = storage

    @classmethod
    def from_storage_name(cls, name: str) -> StorageTarget:
        """Create a StorageTarget from a storage name."""
        return cls(storage_name=name)

    @classmethod
    def from_storage(cls, storage: AbstractStorage) -> StorageTarget:
        """Create a StorageTarget from an AbstractStorage instance."""
        return cls(storage=storage)

    @property
    def name(self) -> str:
        """Get the storage name from this mapping."""
        if self._storage_name is not None:
            return self._storage_name
        if self._storage is None:
            raise InvalidStorageTargetError("StorageTarget has no storage_name or storage")
        return self._storage.name

    def resolve_storage(self, storage_pool: AbstractStoragePool) -> AbstractStorage:
        """
        Resolve this mapping to an AbstractStorage instance.

        Args:
            storage_pool: The storage pool to look up string mappings

        Returns:
            The resolved AbstractStorage instance
        """
        if self._storage is not None:
            return self._storage
        if self._storage_name is None:
            raise InvalidStorageTargetError("StorageTarget has no storage_name or storage")
        return storage_pool.get_storage(self._storage_name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StorageTarget):
            if self._storage_name is not None and other._storage_name is not None:
                return self._storage_name == other._storage_name
            if self._storage is not None and other._storage is not None:
                return self._storage is other._storage
            return False
        return False

    def __hash__(self) -> int:
        if self._storage_name is not None:
            return hash(self._storage_name)
        if self._storage is None:
            raise InvalidStorageTargetError("StorageTarget has no storage_name or storage")
        return id(self._storage)


@dataclass
class ImportStepContext:
    """Context shared across import steps"""

    model: ModelTarget
    registry_name: str
    storage_pool: AbstractStoragePool
    storage_step_mappings: dict[ArtifactStorageImportStep, StorageTarget]
    step_metadata: dict[str, Any]
