import uuid
from typing import Any, Mapping, Optional, Self

from aiohttp import web
from pydantic import AliasChoices, BaseModel, Field

from ai.backend.common import typed_validators as tv
from ai.backend.common.api_handlers import MiddlewareParam
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.api.vfolders.dtos import (
    Keypair,
    UserIdentity,
    VFolderCreateRequirements,
)
from ai.backend.manager.models import (
    VFolderPermission,
)


class VFolderCreateData(BaseModel):
    name: tv.VFolderName = Field(
        description="Name of the vfolder",
    )
    folder_host: Optional[str] = Field(
        validation_alias=AliasChoices("host", "folder_host"),
        default=None,
    )
    usage_mode: VFolderUsageMode = Field(default=VFolderUsageMode.GENERAL)
    permission: VFolderPermission = Field(default=VFolderPermission.READ_WRITE)
    unmanaged_path: Optional[str] = Field(
        validation_alias=AliasChoices("unmanaged_path", "unmanagedPath"),
        default=None,
    )
    group_id: Optional[uuid.UUID] = Field(
        validation_alias=AliasChoices("group", "groupId", "group_id"),
        default=None,
    )
    cloneable: bool = Field(
        default=False,
    )

    def to_dto(self) -> VFolderCreateRequirements:
        return VFolderCreateRequirements(
            name=self.name,
            folder_host=self.folder_host,
            usage_mode=self.usage_mode,
            permission=self.permission,
            group_id=self.group_id,
            cloneable=self.cloneable,
            unmanaged_path=self.unmanaged_path,
        )


class VFolderListRequestedGroupId(BaseModel):
    group_id: Optional[uuid.UUID] = Field(
        default=None, validation_alias=AliasChoices("group_id", "groupId")
    )


class RenameVFolderId(BaseModel):
    vfolder_id: uuid.UUID = Field(validation_alias=AliasChoices("vfolder_id", "vfolderId", "id"))


class VFolderNewName(BaseModel):
    new_name: tv.VFolderName = Field(
        description="Name of the vfolder",
    )


class DeleteVFolderId(BaseModel):
    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("vfolder_id", "vfolderId", "id"),
        description="Target vfolder id to soft-delete, to go to trash bin",
    )


class UserIdentityModel(MiddlewareParam):
    user_uuid: uuid.UUID
    user_role: str
    user_email: str
    domain_name: str

    @classmethod
    def from_request(cls, request: web.Request) -> Self:
        return cls(
            user_uuid=request["user"]["uuid"],
            user_role=request["user"]["role"],
            user_email=request["user"]["email"],
            domain_name=request["user"]["domain_name"],
        )

    def to_dto(self) -> UserIdentity:
        return UserIdentity(
            user_uuid=self.user_uuid,
            user_role=self.user_role,
            user_email=self.user_email,
            domain_name=self.domain_name,
        )


class KeypairModel(MiddlewareParam):
    access_key: str
    resource_policy: Mapping[str, Any]

    @classmethod
    def from_request(cls, request: web.Request) -> Self:
        return cls(
            access_key=request["keypair"]["access_key"],
            resource_policy=request["keypair"]["resource_policy"],
        )

    def to_dto(self) -> Keypair:
        return Keypair(access_key=self.access_key, resource_policy=self.resource_policy)
