from __future__ import annotations

import enum
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePath
from typing import Any, Final, Mapping, Optional, override

import attrs
import trafaret as t
from aiohttp import BodyPartReader, MultipartReader, web
from pydantic import BaseModel

from ai.backend.common import validators as tx
from ai.backend.common.types import QuotaConfig, StreamReader, VFolderID

__all__ = (
    "Sentinel",
    "SENTINEL",
    "FSPerfMetric",
    "CapacityUsage",
    "VolumeInfo",
    "VFolderID",
    "TreeUsage",
    "QuotaConfig",
    "Stat",
    "DirEntry",
    "DirEntryType",
    "HealthResponse",
)


class Sentinel(enum.Enum):
    token = 0


SENTINEL: Final = Sentinel.token


@attrs.define(slots=True, frozen=True)
class FSPerfMetric:
    # iops
    iops_read: int
    iops_write: int
    # thruput
    io_bytes_read: int
    io_bytes_write: int
    # latency
    io_usec_read: float
    io_usec_write: float


@attrs.define(slots=True, frozen=True)
class CapacityUsage:
    used_bytes: int
    capacity_bytes: int


@attrs.define(slots=True, frozen=True)
class QuotaUsage:
    used_bytes: int
    limit_bytes: int


@attrs.define(slots=True, frozen=True)
class VolumeInfo:
    backend: str
    path: Path
    fsprefix: Optional[PurePath]
    options: Optional[Mapping[str, Any]]

    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return t.Dict(
            {
                t.Key("backend"): t.String,
                t.Key("path"): tx.Path(type="dir"),
                t.Key("fsprefix", default="."): tx.PurePath(relative_only=True),
                t.Key("options", default=None): t.Null | t.Mapping(t.String, t.Any),
            },
        )


@attrs.define(slots=True, frozen=True)
class TreeUsage:
    file_count: int  # TODO: refactor using DecimalSize
    used_bytes: int  # TODO: refactor using DecimalSize


@attrs.define(slots=True, frozen=True)
class Stat:
    size: int
    owner: str
    mode: int
    modified: datetime
    created: datetime


class DirEntryType(enum.Enum):
    FILE = 0
    DIRECTORY = 1
    SYMLINK = 2


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class DirEntry:
    name: str
    path: Path
    type: DirEntryType
    stat: Stat
    symlink_target: str


@dataclass
class BucketCopyOptions:
    concurrency: int
    progress_log_interval_bytes: int


_DEFAULT_UPLOAD_FILE_CHUNKS = 8192  # Default chunk size for streaming uploads


class MultipartFileUploadStreamReader(StreamReader):
    _file_reader: MultipartReader

    def __init__(self, file_reader: MultipartReader, content_type: Optional[str]) -> None:
        self._file_reader = file_reader
        self._content_type = content_type

    @override
    async def read(self) -> AsyncIterator[bytes]:
        file_part = await self._file_reader.next()
        while file_part and not getattr(file_part, "filename", None):
            await file_part.release()
            file_part = await self._file_reader.next()

        # TODO: Make exception class
        if file_part is None:
            raise web.HTTPBadRequest(reason='No file part found (expected field "file")')
        if not isinstance(file_part, BodyPartReader):
            raise web.HTTPBadRequest(reason="Invalid file part")

        while True:
            chunk = await file_part.read_chunk(_DEFAULT_UPLOAD_FILE_CHUNKS)
            if not chunk:
                break
            yield chunk

    @override
    def content_type(self) -> Optional[str]:
        return self._content_type


class HealthResponse(BaseModel):
    """Standard health check response"""

    status: str
    version: str
    component: str
