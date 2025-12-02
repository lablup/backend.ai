from __future__ import annotations

import asyncio
import logging
import shutil
import tarfile
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Optional, override

import aiofiles
import aiofiles.os

from ai.backend.common.artifact_storage import AbstractStorage
from ai.backend.common.dto.storage.response import (
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
    VFSFileInfo,
    VFSFileMetaResponse,
    VFSListFilesResponse,
)
from ai.backend.common.types import StreamReader
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import VFSStorageConfig
from ai.backend.storage.errors import (
    FileStreamDownloadError,
    FileStreamUploadError,
    InvalidPathError,
    NotImplementedAPI,
    ObjectInfoFetchError,
    StorageBucketFileNotFoundError,
)
from ai.backend.storage.utils import normalize_filepath

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class VFSFileDownloadServerStreamReader(StreamReader):
    """Stream reader that creates a tar archive of a directory on-the-fly."""

    _file_path: Path
    _chunk_size: int

    def __init__(self, file_path: Path, chunk_size: int) -> None:
        self._file_path = file_path
        self._chunk_size = chunk_size

    @override
    async def read(self) -> AsyncIterator[bytes]:
        """Create a tar archive of the directory and stream it."""
        async with aiofiles.open(self._file_path, "rb") as f:
            bytes_streamed = 0
            while True:
                chunk = await f.read(self._chunk_size)
                if not chunk:
                    break
                bytes_streamed += len(chunk)
                yield chunk

    @override
    def content_type(self) -> Optional[str]:
        return "application/octet-stream"


class VFSDirectoryDownloadServerStreamReader(StreamReader):
    """Stream reader that creates a tar archive of a directory on-the-fly."""

    _directory_path: Path
    _chunk_size: int
    _temp_file: Optional[Path]

    def __init__(self, directory_path: Path, chunk_size: int) -> None:
        self._directory_path = directory_path
        self._chunk_size = chunk_size
        self._temp_file = None

    @override
    async def read(self) -> AsyncIterator[bytes]:
        """Create a tar archive of the directory and stream it."""
        loop = asyncio.get_running_loop()

        # Create temporary file for the tar archive
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar") as temp_file:
            self._temp_file = Path(temp_file.name)

            # Create tar archive in executor to avoid blocking
            await loop.run_in_executor(
                None, self._create_tar_archive, str(self._directory_path), str(self._temp_file)
            )

        try:
            # Stream the tar file
            async with aiofiles.open(self._temp_file, "rb") as f:
                bytes_streamed = 0
                while True:
                    chunk = await f.read(self._chunk_size)
                    if not chunk:
                        break
                    bytes_streamed += len(chunk)
                    yield chunk
        finally:
            # Clean up temp file
            if self._temp_file and self._temp_file.exists():
                await aiofiles.os.remove(self._temp_file)
                log.debug(f"Cleaned up temp file: {self._temp_file}")

    @override
    def content_type(self) -> Optional[str]:
        return "application/x-tar"

    def _create_tar_archive(self, source_dir: str, tar_path: str) -> None:
        """Create tar archive of directory contents."""
        try:
            log.debug(f"Creating tar archive: {source_dir} -> {tar_path}")
            with tarfile.open(tar_path, "w") as tar:
                tar.add(source_dir, arcname=".", recursive=True)
            log.debug(f"Tar archive created successfully: {tar_path}")
        except Exception as e:
            log.error(f"Failed to create tar archive: {e}")
            raise


