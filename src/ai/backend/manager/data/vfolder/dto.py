import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Self

from ai.backend.common.dto.manager.context import KeypairCtx, UserIdentityCtx
from ai.backend.common.dto.manager.field import (
    VFolderItemField,
)
from ai.backend.common.dto.manager.request import VFolderCreateReq
from ai.backend.common.types import VFolderUsageMode
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
    async def from_request(cls, request: VFolderCreateReq) -> Self:
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
class VFolderItem:
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

    def to_field(self) -> VFolderItemField:
        return VFolderItemField(
            id=self.id,
            name=self.name,
            quota_scope_id=self.quota_scope_id,
            host=self.host,
            usage_mode=self.usage_mode,
            created_at=self.created_at,
            permission=self.permission.to_field(),
            max_size=self.max_size,
            creator=self.creator,
            ownership_type=self.ownership_type.to_field(),
            user=self.user,
            group=self.group,
            cloneable=self.cloneable,
            status=self.status.to_field(),
            is_owner=self.is_owner,
            user_email=self.user_email,
            group_name=self.group_name,
            type=self.type,
            max_files=self.max_files,
            cur_size=self.cur_size,
        )
