from __future__ import annotations

import logging
import mimetypes
from collections.abc import AsyncIterator
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, override

import aiofiles.os

from ai.backend.common.artifact_storage import AbstractStorage
from ai.backend.common.dto.storage.response import VFSFileMetaResponse
from ai.backend.common.types import StreamReader, VFolderID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.errors import (
    FileStreamDownloadError,
    FileStreamUploadError,
)

if TYPE_CHECKING:
    from ai.backend.storage.volumes.abc import AbstractVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VolumeDownloadStreamReader(StreamReader):
    """
    StreamReader wrapper for AsyncIterator[bytes] from AbstractVolume.read_file().

    This allows using volume's read_file() output as a StreamReader
    compatible with the import pipeline.
    """

    _iterator: AsyncIterator[bytes]
    _content_type: str | None

    def __init__(
        self,
        iterator: AsyncIterator[bytes],
        content_type: str | None = None,
    ) -> None:
        self._iterator = iterator
        self._content_type = content_type

    @override
    async def read(self) -> AsyncIterator[bytes]:
        async for chunk in self._iterator:
            if chunk:  # Skip empty chunks
                yield chunk

    @override
    def content_type(self) -> str | None:
        return self._content_type


class VFolderStorage(AbstractStorage):
    """
    Storage implementation that wraps AbstractVolume to provide AbstractStorage interface.

    This enables using any volume backend (VFS, XFS, NetApp, GPFS, Weka, VAST, CephFS, etc.)
    as an artifact storage target without registering to StoragePool.

    Key advantages:
    - Uses volume's native file operations (add_file, read_file, delete_files, mkdir)
    - Supports all vfolder backends uniformly
    - No StoragePool registration overhead
    - Works with backend-specific quota management
    - Delegates all operations to the volume, enabling backend-specific optimizations
    """

    _volume: AbstractVolume
    _vfolder_id: VFolderID
    _name: str

    def __init__(
        self,
        name: str,
        volume: AbstractVolume,
        vfolder_id: VFolderID,
    ) -> None:
        self._name = name
        self._volume = volume
        self._vfolder_id = vfolder_id

        log.info(
            "VFolderStorage initialized: name={}, vfolder_id={}, volume_type={}",
            name,
            vfolder_id,
            type(volume).__name__,
        )

    @property
    @override
    def name(self) -> str:
        return self._name

    def _normalize_relpath(self, filepath: str) -> PurePosixPath:
        """Convert string filepath to PurePosixPath, handling leading slashes."""
        normalized = filepath.lstrip("/")
        return PurePosixPath(normalized)

    def resolve_path(self, filepath: str) -> Path:
        """
        Resolve relative filepath to absolute path within vfolder.

        Used for compatibility with verification steps that need filesystem paths.
        This delegates to volume's sanitize_vfpath for proper path validation.
        """
        relpath = self._normalize_relpath(filepath)
        return self._volume.sanitize_vfpath(self._vfolder_id, relpath)

    @override
    async def stream_upload(
        self,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        """
        Upload a file to vfolder using volume's add_file method.

        This method:
        1. Ensures parent directories exist
        2. Converts StreamReader to AsyncIterator[bytes]
        3. Delegates file writing to volume.add_file()
        """
        try:
            relpath = self._normalize_relpath(filepath)

            # Ensure parent directories exist
            parent_relpath = relpath.parent
            if parent_relpath != PurePosixPath("."):
                await self._volume.mkdir(
                    self._vfolder_id,
                    parent_relpath,
                    parents=True,
                    exist_ok=True,
                )

            # Convert StreamReader to AsyncIterator[bytes] for add_file
            async def _stream_to_iterator() -> AsyncIterator[bytes]:
                async for chunk in data_stream.read():
                    if chunk:
                        yield chunk

            await self._volume.add_file(
                self._vfolder_id,
                relpath,
                _stream_to_iterator(),
            )

            log.debug("Uploaded via volume adapter: {}", filepath)

        except Exception as e:
            raise FileStreamUploadError(f"Upload via volume adapter failed: {e!s}") from e

    @override
    async def stream_download(self, filepath: str) -> StreamReader:
        """
        Download a file from vfolder using volume's read_file method.

        Returns a StreamReader that wraps the volume's AsyncIterator[bytes].
        """
        try:
            relpath = self._normalize_relpath(filepath)

            # Detect content type from file extension
            content_type: str | None = None
            if relpath.suffix:
                guessed_type, _ = mimetypes.guess_type(str(relpath))
                content_type = guessed_type

            # read_file returns AsyncIterator[bytes]
            iterator = self._volume.read_file(self._vfolder_id, relpath)

            return VolumeDownloadStreamReader(iterator, content_type)

        except Exception as e:
            raise FileStreamDownloadError(f"Download via volume adapter failed: {e!s}") from e

    @override
    async def delete_file(self, filepath: str) -> None:
        """
        Delete a file or directory from vfolder using volume's delete_files method.

        Silently ignores errors if the file doesn't exist.
        """
        relpath = self._normalize_relpath(filepath)

        try:
            await self._volume.delete_files(
                self._vfolder_id,
                [relpath],
                recursive=True,
            )
            log.debug("Deleted via volume adapter: {}", filepath)
        except Exception as e:
            # Log but don't fail if file doesn't exist
            log.warning("Failed to delete {}: {}", filepath, e)

    @override
    async def get_file_info(self, filepath: str) -> VFSFileMetaResponse:
        """
        Get file metadata using volume's path resolution.

        Uses volume.sanitize_vfpath() for path validation and then
        retrieves file stats using aiofiles.
        """
        try:
            relpath = self._normalize_relpath(filepath)
            target_path = self._volume.sanitize_vfpath(self._vfolder_id, relpath)

            stat_result = await aiofiles.os.stat(target_path)

            content_type = "application/octet-stream"
            if target_path.suffix:
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
            raise FileStreamDownloadError(f"Get file info via volume adapter failed: {e!s}") from e
