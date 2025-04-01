import uuid
from typing import (
    Any,
    Mapping,
    Optional,
)

from ai.backend.manager.actions.action import BaseActionResult

from .base import VFolderAction


class CreateUploadSessionAction(VFolderAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    path: str
    size: str

    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    # def operation_type(self) -> str:
    #     return "create"


class CreateUploadSessionActionResult(BaseActionResult):
    pass


class CreateDownloadSessionAction(VFolderAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    path: str
    archive: bool

    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


class CreateDownloadSessionActionResult(BaseActionResult):
    pass


class ListFilesAction(VFolderAction):
    vfolder_uuid: uuid.UUID

    path: str


class ListFilesActionResult(BaseActionResult):
    pass


class RenameFileAction(VFolderAction):
    user_uuid: uuid.UUID
    keypair_resource_policy: Mapping[str, Any]

    vfolder_uuid: uuid.UUID

    target_path: str
    new_name: str


class RenameFileActionResult(BaseActionResult):
    pass


class DeleteFilesAction(VFolderAction):
    vfolder_uuid: uuid.UUID

    files: list[str]
    recursive: bool = False


class DeleteFilesActionResult(BaseActionResult):
    pass


class MkdirAction(VFolderAction):
    vfolder_uuid: uuid.UUID

    path: str | list[str]
    parents: bool = True
    exist_ok: bool = False


class MkdirActionResult(BaseActionResult):
    pass
