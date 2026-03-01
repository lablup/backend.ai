from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import VFolderAction


@dataclass
class ListAllowedTypesAction(VFolderAction):
    """Query allowed vfolder types from etcd config."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListAllowedTypesActionResult(BaseActionResult):
    allowed_types: list[str]

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListAllHostsAction(VFolderAction):
    """List all storage hosts/volumes with default host info."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListAllHostsActionResult(BaseActionResult):
    default: str | None
    allowed: list[str]

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetVolumePerfMetricAction(VFolderAction):
    """Get performance metrics for a specific storage volume."""

    folder_host: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetVolumePerfMetricActionResult(BaseActionResult):
    data: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetVFolderUsageAction(VFolderAction):
    """Get usage statistics for a specific vfolder from storage proxy."""

    folder_host: str
    vfolder_id: str
    unmanaged_path: str | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.vfolder_id


@dataclass
class GetVFolderUsageActionResult(BaseActionResult):
    data: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetVFolderUsedBytesAction(VFolderAction):
    """Get used bytes for a specific vfolder from storage proxy."""

    folder_host: str
    vfolder_id: str
    unmanaged_path: str | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.vfolder_id


@dataclass
class GetVFolderUsedBytesActionResult(BaseActionResult):
    data: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None
