"""V2 file operation actions — user_id based, no keypair_resource_policy."""

import dataclasses
import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import (
    EntityType,
    RBACElementType,
    ScopeType,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.vfolder.types import FileInfo


@dataclass
class _VFolderFileV2ActionBase(BaseScopeAction):
    """Common fields and RBAC wiring for v2 vfolder file actions."""

    user_id: uuid.UUID
    vfolder_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.VFOLDER

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.VFOLDER,
            element_id=str(self.vfolder_id),
        )


# ---- List files ----


@dataclass
class ListFilesV2Action(_VFolderFileV2ActionBase):
    path: str = "."

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ListFilesV2ActionResult(BaseActionResult):
    files: list[FileInfo]

    @override
    def entity_id(self) -> str | None:
        return None


# ---- Mkdir ----


@dataclass
class MkdirV2Action(_VFolderFileV2ActionBase):
    path: str | list[str] = ""
    parents: bool = True
    exist_ok: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class MkdirV2ActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None


# ---- Move file ----


@dataclass
class MoveFileV2Action(_VFolderFileV2ActionBase):
    src: str = ""
    dst: str = ""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class MoveFileV2ActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None


# ---- Delete files ----


@dataclass
class DeleteFilesV2Action(_VFolderFileV2ActionBase):
    files: list[str] = dataclasses.field(default_factory=list)
    recursive: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class DeleteFilesV2ActionResult(BaseActionResult):
    bgtask_id: str = ""

    @override
    def entity_id(self) -> str | None:
        return None


# ---- Download session ----


@dataclass
class CreateDownloadSessionV2Action(_VFolderFileV2ActionBase):
    path: str = ""
    archive: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class CreateDownloadSessionV2ActionResult(BaseActionResult):
    token: str
    url: str

    @override
    def entity_id(self) -> str | None:
        return None


# ---- Clone ----


@dataclass
class CloneVFolderV2Action(_VFolderFileV2ActionBase):
    target_name: str = ""
    target_host: str | None = None
    usage_mode: str = "general"
    permission: str = "rw"
    cloneable: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CloneVFolderV2ActionResult(BaseActionResult):
    new_vfolder_id: uuid.UUID
    bgtask_id: str | None = None

    @override
    def entity_id(self) -> str | None:
        return str(self.new_vfolder_id)
