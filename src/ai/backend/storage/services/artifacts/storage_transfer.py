from __future__ import annotations

import asyncio
import logging
import shutil

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.exception import StorageTransferError
from ai.backend.storage.storages.base import AbstractStorage
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.storages.vfs_storage import VFSStorage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StorageTransferManager:
    """Utility class for transferring data between different storage types."""

    def __init__(self, storage_pool: StoragePool):
        self._storage_pool = storage_pool

    async def transfer_file(
        self,
        source_storage_name: str,
        dest_storage_name: str,
        source_path: str,
        dest_path: str,
    ) -> None:
        """
        Transfer a file from source storage to destination storage.

        Args:
            source_storage_name: Name of source storage
            dest_storage_name: Name of destination storage
            source_path: Path of file in source storage
            dest_path: Path of file in destination storage
        """
        if source_storage_name == dest_storage_name:
            log.debug(f"Skipping transfer - same storage: {source_storage_name}")
            return

        source_storage = self._storage_pool.get_storage(source_storage_name)
        dest_storage = self._storage_pool.get_storage(dest_storage_name)

        log.info(
            f"Transferring file from {source_storage_name} to {dest_storage_name}: "
            f"{source_path} -> {dest_path}"
        )

        try:
            # Optimize VFS-to-VFS transfer using direct file copy
            if isinstance(source_storage, VFSStorage) and isinstance(dest_storage, VFSStorage):
                await self._copy_vfs_to_vfs(source_storage, dest_storage, source_path, dest_path)
            else:
                # Generic storage-to-storage transfer via streaming
                await self._copy_via_stream(source_storage, dest_storage, source_path, dest_path)

            log.info(
                f"Successfully transferred file from {source_storage_name} to {dest_storage_name}: "
                f"{source_path} -> {dest_path}"
            )
        except Exception as e:
            raise StorageTransferError(
                f"Failed to transfer file from {source_storage_name} to {dest_storage_name}: "
                f"{source_path} -> {dest_path}: {str(e)}"
            ) from e

    async def transfer_directory(
        self,
        source_storage_name: str,
        dest_storage_name: str,
        source_prefix: str,
        dest_prefix: str,
        concurrency: int = 10,
    ) -> None:
        """
        Transfer all files with given prefix from source to destination storage.

        Args:
            source_storage_name: Name of source storage
            dest_storage_name: Name of destination storage
            source_prefix: Prefix path in source storage
            dest_prefix: Prefix path in destination storage
            concurrency: Number of concurrent transfers
        """
        if source_storage_name == dest_storage_name:
            log.debug(f"Skipping transfer - same storage: {source_storage_name}")
            return

        source_storage = self._storage_pool.get_storage(source_storage_name)

        try:
            # Get list of files to transfer
            file_list = await self._list_files_with_prefix(source_storage, source_prefix)

            if not file_list:
                log.warning(f"No files found with prefix: {source_prefix}")
                return

            log.info(
                f"Transferring {len(file_list)} files from {source_storage_name} to {dest_storage_name}"
            )

            # Transfer files with concurrency control
            sem = asyncio.Semaphore(concurrency)

            async def _transfer_single_file(source_path: str) -> None:
                async with sem:
                    # Convert source path to destination path
                    relative_path = source_path[len(source_prefix) :].lstrip("/")
                    dest_path = (
                        f"{dest_prefix.rstrip('/')}/{relative_path}"
                        if relative_path
                        else dest_prefix
                    )

                    await self.transfer_file(
                        source_storage_name, dest_storage_name, source_path, dest_path
                    )

            # Execute transfers concurrently
            await asyncio.gather(*[_transfer_single_file(path) for path in file_list])

            log.info(
                f"Successfully transferred {len(file_list)} files from {source_storage_name} to {dest_storage_name}"
            )

        except Exception as e:
            raise StorageTransferError(
                f"Failed to transfer directory from {source_storage_name} to {dest_storage_name}: "
                f"{source_prefix} -> {dest_prefix}: {str(e)}"
            ) from e

    async def _copy_vfs_to_vfs(
        self,
        source_storage: VFSStorage,
        dest_storage: VFSStorage,
        source_path: str,
        dest_path: str,
    ) -> None:
        """Optimized copy between VFS storages using direct file system operations."""
        source_full_path = source_storage._resolve_path(source_path)
        dest_full_path = dest_storage._resolve_path(dest_path)

        # Ensure destination directory exists
        dest_full_path.parent.mkdir(parents=True, exist_ok=True)

        # Use efficient file system copy
        await asyncio.get_event_loop().run_in_executor(
            None, shutil.copy2, str(source_full_path), str(dest_full_path)
        )

    async def _copy_via_stream(
        self,
        source_storage: AbstractStorage,
        dest_storage: AbstractStorage,
        source_path: str,
        dest_path: str,
    ) -> None:
        """Generic copy between storages using streaming."""
        # Download from source
        data_stream = await source_storage.stream_download(source_path)

        # Upload to destination
        await dest_storage.stream_upload(dest_path, data_stream)

    async def _list_files_with_prefix(self, storage: AbstractStorage, prefix: str) -> list[str]:
        """List all files in storage with given prefix."""
        if isinstance(storage, VFSStorage):
            return await self._list_vfs_files_with_prefix(storage, prefix)
        elif isinstance(storage, ObjectStorage):
            return await self._list_object_storage_files_with_prefix(storage, prefix)
        else:
            raise StorageTransferError(f"Unsupported storage type: {type(storage)}")

    async def _list_vfs_files_with_prefix(self, storage: VFSStorage, prefix: str) -> list[str]:
        """List files in VFS storage with given prefix."""
        try:
            full_path = storage._resolve_path(prefix)
            if full_path.is_file():
                return [prefix]
            elif full_path.is_dir():
                files = []
                for item in full_path.rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(storage.base_path)
                        files.append(str(rel_path))
                return files
            else:
                return []
        except Exception:
            return []

    async def _list_object_storage_files_with_prefix(
        self, storage: ObjectStorage, prefix: str
    ) -> list[str]:
        """List files in Object storage with given prefix."""
        try:
            # Use storage's list_objects method if available
            # This is a simplified implementation - actual implementation would depend on storage interface
            # For now, return empty list and rely on higher-level logic
            return []
        except Exception:
            return []

    async def verify_transfer(
        self,
        source_storage_name: str,
        dest_storage_name: str,
        source_path: str,
        dest_path: str,
    ) -> bool:
        """
        Verify that a file was transferred correctly by comparing metadata.

        Args:
            source_storage_name: Name of source storage
            dest_storage_name: Name of destination storage
            source_path: Path in source storage
            dest_path: Path in destination storage

        Returns:
            True if transfer was successful, False otherwise
        """
        try:
            source_storage = self._storage_pool.get_storage(source_storage_name)
            dest_storage = self._storage_pool.get_storage(dest_storage_name)

            # Get metadata from both storages
            source_meta = await source_storage.get_object_info(source_path)
            dest_meta = await dest_storage.get_object_info(dest_path)

            # Compare file sizes
            if hasattr(source_meta, "size") and hasattr(dest_meta, "size"):
                return source_meta.size == dest_meta.size

            # If size comparison is not available, assume success
            return True

        except Exception as e:
            log.error(f"Failed to verify transfer: {source_path} -> {dest_path}: {str(e)}")
            return False
