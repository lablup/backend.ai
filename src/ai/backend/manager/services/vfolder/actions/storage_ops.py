from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

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


@dataclass
class ListHostsAction(VFolderAction):
    """List allowed storage hosts with permission filtering and volume info."""

    user_uuid: uuid.UUID
    domain_name: str
    group_id: uuid.UUID | None
    resource_policy: Mapping[str, Any]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListHostsActionResult(BaseActionResult):
    default: str | None
    allowed: list[str]
    volume_info: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetQuotaAction(VFolderAction):
    """Get quota for a specific vfolder from storage proxy."""

    folder_host: str
    vfid: str
    vfolder_id: uuid.UUID
    unmanaged_path: str | None
    user_role: UserRole
    user_uuid: uuid.UUID
    domain_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)


@dataclass
class GetQuotaActionResult(BaseActionResult):
    data: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class UpdateQuotaAction(VFolderAction):
    """Update quota for a specific vfolder."""

    folder_host: str
    vfid: str
    vfolder_id: uuid.UUID
    unmanaged_path: str | None
    user_role: UserRole
    user_uuid: uuid.UUID
    domain_name: str
    resource_policy: Mapping[str, Any]
    size_bytes: int

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)


@dataclass
class UpdateQuotaActionResult(BaseActionResult):
    size_bytes: int

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ChangeVFolderOwnershipAction(VFolderAction):
    """Change ownership of a user vfolder to another user."""

    vfolder_id: uuid.UUID
    user_email: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)


@dataclass
class ChangeVFolderOwnershipActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None
