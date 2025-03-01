from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Optional, Self

from ai.backend.common.dto.storage.field import VFolderMetaField, VolumeMetaField
from ai.backend.common.dto.storage.path import QuotaScopeKeyPath, VFolderKeyPath
from ai.backend.common.dto.storage.response import QuotaScopeResponse
from ai.backend.common.types import QuotaScopeID, VFolderID, VolumeID


class LoggingInternalMeta(metaclass=ABCMeta):
    @abstractmethod
    def to_logging_str(self) -> str:
        pass


@dataclass
class QuotaScopeKey(LoggingInternalMeta):
    volume_id: VolumeID
    quota_scope_id: QuotaScopeID

    @classmethod
    def from_quota_scope_path(cls, path: QuotaScopeKeyPath) -> Self:
        return cls(
            volume_id=path.volume_id, quota_scope_id=QuotaScopeID(path.scope_type, path.scope_uuid)
        )

    def to_logging_str(self) -> str:
        return f"QuotaScopeKey(volume_id={self.volume_id}, quota_scope_id={self.quota_scope_id})"


@dataclass
class VFolderKey(LoggingInternalMeta):
    volume_id: VolumeID
    vfolder_id: VFolderID

    @classmethod
    def from_vfolder_path(cls, path: VFolderKeyPath) -> Self:
        quota_scope_id = QuotaScopeID(path.scope_type, path.scope_uuid)
        return cls(
            volume_id=path.volume_id,
            vfolder_id=VFolderID(quota_scope_id, path.folder_uuid),
        )

    def to_logging_str(self) -> str:
        return f"VFolderKey(volume_id={self.volume_id}, vfolder_id={self.vfolder_id})"


@dataclass
class VolumeMeta(LoggingInternalMeta):
    volume_id: VolumeID
    backend: str
    path: Path
    fsprefix: Optional[PurePath]
    capabilities: list[str]

    def to_field(self) -> VolumeMetaField:
        return VolumeMetaField(
            volume_id=self.volume_id,
            backend=self.backend,
            path=str(self.path),
            fsprefix=str(self.fsprefix) if self.fsprefix is not None else None,
            capabilities=self.capabilities,
        )

    def to_logging_str(self) -> str:
        return (
            f"VolumeMeta(volume_id={self.volume_id}, backend={self.backend}, path={self.path}, "
            f"fsprefix={self.fsprefix}, capabilities={self.capabilities})"
        )


@dataclass
class VFolderMeta(LoggingInternalMeta):
    mount_path: Path
    file_count: int
    used_bytes: int
    capacity_bytes: int
    fs_used_bytes: int

    def to_field(self) -> VFolderMetaField:
        return VFolderMetaField(
            mount_path=str(self.mount_path),
            file_count=self.file_count,
            used_bytes=self.used_bytes,
            capacity_bytes=self.capacity_bytes,
            fs_used_bytes=self.fs_used_bytes,
        )

    def to_logging_str(self) -> str:
        return (
            f"VFolderMeta(mount_path={self.mount_path}, file_count={self.file_count}, "
            f"used_bytes={self.used_bytes}, capacity_bytes={self.capacity_bytes}, "
            f"fs_used_bytes={self.fs_used_bytes})"
        )


@dataclass
class QuotaScopeMeta(LoggingInternalMeta):
    used_bytes: Optional[int] = 0
    limit_bytes: Optional[int] = 0

    def to_response(self) -> QuotaScopeResponse:
        return QuotaScopeResponse(
            used_bytes=self.used_bytes,
            limit_bytes=self.limit_bytes,
        )

    def to_logging_str(self) -> str:
        return f"QuotaScopeMeta(used_bytes={self.used_bytes}, limit_bytes={self.limit_bytes})"
