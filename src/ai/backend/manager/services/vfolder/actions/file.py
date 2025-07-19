import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    Any,
    Optional,
    override,
)

from ai.backend.common.types import ResultSet
from ai.backend.manager.actions.action import BaseActionResult

from ..types import FileInfo
from .base import VFolderAction


@dataclass
class CreateUploadSessionAction(VFolderAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    path: str
    size: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "upload"


@dataclass
class CreateUploadSessionActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    token: str
    url: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class CreateDownloadSessionAction(VFolderAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    path: str
    archive: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "download"


@dataclass
class CreateDownloadSessionActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    token: str
    url: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class ListFilesAction(VFolderAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID

    path: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_files"


@dataclass
class ListFilesActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID
    files: list[FileInfo]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class RenameFileAction(VFolderAction):
    user_uuid: uuid.UUID
    keypair_resource_policy: Mapping[str, Any]

    vfolder_uuid: uuid.UUID

    target_path: str
    new_name: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "rename"


@dataclass
class RenameFileActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class DeleteFilesAction(VFolderAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID

    files: list[str]
    recursive: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_files"


@dataclass
class DeleteFilesActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class MkdirAction(VFolderAction):
    user_id: uuid.UUID
    vfolder_uuid: uuid.UUID

    path: str | list[str]
    parents: bool
    exist_ok: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "mkdir"


@dataclass
class MkdirActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID
    results: ResultSet
    storage_resp_status: int

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)
