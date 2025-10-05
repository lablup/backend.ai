import logging
from typing import Optional, Self

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.exception import GenericNotImplementedError, InvalidConfigError
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.config.unified import (
    StorageProxyUnifiedConfig,
)
from ai.backend.storage.storages.base import AbstractStorage
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.vfs_storage import VFSStorage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StoragePool:
    """
    Storage pool that manages different types of storage backends.
    Supports both Object Storage (S3-compatible) and VFS storage.
    """

    _storages: dict[str, AbstractStorage]

    def __init__(self, storages: Optional[dict[str, AbstractStorage]] = None) -> None:
        self._storages = storages or {}

    @classmethod
    def from_config(cls, config: StorageProxyUnifiedConfig) -> Self:
        """
        Create StoragePool from configuration.

        Args:
            config: Unified storage proxy configuration

        Returns:
            StoragePool instance with all configured storages
        """
        storages: dict[str, AbstractStorage] = {}

        # Add Legacy Object Storage instances
        for legacy_storage_config in config.storages:
            log.info(
                f"Adding object storage: {legacy_storage_config.name} ({legacy_storage_config.endpoint})"
            )
            storages[legacy_storage_config.name] = ObjectStorage(
                legacy_storage_config.name, legacy_storage_config
            )

        # Add Storage instances
        for storage_name, artifact_storage_config in config.artifact_storages.items():
            match artifact_storage_config.storage_type:
                case ArtifactStorageType.VFS:
                    if artifact_storage_config.vfs is None:
                        raise InvalidConfigError(
                            "vfs config is required when storage_type is 'vfs'"
                        )
                    log.info(
                        f"Adding VFS storage: {storage_name} ({artifact_storage_config.vfs.base_path})"
                    )
                    storages[storage_name] = VFSStorage(storage_name, artifact_storage_config.vfs)

                case ArtifactStorageType.OBJECT_STORAGE:
                    if artifact_storage_config.object_storage is None:
                        raise InvalidConfigError(
                            "object_storage config is required when storage_type is 'object_storage'"
                        )
                    log.info(
                        f"Adding object storage: {storage_name} ({artifact_storage_config.object_storage.endpoint})"
                    )
                    storages[storage_name] = ObjectStorage(
                        storage_name, artifact_storage_config.object_storage
                    )

                case ArtifactStorageType.GIT_LFS:
                    raise GenericNotImplementedError("Git LFS storage is not supported yet")

        return cls(storages)

    def get_storage(self, name: str) -> AbstractStorage:
        """
        Get storage by name.

        Args:
            name: Name of the storage configuration

        Returns:
            AbstractStorage instance

        Raises:
            KeyError: If storage with given name is not found
        """
        return self._storages[name]

    def add_storage(self, name: str, storage: AbstractStorage) -> None:
        """
        Add a storage to the pool.

        Args:
            name: Name of the storage
            storage: Storage instance
        """
        self._storages[name] = storage

    def remove_storage(self, name: str) -> None:
        """
        Remove a storage from the pool.

        Args:
            name: Name of the storage to remove
        """
        if name in self._storages:
            del self._storages[name]

    def list_storages(self) -> list[str]:
        """
        List all storage names in the pool.

        Returns:
            List of storage names
        """
        return list(self._storages.keys())

    def has_storage(self, name: str) -> bool:
        """
        Check if storage exists in the pool.

        Args:
            name: Name of the storage

        Returns:
            True if storage exists
        """
        return name in self._storages
