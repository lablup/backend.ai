from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Any, override

from ai.backend.common.dto.storage.response import (
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
)
from ai.backend.common.types import StreamReader
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.exception import FileStreamUploadError, NotImplementedAPI
from ai.backend.storage.storages.base import AbstractStorage
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.vfs import VFSStorage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SequenceCompositeStorage(AbstractStorage):
    """
    Composite storage that stores files in a primary storage first,
    then cascades to secondary storages by copying from the primary.

    This design optimizes for cases where the primary storage is local (VFS)
    and secondary storages are remote, avoiding network transfers for
    secondary storage operations.
    """

    _name: str
    _primary_storage: AbstractStorage
    _secondary_storages: list[AbstractStorage]

    def __init__(
        self,
        name: str,
        primary_storage: AbstractStorage,
        secondary_storages: list[AbstractStorage],
    ) -> None:
        self._name = name
        self._primary_storage = primary_storage
        self._secondary_storages = secondary_storages

    @property
    def name(self) -> str:
        return self._name

    @property
    def primary_storage(self) -> AbstractStorage:
        return self._primary_storage

    @property
    def secondary_storages(self) -> list[AbstractStorage]:
        return self._secondary_storages.copy()

    @override
    async def stream_upload(
        self,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        """
        Upload file to primary storage first, then cascade to secondary storages.

        Args:
            filepath: Path to the file to upload
            data_stream: Async iterator of file data chunks
        """
        # 1. Upload to primary storage
        try:
            await self._primary_storage.stream_upload(filepath, data_stream)
        except Exception as e:
            raise FileStreamUploadError(f"Primary storage upload failed: {e}") from e

        # 2. Cascade to secondary storages
        failed_storages = []
        for i, secondary_storage in enumerate(self._secondary_storages):
            try:
                await self._copy_between_storages(
                    self._primary_storage, secondary_storage, filepath
                )
            except Exception as e:
                failed_storages.append((i, str(e)))
                log.warning(f"Failed to copy {filepath} to secondary storage {i}: {e}")

        # Log failures but don't fail the entire operation
        if failed_storages:
            log.warning(f"Some secondary storages failed for {filepath}: {failed_storages}")

    async def _copy_between_storages(
        self,
        src_storage: AbstractStorage,
        dst_storage: AbstractStorage,
        filepath: str,
    ) -> None:
        """
        Copy file between storages with optimization for VFS-to-VFS copies.

        Args:
            src_storage: Source storage
            dst_storage: Destination storage
            filepath: File path to copy
        """
        # VFS → VFS optimization: direct file system copy
        if isinstance(src_storage, VFSStorage) and isinstance(dst_storage, VFSStorage):
            await self._copy_vfs_to_vfs(src_storage, dst_storage, filepath)
        else:
            # General case: stream download + upload
            stream = await src_storage.stream_download(filepath)
            await dst_storage.stream_upload(filepath, stream)

    async def _copy_vfs_to_vfs(
        self,
        src_vfs: VFSStorage,
        dst_vfs: VFSStorage,
        filepath: str,
    ) -> None:
        """
        Optimized VFS-to-VFS copy using file system operations.

        Args:
            src_vfs: Source VFS storage
            dst_vfs: Destination VFS storage
            filepath: File path to copy
        """
        src_path = src_vfs._resolve_path(filepath)
        dst_path = dst_vfs._resolve_path(filepath)

        # Create parent directories
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Async file copy
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, shutil.copy2, src_path, dst_path)

    @override
    async def stream_download(self, filepath: str) -> StreamReader:
        """
        Download file from primary storage only.

        Since all storages are synchronized, we only need to download
        from the primary storage.

        Args:
            filepath: Path to the file to download

        Returns:
            StreamReader for the file content
        """
        return await self._primary_storage.stream_download(filepath)

    async def get_object_info(self, filepath: str) -> Any:
        """
        Get object metadata from primary storage.

        Args:
            filepath: Path to the file

        Returns:
            Object metadata response
        """
        return await self._primary_storage.get_object_info(filepath)

    async def delete_object(self, filepath: str) -> None:
        """
        Delete object from all storages.

        Args:
            filepath: Path to the file to delete
        """
        # Delete from all storages (primary and secondary)
        all_storages = [self._primary_storage] + self._secondary_storages

        failed_deletions = []
        for i, storage in enumerate(all_storages):
            try:
                await storage.delete_object(filepath)
            except Exception as e:
                failed_deletions.append((i, str(e)))
                log.warning(f"Failed to delete {filepath} from storage {i}: {e}")

        # Log failures but don't fail the entire operation
        if failed_deletions:
            log.warning(f"Some storages failed to delete {filepath}: {failed_deletions}")

    async def generate_presigned_upload_url(self, key: str) -> PresignedUploadObjectResponse:
        """
        Generate presigned upload URL from primary storage.

        Args:
            key: Object key

        Returns:
            Presigned upload URL response
        """
        if isinstance(self._primary_storage, ObjectStorage):
            return await self._primary_storage.generate_presigned_upload_url(key)
        else:
            raise NotImplementedAPI("Primary storage does not support presigned upload URLs")

    async def generate_presigned_download_url(
        self, filepath: str
    ) -> PresignedDownloadObjectResponse:
        """
        Generate presigned download URL from primary storage.

        Args:
            filepath: Path to the file

        Returns:
            Presigned download URL response
        """
        if isinstance(self._primary_storage, ObjectStorage):
            return await self._primary_storage.generate_presigned_download_url(filepath)
        else:
            raise NotImplementedAPI("Primary storage does not support presigned download URLs")
