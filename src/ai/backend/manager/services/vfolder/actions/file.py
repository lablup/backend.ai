import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    Any,
    override,
)

from ai.backend.common.bgtask.types import TaskID
from ai.backend.common.types import ResultSet
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.types import FileInfo

from .base import VFolderDirectoryAction, VFolderFileAction


@dataclass
class CreateUploadSessionAction(VFolderFileAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    path: str
    size: str

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateUploadSessionActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    token: str
    url: str

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)


@dataclass
class CreateDownloadSessionAction(VFolderFileAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    path: str
    archive: bool

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class CreateDownloadSessionActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    token: str
    url: str

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)


@dataclass
class ListFilesAction(VFolderFileAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID

    path: str

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListFilesActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID
    files: list[FileInfo]

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)


@dataclass
class RenameFileAction(VFolderFileAction):
    user_uuid: uuid.UUID
    keypair_resource_policy: Mapping[str, Any]

    vfolder_uuid: uuid.UUID

    target_path: str
    new_name: str

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class RenameFileActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)


@dataclass
class DeleteFilesAction(VFolderFileAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID

    files: list[str]
    recursive: bool

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteFilesActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)


@dataclass
class DeleteFilesAsyncAction(VFolderFileAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID

    files: list[str]
    recursive: bool

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteFilesAsyncActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID
    task_id: TaskID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)


@dataclass
class MkdirAction(VFolderDirectoryAction):
    user_id: uuid.UUID
    vfolder_uuid: uuid.UUID

    path: str | list[str]
    parents: bool
    exist_ok: bool

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class MkdirActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID
    results: ResultSet
    storage_resp_status: int

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)
