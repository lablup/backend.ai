from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path

from ai.backend.common.artifact_storage import AbstractStorage, AbstractStoragePool
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.data.storage.types import StorageTarget
from ai.backend.storage.errors import StorageTransferError
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.vfs_storage import VFSStorage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StorageTransferManager:
    """
    Manages transferring files between different artifact storage backends.
    """

    def __init__(self, storage_pool: AbstractStoragePool) -> None:
        self._storage_pool = storage_pool

    async def transfer_file(
        self,
        source_storage: StorageTarget,
        dest_storage: StorageTarget,
        source_path: str,
        dest_path: str,
    ) -> None:
        """
        Transfer a file from source storage to destination storage.

        Args:
            source_storage: Source storage (name or instance)
            dest_storage: Destination storage (name or instance)
            source_path: Path of file in source storage
            dest_path: Path of file in destination storage
        """
        source_storage_name = source_storage.name
        dest_storage_name = dest_storage.name

        if source_storage_name == dest_storage_name:
            log.debug("Skipping transfer - same storage: {}", source_storage_name)
            return

        resolved_source = source_storage.resolve_storage(self._storage_pool)
        resolved_dest = dest_storage.resolve_storage(self._storage_pool)

        log.info(
            "Transferring file from {} to {}: {} -> {}",
            source_storage_name,
            dest_storage_name,
            source_path,
            dest_path,
        )

        try:
            # Optimize VFS-to-VFS transfer using direct file move
            if isinstance(resolved_source, VFSStorage) and isinstance(resolved_dest, VFSStorage):
                await self._move_vfs_to_vfs(resolved_source, resolved_dest, source_path, dest_path)
            else:
                # Generic storage-to-storage transfer via streaming
                await self._copy_via_stream(resolved_source, resolved_dest, source_path, dest_path)

            log.info(
                "Successfully transferred file from {} to {}: {} -> {}",
                source_storage_name,
                dest_storage_name,
                source_path,
                dest_path,
            )
        except Exception as e:
            raise StorageTransferError(
                f"Failed to transfer file from {source_storage_name} to {dest_storage_name}: "
                f"{source_path} -> {dest_path}: {e!s}"
            ) from e

    async def transfer_directory(
        self,
        source_storage: StorageTarget,
        dest_storage: StorageTarget,
        source_prefix: str,
        dest_prefix: str,
        concurrency: int = 10,
    ) -> int:
        """
        Transfer all files with given prefix from source to destination storage.

        Args:
            source_storage: Source storage (name or instance)
            dest_storage: Destination storage (name or instance)
            source_prefix: Prefix path in source storage
            dest_prefix: Prefix path in destination storage
            concurrency: Number of concurrent transfers
        """
        source_storage_name = source_storage.name
        dest_storage_name = dest_storage.name

        if source_storage_name == dest_storage_name:
            log.debug("Skipping transfer - same storage: {}", source_storage_name)
            return 0

        resolved_source = source_storage.resolve_storage(self._storage_pool)
        resolved_dest = dest_storage.resolve_storage(self._storage_pool)

        try:
            # VFS-to-VFS: move entire directory at once (no empty directory cleanup needed)
            if isinstance(resolved_source, VFSStorage) and isinstance(resolved_dest, VFSStorage):
                file_count = len(await self._list_files_with_prefix(resolved_source, source_prefix))
                if file_count == 0:
                    log.warning("No files found with prefix: {}", source_prefix)
                    return 0

                await self._move_vfs_directory(
                    resolved_source, resolved_dest, source_prefix, dest_prefix
                )
                log.info(
                    "Successfully moved directory from {} to {}: {} -> {} ({} files)",
                    source_storage_name,
                    dest_storage_name,
                    source_prefix,
                    dest_prefix,
                    file_count,
                )
                return file_count

            # Other storage types: transfer files individually
            file_list = await self._list_files_with_prefix(resolved_source, source_prefix)

            if not file_list:
                log.warning("No files found with prefix: {}", source_prefix)
                return 0

            log.info(
                "Transferring {} files from {} to {}",
                len(file_list),
                source_storage_name,
                dest_storage_name,
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

                    await self.transfer_file(source_storage, dest_storage, source_path, dest_path)

            # Execute transfers concurrently
            await asyncio.gather(*[_transfer_single_file(path) for path in file_list])

            log.info(
                "Successfully transferred {} files from {} to {}",
                len(file_list),
                source_storage_name,
                dest_storage_name,
            )
            return len(file_list)

        except Exception as e:
            raise StorageTransferError(
                f"Failed to transfer directory from {source_storage_name} to {dest_storage_name}: "
                f"{source_prefix} -> {dest_prefix}: {e!s}"
            ) from e

    async def _move_vfs_directory(
        self,
        source_storage: VFSStorage,
        dest_storage: VFSStorage,
        source_prefix: str,
        dest_prefix: str,
    ) -> None:
        """Move entire directory between VFS storages."""
        source_path = source_storage.resolve_path(source_prefix)
        dest_path = dest_storage.resolve_path(dest_prefix)

        if not source_path.exists():
            raise StorageTransferError(f"Source path does not exist: {source_path}")

        if dest_path.exists():
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, str(dest_path))

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        await asyncio.get_event_loop().run_in_executor(
            None, shutil.move, str(source_path), str(dest_path)
        )

        # Ensure cleanup for cross-filesystem moves
        if source_path.exists():
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, shutil.rmtree, str(source_path)
                )
                log.warning(
                    "Cross-filesystem move fallback: manually removed source {}", source_path
                )
            except Exception as e:
                log.error("Failed to cleanup source after move: {}", e)
                raise

        # Cleanup empty artifact directories
        self._cleanup_empty_parents(source_path.parent, source_storage.base_path)

    def _cleanup_empty_parents(self, path: Path, base_path: Path) -> None:
        """Remove empty parent directories up to base_path."""
        current = path
        while current != base_path and current.exists():
            try:
                current.rmdir()  # Only removes if empty
                current = current.parent
            except OSError:
                break  # Not empty or other error

    async def _move_vfs_to_vfs(
        self,
        source_storage: VFSStorage,
        dest_storage: VFSStorage,
        source_path: str,
        dest_path: str,
    ) -> None:
        """Optimized move between VFS storages using direct file system operations."""
        source_full_path = source_storage.resolve_path(source_path)
        dest_full_path = dest_storage.resolve_path(dest_path)

        if not source_full_path.exists():
            raise StorageTransferError(f"Source path does not exist: {source_full_path}")

        # Remove destination if it exists to avoid conflicts
        if dest_full_path.exists():
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, str(dest_full_path))

        # Ensure parent directory exists
        dest_full_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file or directory (automatically removes source)
        await asyncio.get_event_loop().run_in_executor(
            None, shutil.move, str(source_full_path), str(dest_full_path)
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
        if isinstance(storage, ObjectStorage):
            return await self._list_object_storage_files_with_prefix(storage, prefix)
        raise StorageTransferError(f"Unsupported storage type: {type(storage)}")

    async def _list_vfs_files_with_prefix(self, storage: VFSStorage, prefix: str) -> list[str]:
        """List files in VFS storage with given prefix."""
        try:
            full_path = storage.resolve_path(prefix)
            if full_path.is_file():
                return [prefix]
            if full_path.is_dir():
                files = []
                for item in full_path.rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(storage.base_path)
                        files.append(str(rel_path))
                return files
            return []
        except Exception:
            return []

    async def _list_object_storage_files_with_prefix(
        self, storage: ObjectStorage, prefix: str
    ) -> list[str]:
        """List files in Object storage with given prefix."""
        try:
            return await storage.list_objects_with_prefix(prefix)
        except Exception as e:
            log.warning(f"Failed to list objects with prefix '{prefix}': {e!s}")
            return []

    async def verify_transfer(
        self,
        source_storage: StorageTarget,
        dest_storage: StorageTarget,
        source_path: str,
        dest_path: str,
    ) -> bool:
        """
        Verify that a file was transferred correctly by comparing metadata.

        Args:
            source_storage: Source storage (name or instance)
            dest_storage: Destination storage (name or instance)
            source_path: Path in source storage
            dest_path: Path in destination storage

        Returns:
            True if transfer was successful, False otherwise
        """
        try:
            resolved_source = source_storage.resolve_storage(self._storage_pool)
            resolved_dest = dest_storage.resolve_storage(self._storage_pool)

            # Get metadata from both storages
            source_meta = await resolved_source.get_file_info(source_path)
            dest_meta = await resolved_dest.get_file_info(dest_path)

            # Compare file sizes
            if hasattr(source_meta, "size") and hasattr(dest_meta, "size"):
                return source_meta.size == dest_meta.size

            # If size comparison is not available, assume success
            return True

        except Exception as e:
            log.error("Failed to verify transfer: {} -> {}: {}", source_path, dest_path, e)
            return False
