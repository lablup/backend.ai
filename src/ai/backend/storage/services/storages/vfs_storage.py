import logging

from ai.backend.common.dto.storage.response import (
    VFSFileMetaResponse,
)
from ai.backend.common.types import StreamReader
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.exception import StorageNotFoundError, StorageTypeInvalidError
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.storages.vfs_storage import VFSStorage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFSStorageService:
    """
    Service class for VFS storage operations.
    Provides a service layer similar to ObjectStorageService but for VFS storage.
    """

    _storage_pool: StoragePool

    def __init__(self, storage_pool: StoragePool) -> None:
        self._storage_pool = storage_pool

    async def stream_upload(
        self,
        storage_name: str,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        """
        Upload a file to VFS using streaming.

        Args:
            storage_name: Name of the VFS storage configuration
            filepath: Path to the file to upload
            data_stream: Async iterator of file data chunks
        """
        storage = self._resolve_storage(storage_name)
        await storage.stream_upload(filepath, data_stream)

    async def stream_download(self, storage_name: str, filepath: str) -> StreamReader:
        """
        Download a file from VFS using streaming.

        Args:
            storage_name: Name of the VFS storage configuration
            filepath: Path to the file to download

        Returns:
            FileStream: Stream for reading file data
        """
        storage = self._resolve_storage(storage_name)
        return await storage.stream_download(filepath)

    async def get_file_meta(self, storage_name: str, filepath: str) -> VFSFileMetaResponse:
        """
        Get file information.

        Args:
            storage_name: Name of the VFS storage configuration
            filepath: Path to the file

        Returns:
            VFSFileMetaResponse with file metadata
        """
        storage = self._resolve_storage(storage_name)
        return await storage.get_object_info(filepath)

    async def delete_file(self, storage_name: str, filepath: str) -> None:
        """
        Delete a file or directory.

        Args:
            storage_name: Name of the VFS storage configuration
            filepath: Path to the file/directory to delete
        """
        storage = self._resolve_storage(storage_name)
        await storage.delete_object(filepath)

    async def list_files(self, storage_name: str, directory: str) -> list[dict]:
        """
        List files and directories in a directory.

        Args:
            storage_name: Name of the VFS storage configuration
            directory: Directory path to list

        Returns:
            List of file/directory information
        """
        storage = self._resolve_storage(storage_name)
        return await storage.list_directory(directory)

    async def create_directory(self, storage_name: str, directory: str) -> None:
        """
        Create a directory.

        Args:
            storage_name: Name of the VFS storage configuration
            directory: Directory path to create
        """
        storage = self._resolve_storage(storage_name)
        await storage.create_directory(directory)

    async def get_disk_usage(self, storage_name: str) -> dict:
        """
        Get disk usage information for the storage.

        Args:
            storage_name: Name of the VFS storage configuration

        Returns:
            Dictionary with capacity and used bytes information
        """
        storage = self._resolve_storage(storage_name)
        return await storage.get_disk_usage()

    def _resolve_storage(self, storage_name: str) -> VFSStorage:
        """
        Resolve VFS storage by name from storage pool.

        Args:
            storage_name: Name of the VFS storage configuration

        Returns:
            VFSStorage instance

        Raises:
            StorageNotFoundError: If storage is not found or not a VFS storage
        """
        try:
            storage = self._storage_pool.get_storage(storage_name)
            if not isinstance(storage, VFSStorage):
                raise StorageTypeInvalidError(f"Storage '{storage_name}' is not a VFS storage")
            return storage
        except KeyError:
            raise StorageNotFoundError(f"No VFS storage configuration found for: {storage_name}")
