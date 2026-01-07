from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, override

import aiofiles
import aiofiles.os

from ai.backend.common.artifact_storage import AbstractStorage
from ai.backend.common.dto.storage.response import VFSFileMetaResponse
from ai.backend.common.types import StreamReader, VFolderID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.errors import (
    FileStreamDownloadError,
    FileStreamUploadError,
)
from ai.backend.storage.exception import VFolderFileNotFoundError
from ai.backend.storage.storages.vfs_storage import (
    VFSDirectoryDownloadServerStreamReader,
    VFSFileDownloadServerStreamReader,
)
from ai.backend.storage.utils import normalize_filepath

if TYPE_CHECKING:
    from ai.backend.storage.volumes.abc import AbstractVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

# Default chunk sizes for upload/download
DEFAULT_UPLOAD_CHUNK_SIZE = 64 * 1024  # 64KB
DEFAULT_DOWNLOAD_CHUNK_SIZE = 64 * 1024  # 64KB


class VFolderStorage(AbstractStorage):
    """
    VFolder storage backend that uses a resolved vfolder path as base storage.
    This allows artifact import operations to write directly to a vfolder
    without modifying the import pipeline logic.
    """

    _name: str
    _base_path: Path
    _vfid: VFolderID
    _upload_chunk_size: int
    _download_chunk_size: int

    def __init__(
        self,
        name: str,
        volume: AbstractVolume,
        vfid: VFolderID,
        *,
        upload_chunk_size: int = DEFAULT_UPLOAD_CHUNK_SIZE,
        download_chunk_size: int = DEFAULT_DOWNLOAD_CHUNK_SIZE,
    ) -> None:
        self._name = name
        self._vfid = vfid
        self._base_path = volume.mangle_vfpath(vfid)
        self._upload_chunk_size = upload_chunk_size
        self._download_chunk_size = download_chunk_size

        log.info(
            f"VFolderStorage initialized: name={name}, vfid={vfid}, base_path={self._base_path}"
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def base_path(self) -> Path:
        return self._base_path

    @property
    def vfid(self) -> VFolderID:
        return self._vfid

    def resolve_path(self, filepath: str) -> Path:
        """
        Resolve relative filepath to absolute path within base_path.
        Prevents path traversal attacks.
        """
        normalized_path = normalize_filepath(filepath)
        full_path = (self._base_path / normalized_path).resolve()

        try:
            full_path.relative_to(self._base_path)
        except ValueError:
            raise FileStreamUploadError(f"Path traversal not allowed: {filepath}")

        return full_path

    @override
    async def stream_upload(
        self,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        """
        Upload a file to vfolder using streaming.

        Args:
            filepath: Path to the file to upload (relative to vfolder base_path)
            data_stream: Async iterator of file data chunks
        """
        try:
            target_path = self.resolve_path(filepath)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            total_size = 0
            async with aiofiles.open(target_path, "wb") as f:
                async for chunk in data_stream.read():
                    if chunk:
                        await f.write(chunk)
                        total_size += len(chunk)

            log.debug(f"Uploaded to vfolder: {filepath} ({total_size} bytes)")

        except Exception as e:
            raise FileStreamUploadError(f"Upload to vfolder failed: {e!s}") from e

    @override
    async def stream_download(self, filepath: str) -> StreamReader:
        """
        Download a file or directory from vfolder using streaming.

        Args:
            filepath: Path to the file or directory to download (relative to base_path)

        Returns:
            StreamReader: Stream for reading file data or tar archive for directories
        """
        try:
            target_path = self.resolve_path(filepath)

            if not target_path.exists():
                raise FileStreamDownloadError(f"Path not found in vfolder: {filepath}")

            if target_path.is_dir():
                return VFSDirectoryDownloadServerStreamReader(
                    target_path, self._download_chunk_size
                )
            return VFSFileDownloadServerStreamReader(target_path, self._download_chunk_size)

        except Exception as e:
            raise FileStreamDownloadError(f"Download from vfolder failed: {e!s}") from e

    @override
    async def get_file_info(self, filepath: str) -> VFSFileMetaResponse:
        """
        Get file information.

        Args:
            filepath: Path to the file (relative to base_path)

        Returns:
            VFSFileMetaResponse with file metadata
        """
        try:
            target_path = self.resolve_path(filepath)

            if not target_path.exists():
                raise VFolderFileNotFoundError(f"File not found in vfolder: {filepath}")

            stat_result = await aiofiles.os.stat(target_path)

            content_type = "application/octet-stream"
            if target_path.suffix:
                import mimetypes

                guessed_type, _ = mimetypes.guess_type(str(target_path))
                if guessed_type:
                    content_type = guessed_type

            return VFSFileMetaResponse(
                filepath=filepath,
                content_length=stat_result.st_size,
                content_type=content_type,
                last_modified=stat_result.st_mtime,
                created=stat_result.st_ctime,
                is_directory=target_path.is_dir(),
                metadata={
                    "mode": oct(stat_result.st_mode),
                    "uid": str(stat_result.st_uid),
                    "gid": str(stat_result.st_gid),
                },
            )

        except Exception as e:
            raise FileStreamDownloadError(f"Get vfolder file info failed: {e!s}") from e

    @override
    async def delete_file(self, filepath: str) -> None:
        """
        Delete a file or directory from vfolder.

        Args:
            filepath: Path to the file/directory to delete (relative to base_path)
        """
        try:
            target_path = self.resolve_path(filepath)

            if not target_path.exists():
                return

            if target_path.is_file():
                await aiofiles.os.remove(target_path)
            elif target_path.is_dir():
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, shutil.rmtree, target_path)
            else:
                raise FileStreamUploadError(f"Cannot delete from vfolder: {filepath}")

        except Exception as e:
            raise FileStreamUploadError(f"Delete from vfolder failed: {e!s}") from e
