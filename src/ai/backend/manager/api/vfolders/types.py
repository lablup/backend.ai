import uuid
from dataclasses import dataclass
from typing import Annotated, Any, Mapping

from pydantic import AliasChoices, BaseModel, Field

from ai.backend.common import typed_validators as tv
from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.api.utils import (
    BaseResponseModel,
)
from ai.backend.manager.models import (
    ProjectType,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)


class NoContentResponseModel(BaseResponseModel):
    status: Annotated[int, Field(strict=True, exclude=True, ge=100, lt=600)] = 204


class CreatedResponseModel(BaseResponseModel):
    status: Annotated[int, Field(strict=True, exclude=True, ge=100, lt=600)] = 201


class VFolderCreateRequestModel(BaseModel):
    name: tv.VFolderName
    folder_host: str | None = Field(
        validation_alias=AliasChoices("host", "folder_host"),
        default=None,
    )
    usage_mode: VFolderUsageMode = Field(default=VFolderUsageMode.GENERAL)
    permission: VFolderPermission = Field(default=VFolderPermission.READ_WRITE)
    unmanaged_path: str | None = Field(
        validation_alias=AliasChoices("unmanaged_path", "unmanagedPath"),
        default=None,
    )
    group: str | uuid.UUID | None = Field(
        validation_alias=AliasChoices("group", "groupId", "group_id"),
        default=None,
    )
    cloneable: bool = Field(
        default=False,
    )


class VFolderListRequestModel(BaseModel):
    all: bool = Field(default=False)
    group_id: uuid.UUID | str | None = Field(
        default=None, validation_alias=AliasChoices("group_id", "groupId")
    )
    owner_user_email: str | None = Field(
        default=None, validation_alias=AliasChoices("owner_user_email", "ownerUserEmail")
    )


class VFolderRenameRequestModel(BaseModel):
    new_name: tv.VFolderName


class VFolderDeleteRequestModel(BaseModel):
    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("vfolder_id", "vfolderId", "id"),
        description="Target vfolder id to soft-delete, to go to trash bin",
    )


@dataclass
class UserIdentity:
    user_uuid: uuid.UUID
    user_role: str
    domain_name: str


@dataclass
class Keypair:
    access_key: str
    resource_policy: Mapping[str, Any]


@dataclass
class VFolderCreateRequirements:
    name: str
    folder_host: str | None
    usage_mode: VFolderUsageMode
    permission: VFolderPermission
    group: str | uuid.UUID | None
    cloneable: bool
    unmanaged_path: str | None

    @classmethod
    def from_params(cls, params: VFolderCreateRequestModel):
        cls.name = params.name
        cls.folder_host = params.folder_host if params.folder_host else None
        cls.usage_mode = params.usage_mode
        cls.permission = params.permission
        cls.group = params.group if params.group else None
        cls.cloneable = params.cloneable
        cls.unmanaged_path = params.unmanaged_path if params.unmanaged_path else None


@dataclass
class VFolderMetadata:
    id: str
    name: str
    quota_scope_id: QuotaScopeID
    host: str
    usage_mode: VFolderUsageMode
    created_at: str
    permission: VFolderPermission
    max_size: int  # migrated to quota scopes, no longer valid
    creator: str
    ownership_type: VFolderOwnershipType
    user: str | None
    group: str | None
    cloneable: bool
    status: VFolderOperationStatus


class VFolderCreateResponseModel(BaseResponseModel):
    id: str
    name: str
    quota_scope_id: str
    host: str
    usage_mode: VFolderUsageMode
    permission: str
    max_size: int = 0  # migrated to quota scopes, no longer valid
    creator: str
    ownership_type: str
    user: str | None
    group: str | None
    cloneable: bool
    status: VFolderOperationStatus = Field(default=VFolderOperationStatus.READY)

    @classmethod
    def from_vfolder_metadata(cls, data: VFolderMetadata):
        return cls(
            id=data.id,
            name=data.name,
            quota_scope_id=str(data.quota_scope_id),
            host=data.host,
            usage_mode=data.usage_mode,
            permission=data.permission,
            max_size=data.max_size,
            creator=data.creator,
            ownership_type=data.ownership_type,
            user=data.user,
            group=data.group,
            cloneable=data.cloneable,
            status=data.status,
        )


@dataclass
class VFolderListItem:
    id: str
    name: str
    quota_scope_id: str
    host: str
    usage_mode: VFolderUsageMode
    created_at: str
    permission: VFolderPermission
    max_size: int
    creator: str
    ownership_type: VFolderOwnershipType
    user: str | None
    group: str | None
    cloneable: bool
    status: VFolderOperationStatus
    is_owner: bool
    user_email: str
    group_name: str
    type: str  # legacy
    max_files: int
    cur_size: int


@dataclass
class VFolderList:
    entries: list[VFolderListItem]


class VFolderListResponseModel(BaseResponseModel):
    root: list[VFolderListItem] = Field(default_factory=list)

    @classmethod
    def from_dataclass(cls, vfolder_list: VFolderList) -> "VFolderListResponseModel":
        return cls(root=vfolder_list.entries)


@dataclass
class VFolderCapabilityInfo:
    max_vfolder_count: int
    max_quota_scope_size: int
    ownership_type: str
    quota_scope_id: QuotaScopeID
    group_uuid: uuid.UUID | None = None
    group_type: ProjectType | None = None
