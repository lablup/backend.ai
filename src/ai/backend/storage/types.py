from __future__ import annotations

import enum
from datetime import datetime
from pathlib import Path, PurePath
from typing import Any, Final, Mapping, Optional

import attrs
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.types import BinarySize


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
class FSUsage:
    capacity_bytes: BinarySize
    used_bytes: BinarySize


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
class VFolderCreationOptions:
    quota: Optional[BinarySize]

    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return t.Dict({t.Key("quota", default=None): t.Null | tx.BinarySize})

    @classmethod
    def as_object(cls, dict_opts: Mapping | None) -> VFolderCreationOptions:
        if dict_opts is None:
            quota = None
        else:
            quota = dict_opts.get("quota")
        return VFolderCreationOptions(quota=quota)


@attrs.define(slots=True, frozen=True)
class VFolderUsage:
    file_count: int
    used_bytes: int


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
