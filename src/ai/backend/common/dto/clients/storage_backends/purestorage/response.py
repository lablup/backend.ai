from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import ConfigDict

from ai.backend.common.dto.clients.storage_backends.purestorage.types import (
    RapidFileEntryType,
)
from ai.backend.common.types import BackendAISchema


class PurityArrayMetadata(BackendAISchema):
    id: str
    name: str
    os: str
    revision: str
    version: str
    blade_count: int
    console_url: str


class PurityFileSystemUsage(BackendAISchema):
    capacity_bytes: int
    used_bytes: int


class PurityNFSMetric(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    reads_per_sec: float
    writes_per_sec: float
    read_bytes_per_sec: float
    write_bytes_per_sec: float
    usec_per_read_op: float
    usec_per_write_op: float


class RapidFileStat(BackendAISchema):
    size: int
    owner: str
    mode: int
    modified: datetime
    created: datetime


class RapidFileEntry(BackendAISchema):
    name: str
    path: Path
    type: RapidFileEntryType
    stat: RapidFileStat
    symlink_target: str


class RapidFileTreeUsage(BackendAISchema):
    file_count: int
    used_bytes: int
