import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    Any,
    override,
)

from ai.backend.common.bgtask.types import TaskID
from ai.backend.common.types import ResultSet
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.types import FileInfo

from .base import VFolderDirectoryAction, VFolderFileAction


@dataclass
class CreateUploadSessionAction(VFolderFileAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    path: str
    size: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_upload_session"


@dataclass
class CreateUploadSessionActionResult:
    vfolder_uuid: uuid.UUID

    token: str
    url: str


@dataclass
class CreateDownloadSessionAction(VFolderFileAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    path: str
    archive: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_download_session"


@dataclass
class CreateDownloadSessionActionResult:
    vfolder_uuid: uuid.UUID

    token: str
    url: str


@dataclass
class CreateArchiveDownloadSessionAction(VFolderFileAction):
    keypair_resource_policy: Mapping[str, Any]

    files: list[str]

    filename: str | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder_archive_download_session"


@dataclass
class CreateArchiveDownloadSessionActionResult:
    vfolder_uuid: uuid.UUID

    token: str
    url: str


@dataclass
class ListFilesAction(VFolderFileAction):
    user_uuid: uuid.UUID

    path: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_vfolder_files"


@dataclass
class ListFilesActionResult:
    vfolder_uuid: uuid.UUID
    files: list[FileInfo]


@dataclass
class RenameFileAction(VFolderFileAction):
    user_uuid: uuid.UUID
    keypair_resource_policy: Mapping[str, Any]

    target_path: str
    new_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "rename_vfolder_file"


@dataclass
class RenameFileActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class DeleteFilesAction(VFolderFileAction):
    user_uuid: uuid.UUID

    files: list[str]
    recursive: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_vfolder_files"


@dataclass
class DeleteFilesActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class DeleteFilesAsyncAction(VFolderFileAction):
    user_uuid: uuid.UUID

    files: list[str]
    recursive: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_vfolder_files_async"


@dataclass
class DeleteFilesAsyncActionResult:
    vfolder_uuid: uuid.UUID
    task_id: TaskID


@dataclass
class MoveFileAction(VFolderFileAction):
    user_uuid: uuid.UUID

    src: str
    dst: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "move_vfolder_file"


@dataclass
class MoveFileActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class MkdirAction(VFolderDirectoryAction):
    user_id: uuid.UUID

    path: str | list[str]
    parents: bool
    exist_ok: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "vfolder_mkdir"


@dataclass
class MkdirActionResult:
    vfolder_uuid: uuid.UUID
    results: ResultSet
    storage_resp_status: int
