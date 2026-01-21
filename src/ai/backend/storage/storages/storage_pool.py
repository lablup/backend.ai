import logging
from typing import Optional, Self, override

from ai.backend.common.artifact_storage import AbstractStorage, AbstractStoragePool
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.exception import GenericNotImplementedError, InvalidConfigError
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.config.unified import (
    StorageProxyUnifiedConfig,
)
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.vfs_storage import VFSStorage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StoragePool(AbstractStoragePool):
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
            log.debug(
                f"Adding object storage: {legacy_storage_config.name} ({legacy_storage_config.endpoint})"
            )
            storages[legacy_storage_config.name] = ObjectStorage(
                legacy_storage_config.name, legacy_storage_config
            )

        # Add Storage instances
        for storage_name, artifact_storage_config in config.artifact_storages.items():
            match artifact_storage_config.storage_type:
                case ArtifactStorageType.VFS_STORAGE:
                    if artifact_storage_config.vfs_storage is None:
                        raise InvalidConfigError(
                            "vfs_storage config is required when storage_type is 'vfs_storage'"
                        )
                    log.info(
                        f"Adding VFS storage: {storage_name} ({artifact_storage_config.vfs_storage.base_path})"
                    )
                    storages[storage_name] = VFSStorage(
                        storage_name, artifact_storage_config.vfs_storage
                    )

                case ArtifactStorageType.OBJECT_STORAGE:
                    if artifact_storage_config.object_storage is None:
                        raise InvalidConfigError(
                            "object_storage config is required when storage_type is 'object_storage'"
                        )
                    log.debug(
                        f"Adding object storage: {storage_name} ({artifact_storage_config.object_storage.endpoint})"
                    )
                    storages[storage_name] = ObjectStorage(
                        storage_name, artifact_storage_config.object_storage
                    )

                case ArtifactStorageType.GIT_LFS:
                    raise GenericNotImplementedError("Git LFS storage is not supported yet")

        return cls(storages)

    @override
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

    @override
    def add_storage(self, name: str, storage: AbstractStorage) -> None:
        """
        Add a storage to the pool.

        Args:
            name: Name of the storage
            storage: Storage instance
        """
        self._storages[name] = storage

    @override
    def remove_storage(self, name: str) -> None:
        """
        Remove a storage from the pool.

        Args:
            name: Name of the storage to remove
        """
        if name in self._storages:
            del self._storages[name]

    @override
    def list_storages(self) -> list[str]:
        """
        List all storage names in the pool.

        Returns:
            List of storage names
        """
        return list(self._storages.keys())

    @override
    def has_storage(self, name: str) -> bool:
        """
        Check if storage exists in the pool.

        Args:
            name: Name of the storage

        Returns:
            True if storage exists
        """
        return name in self._storages

    def cleanup_temporary_storages(self) -> None:
        """
        Clean up all temporary VFS storages.
        This should be called only by the first process (pidx=0) on server startup.
        """

        for storage in self._storages.values():
            if isinstance(storage, VFSStorage):
                storage.cleanup_temporary_storage()
