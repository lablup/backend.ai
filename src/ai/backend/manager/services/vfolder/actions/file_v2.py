"""V2 file operation actions — user_id based, no keypair_resource_policy."""

import dataclasses
import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.actions.base import VFolderFileAction
from ai.backend.manager.services.vfolder.types import FileInfo


@dataclass
class _VFolderFileV2ActionBase(VFolderFileAction):
    """Common fields of the v2 vfolder file operations."""

    user_id: uuid.UUID


# ---- List files ----


@dataclass
class ListFilesV2Action(_VFolderFileV2ActionBase):
    path: str = "."

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_vfolder_files_v2"


@dataclass
class ListFilesV2ActionResult:
    files: list[FileInfo]


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

    @override
    @classmethod
    def action_name(cls) -> str:
        return "vfolder_mkdir_v2"


@dataclass
class MkdirV2ActionResult:
    pass


# ---- Move file ----


@dataclass
class MoveFileV2Action(_VFolderFileV2ActionBase):
    src: str = ""
    dst: str = ""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "move_vfolder_file_v2"


@dataclass
class MoveFileV2ActionResult:
    pass


# ---- Delete files ----


@dataclass
class DeleteFilesV2Action(_VFolderFileV2ActionBase):
    files: list[str] = dataclasses.field(default_factory=list)
    recursive: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_vfolder_files_v2"


@dataclass
class DeleteFilesV2ActionResult:
    bgtask_id: str = ""


# ---- Download session ----


@dataclass
class CreateDownloadSessionV2Action(_VFolderFileV2ActionBase):
    path: str = ""
    archive: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_download_session_v2"


@dataclass
class CreateDownloadSessionV2ActionResult:
    token: str
    url: str


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

    @override
    @classmethod
    def action_name(cls) -> str:
        return "clone_vfolder_v2"


@dataclass
class CloneVFolderV2ActionResult:
    new_vfolder_id: uuid.UUID
    bgtask_id: str | None = None
