"""
Module for handling ZIP file streaming operations.

Provides ZipArchiveStreamReader (a StreamReader subclass) for streaming
multiple files/directories as a single ZIP archive, and a format-agnostic
stream_archive_response helper for writing any StreamReader to an HTTP response.
"""

from __future__ import annotations

import asyncio
import os
import urllib.parse
from collections.abc import AsyncIterator
from pathlib import Path, PurePosixPath
from typing import Literal, Optional, override

import janus
import zipstream
from aiohttp import hdrs, web
from pydantic import BaseModel, Field

from ai.backend.common.type_adapters.vfolder import VFolderIDField
from ai.backend.common.types import StreamReader
from ai.backend.storage.types import SENTINEL, Sentinel

DEFAULT_INFLIGHT_CHUNKS = 8


class ArchiveDownloadTokenData(BaseModel):
    """Pydantic model for validating the JWT payload of archive download tokens."""

    operation: Literal["download"]
    volume: str
    vfolder_id: VFolderIDField
    files: list[PurePosixPath] = Field(min_length=1)


class ZipArchiveStreamReader(StreamReader):
    """StreamReader that produces a ZIP archive from multiple file/directory entries.

    The constructor registers files into a zipstream.ZipFile (metadata only, lazy).
    Actual file reads and compression happen when read() is iterated, bridged from
    a sync thread to async via janus.Queue.
    """

    _zf: zipstream.ZipFile

    _base_path: Path

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path
        self._zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)

    def add_entries(self, entries: list[Path]) -> None:
        """Register file/directory paths into the zip archive.

        Each entry's archive name is derived from its path relative to base_path.
        Directories are walked recursively via os.walk. Symlinks and other
        non-regular file types raise ValueError.
        """
        for file_path in entries:
            arcname = str(PurePosixPath(file_path.relative_to(self._base_path)))
            if file_path.is_file():
                self._zf.write(file_path, arcname=arcname)
            elif file_path.is_dir():
                for root, dirs, files in os.walk(file_path):
                    root_path = Path(root)
                    rel_root = root_path.relative_to(file_path)
                    for f in files:
                        self._zf.write(
                            root_path / f,
                            arcname=str(Path(arcname) / rel_root / f),
                        )
                    if len(dirs) == 0 and len(files) == 0:
                        self._zf.write(
                            root_path,
                            arcname=str(Path(arcname) / rel_root),
                        )
            else:
                raise ValueError(f"Unsupported file type: {file_path.relative_to(self._base_path)}")

    @override
    async def read(self) -> AsyncIterator[bytes]:
        # Sync-to-async bridge: zipstream.ZipFile is a sync iterable,
        # so we run it in a thread executor and pipe chunks through
        # a janus queue (sync producer → async consumer).
        q: janus.Queue[bytes | Sentinel] = janus.Queue(maxsize=DEFAULT_INFLIGHT_CHUNKS)
        try:
            loop = asyncio.get_running_loop()
            put_chunks = loop.run_in_executor(None, self._produce_chunks, q.sync_q)
            while True:
                item = await q.async_q.get()
                if isinstance(item, Sentinel):
                    break
                yield item
                q.async_q.task_done()
            await put_chunks
        finally:
            q.close()
            await q.wait_closed()

    def _produce_chunks(self, q: janus.SyncQueue[bytes | Sentinel]) -> None:
        for chunk in self._zf:
            q.put(chunk)
        q.put(SENTINEL)

    @override
    def content_type(self) -> Optional[str]:
        return "application/zip"


async def stream_archive_response(
    request: web.Request,
    reader: StreamReader,
    filename: str,
) -> web.StreamResponse:
    """Stream a StreamReader's output as an HTTP attachment response.

    This helper is format-agnostic: it works with any StreamReader (ZIP, tar, etc.).
    """
    ascii_filename = filename.encode("ascii", errors="ignore").decode("ascii").replace('"', r"\"")
    encoded_filename = urllib.parse.quote(filename, encoding="utf-8")
    response = web.StreamResponse(
        headers={
            hdrs.CONTENT_TYPE: reader.content_type() or "application/octet-stream",
            hdrs.CONTENT_DISPOSITION: " ".join([
                f'attachment;filename="{ascii_filename}";',  # RFC-2616 sec2.2
                f"filename*=UTF-8''{encoded_filename}",  # RFC-5987
            ]),
        },
    )
    await response.prepare(request)
    async for chunk in reader.read():
        await response.write(chunk)
    return response
