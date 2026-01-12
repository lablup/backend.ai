from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ai.backend.common.artifact_storage import AbstractStorage, AbstractStoragePool
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.logging import BraceStyleAdapter

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