class VFSStorage(AbstractStorage):
    """
    VFS (Virtual File System) storage backend that uses host filesystem path
    as storage backend, similar to object storage but for local files.
    """

    _name: str
    _base_path: Path
    _upload_chunk_size: int
    _download_chunk_size: int
    _temporary: bool
    _max_file_size: Optional[int]

    def __init__(self, name: str, cfg: VFSStorageConfig) -> None:
        self._name = name
        base_path = cfg.base_path.resolve()
        if cfg.subpath:
            base_path = base_path / cfg.subpath
        self._base_path = base_path
        self._temporary = cfg.temporary

        # Ensure base path exists
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._upload_chunk_size = cfg.upload_chunk_size
        self._download_chunk_size = cfg.download_chunk_size
        self._max_file_size = cfg.max_file_size

    def cleanup_temporary_storage(self) -> None:
        """
        Clean up all files in temporary storage.
        This should be called only by the first process (pidx=0) on server startup.
        """
        if not self._temporary:
            return

        if not self._base_path.exists():
            return

        log.info(f"Cleaning up temporary storage: {self._base_path}")
        try:
            # Remove all contents but keep the directory itself
            for item in self._base_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            log.info(f"Temporary storage cleaned: {self._base_path}")
        except Exception as e:
            log.warning(f"Failed to clean temporary storage {self._base_path}: {e}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def base_path(self) -> Path:
        return self._base_path

    def resolve_path(self, filepath: str) -> Path:
        """
        Resolve relative filepath to absolute path within base_path.
        Prevents path traversal attacks.
        """
        # Normalize the filepath (remove .., ., etc.)
        normalized_path = normalize_filepath(filepath)

        # Resolve to absolute path within base_path
        full_path = (self._base_path / normalized_path).resolve()

        # Ensure the resolved path is within base_path
        try:
            full_path.relative_to(self._base_path)
        except ValueError:
            raise InvalidPathError(f"Path traversal not allowed: {filepath}")

        return full_path

    def _validate_upload_constraints(self, filepath: str, file_size: Optional[int] = None) -> None:
        """Validate upload constraints (file extension, size, read-only mode)."""
        # Check file size
        if self._max_file_size and file_size and file_size > self._max_file_size:
            raise FileStreamUploadError(
                f"File size {file_size} exceeds maximum {self._max_file_size}"
            )

    @override
    async def stream_upload(
        self,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        """
        Upload a file to VFS using streaming.

        Args:
            filepath: Path to the file to upload (relative to base_path)
            data_stream: Async iterator of file data chunks
        """
        try:
            # Validate constraints first
            self._validate_upload_constraints(filepath)

            # Resolve target path
            target_path = self.resolve_path(filepath)

            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Stream write to file
            total_size = 0
            async with aiofiles.open(target_path, "wb") as f:
                async for chunk in data_stream.read():
                    if chunk:  # Skip empty chunks
                        await f.write(chunk)
                        total_size += len(chunk)

                        # Check size limit during upload
                        if self._max_file_size and total_size > self._max_file_size:
                            # Clean up partial file
                            await f.close()
                            await aiofiles.os.remove(target_path)
                            raise FileStreamUploadError(
                                f"File size exceeds maximum {self._max_file_size}"
                            )

        except Exception as e:
            raise FileStreamUploadError(f"Upload failed: {str(e)}") from e

    @override
    async def stream_download(self, filepath: str) -> StreamReader:
        """
        Download a file or directory from VFS using streaming.

        Args:
            filepath: Path to the file or directory to download (relative to base_path)

        Returns:
            StreamReader: Stream for reading file data or tar archive for directories
        """
        try:
            target_path = self.resolve_path(filepath)

            if not target_path.exists():
                raise FileStreamDownloadError(f"Path not found: {filepath}")

            if target_path.is_dir():
                # Handle directory download as tar archive
                return VFSDirectoryDownloadServerStreamReader(
                    target_path, self._download_chunk_size
                )
            else:
                return VFSFileDownloadServerStreamReader(target_path, self._download_chunk_size)

        except Exception as e:
            raise FileStreamDownloadError(f"Download failed: {str(e)}") from e

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
                raise StorageBucketFileNotFoundError(f"File not found: {filepath}")

            stat_result = await aiofiles.os.stat(target_path)

            # Determine content type based on file extension
            content_type = "application/octet-stream"  # Default
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
            raise ObjectInfoFetchError(f"Get file info failed: {str(e)}") from e

    @override
    async def delete_file(self, filepath: str) -> None:
        """
        Delete a file or directory.

        Args:
            filepath: Path to the file/directory to delete (relative to base_path)
        """

        try:
            target_path = self.resolve_path(filepath)

            if not target_path.exists():
                # Silently ignore non-existent files (similar to S3 behavior)
                return

            if target_path.is_file():
                await aiofiles.os.remove(target_path)
            elif target_path.is_dir():
                # Remove directory recursively
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, shutil.rmtree, target_path)
            else:
                raise FileStreamUploadError(f"Cannot delete: {filepath}")

        except Exception as e:
            raise FileStreamUploadError(f"Delete failed: {str(e)}") from e

    async def list_directory(self, directory: str) -> list[VFSFileInfo]:
        """
        List files and directories in a directory.

        Args:
            directory: Directory path to list (relative to base_path)

        Returns:
            List of file/directory information
        """
        try:
            target_path = self.resolve_path(directory)

            if not target_path.exists():
                raise StorageBucketFileNotFoundError(f"Directory not found: {directory}")

            if not target_path.is_dir():
                raise FileStreamDownloadError(f"Path is not a directory: {directory}")

            entries = []
            entries_iter = await aiofiles.os.scandir(target_path)
            for entry in entries_iter:
                stat_result = await aiofiles.os.stat(entry.path)
                entries.append(
                    VFSFileInfo(
                        name=entry.name,
                        type="directory" if entry.is_dir() else "file",
                        size=stat_result.st_size if entry.is_file() else None,
                        modified=stat_result.st_mtime,
                        created=stat_result.st_ctime,
                        path=str(Path(directory) / entry.name),
                    )
                )

            return entries

        except Exception as e:
            raise FileStreamDownloadError(f"List directory failed: {str(e)}") from e

    async def list_files_recursive(self, directory: str) -> VFSListFilesResponse:
        """
        Recursively list all files in a directory and its subdirectories.

        Args:
            directory: Directory path to start listing from (relative to base_path)

        Returns:
            VFSListFilesResponse containing all files found recursively
        """
        try:
            target_path = self.resolve_path(directory)

            if not target_path.exists():
                raise StorageBucketFileNotFoundError(f"Directory not found: {directory}")

            if not target_path.is_dir():
                raise FileStreamDownloadError(f"Path is not a directory: {directory}")

            files = await self._collect_files_recursive(target_path, directory)

            return VFSListFilesResponse(files=files)

        except Exception as e:
            raise FileStreamDownloadError(f"List files recursively failed: {str(e)}") from e

    async def _collect_files_recursive(
        self, current_path: Path, relative_base: str
    ) -> list[VFSFileInfo]:
        """
        Helper method to recursively collect files.

        Args:
            current_path: Current absolute path being processed
            relative_base: Relative path from the original base directory

        Returns:
            List of found files
        """
        files: list[VFSFileInfo] = []
        entries_iter = await aiofiles.os.scandir(current_path)
        for entry in entries_iter:
            stat_result = await aiofiles.os.stat(entry.path)

            # Calculate relative path
            if relative_base:
                relative_path = str(Path(relative_base) / entry.name)
            else:
                relative_path = entry.name

            file_info = VFSFileInfo(
                name=entry.name,
                type="directory" if entry.is_dir() else "file",
                size=stat_result.st_size if entry.is_file() else None,
                modified=stat_result.st_mtime,
                created=stat_result.st_ctime,
                path=relative_path,
            )
            files.append(file_info)

            # Recursively process subdirectories
            if entry.is_dir():
                subdirectory_files = await self._collect_files_recursive(
                    Path(entry.path), relative_path
                )
                files.extend(subdirectory_files)

        return files

    async def create_directory(self, directory: str) -> None:
        """
        Create a directory.

        Args:
            directory: Directory path to create (relative to base_path)
        """
        try:
            target_path = self.resolve_path(directory)
            target_path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            raise FileStreamUploadError(f"Create directory failed: {str(e)}") from e

    async def get_disk_usage(self) -> dict:
        """
        Get disk usage information for the base path.

        Returns:
            Dictionary with capacity and used bytes information
        """
        try:
            stat_result = await aiofiles.os.statvfs(self._base_path)

            total_bytes = stat_result.f_frsize * stat_result.f_blocks
            available_bytes = stat_result.f_frsize * stat_result.f_bavail
            used_bytes = total_bytes - available_bytes

            return {
                "capacity_bytes": total_bytes,
                "used_bytes": used_bytes,
                "available_bytes": available_bytes,
            }

        except Exception as e:
            raise FileStreamDownloadError(f"Get disk usage failed: {str(e)}") from e

    async def generate_presigned_upload_url(self, key: str) -> PresignedUploadObjectResponse:
        raise NotImplementedAPI("VFS storage doesn't support presigned upload URLs")

    async def generate_presigned_download_url(
        self, filepath: str
    ) -> PresignedDownloadObjectResponse:
        raise NotImplementedAPI("VFS storage doesn't support presigned download URLs")
