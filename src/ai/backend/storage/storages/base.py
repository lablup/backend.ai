import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Self

from ai.backend.common.types import StreamReader
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.config.unified import (
    StorageProxyUnifiedConfig,
)
from ai.backend.storage.exception import NotImplementedAPI

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractStorage(ABC):
    @abstractmethod
    async def stream_upload(
        self,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        raise NotImplementedAPI

    @abstractmethod
    async def stream_download(self, filepath: str) -> StreamReader:
        raise NotImplementedAPI

    @abstractmethod
    async def delete_object(self, filepath: str) -> None:
        raise NotImplementedAPI

    @abstractmethod
    # TODO: Make return type
    async def get_object_info(self, filepath: str) -> Any:
        raise NotImplementedAPI


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

        # Add Object Storage instances
        from ai.backend.storage.storages.object_storage import ObjectStorage

        for storage_config in config.storages:
            log.info(f"Adding object storage: {storage_config.name} ({storage_config.endpoint})")
            storages[storage_config.name] = ObjectStorage(storage_config)

        # Add VFS Storage instances
        from ai.backend.storage.storages.vfs import VFSStorage

        for vfs_config in config.vfs_storages:
            log.info(f"Adding VFS storage: {vfs_config.name} ({vfs_config.base_path})")
            storages[vfs_config.name] = VFSStorage(vfs_config)

        # Add Composite Storage instances
        from ai.backend.storage.storages.composite import SequenceCompositeStorage

        for composite_config in config.composite_storages:
            log.info(
                f"Adding composite storage: {composite_config.name} (primary: {composite_config.primary})"
            )

            # Get primary storage
            primary_storage = storages.get(composite_config.primary)
            if primary_storage is None:
                raise KeyError(
                    f"Primary storage '{composite_config.primary}' not found for composite storage '{composite_config.name}'"
                )

            # Get secondary storages
            secondary_storages = []
            for secondary_name in composite_config.secondary:
                secondary_storage = storages.get(secondary_name)
                if secondary_storage is None:
                    raise KeyError(
                        f"Secondary storage '{secondary_name}' not found for composite storage '{composite_config.name}'"
                    )
                secondary_storages.append(secondary_storage)

            # Create composite storage
            storages[composite_config.name] = SequenceCompositeStorage(
                name=composite_config.name,
                primary_storage=primary_storage,
                secondary_storages=secondary_storages,
            )

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
