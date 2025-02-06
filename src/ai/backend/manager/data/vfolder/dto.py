import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Self

from ai.backend.common.dto.manager.context import KeypairCtx, UserIdentityCtx
from ai.backend.common.dto.manager.dto import VFolderPermissionDTO
from ai.backend.common.dto.manager.request import VFolderCreateReq
from ai.backend.common.dto.manager.response import (
    VFolderCreateResponse,
    VFolderListItemRes,
    VFolderOperationStatusRes,
    VFolderOwnershipTypeRes,
)
from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.models import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)


@dataclass
class UserIdentity:
    user_uuid: uuid.UUID
    user_role: str
    user_email: str
    domain_name: str

    @classmethod
    def from_ctx(cls, ctx: UserIdentityCtx) -> Self:
        return cls(
            user_uuid=ctx.user_uuid,
            user_role=ctx.user_role,
            user_email=ctx.user_email,
            domain_name=ctx.domain_name,
        )


@dataclass
class Keypair:
    access_key: str
    resource_policy: Mapping[str, Any]

    @classmethod
    def from_ctx(cls, ctx: KeypairCtx) -> Self:
        return cls(
            access_key=ctx.access_key,
            resource_policy=ctx.resource_policy,
        )


@dataclass
class VFolderItemToCreate:
    name: str
    folder_host: Optional[str]
    usage_mode: VFolderUsageMode
    permission: VFolderPermission
    group_id: Optional[uuid.UUID]
    cloneable: bool
    unmanaged_path: Optional[str]

    @classmethod
    def from_request(cls, request: VFolderCreateReq) -> Self:
        return cls(
            name=request.name,
            folder_host=request.folder_host,
            usage_mode=request.usage_mode,
            permission=VFolderPermission(request.permission),
            group_id=request.group_id,
            cloneable=request.cloneable,
            unmanaged_path=request.unmanaged_path,
        )


@dataclass
class VFolderInfo:
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
    user: Optional[str]
    group: Optional[str]
    cloneable: bool
    status: VFolderOperationStatus

    def to_vfolder_create_response(self) -> VFolderCreateResponse:
        return VFolderCreateResponse(
            id=self.id,
            name=self.name,
            quota_scope_id=str(self.quota_scope_id),
            host=self.host,
            usage_mode=self.usage_mode,
            permission=VFolderPermissionDTO(self.permission),
            max_size=self.max_size,
            creator=self.creator,
            ownership_type=self.ownership_type,
            user=self.user,
            group=self.group,
            cloneable=self.cloneable,
            status=VFolderOperationStatusRes(self.status),
        )


@dataclass
class VFolderListItem:  # TODO: Why VFolderListItem is needed?
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
    user: Optional[str]
    group: Optional[str]
    cloneable: bool
    status: VFolderOperationStatus
    is_owner: bool
    user_email: str
    group_name: str
    type: str  # legacy
    max_files: int
    cur_size: int

    def to_response(self) -> VFolderListItemRes:
        return VFolderListItemRes(
            id=self.id,
            name=self.name,
            quota_scope_id=self.quota_scope_id,
            host=self.host,
            usage_mode=self.usage_mode,
            created_at=self.created_at,
            permission=VFolderPermissionDTO(self.permission),
            max_size=self.max_size,
            creator=self.creator,
            ownership_type=VFolderOwnershipTypeRes(self.ownership_type),
            user=self.user,
            group=self.group,
            cloneable=self.cloneable,
            status=VFolderOperationStatusRes(self.status),
            is_owner=self.is_owner,
            user_email=self.user_email,
            group_name=self.group_name,
            type=self.type,
            max_files=self.max_files,
            cur_size=self.cur_size,
        )
