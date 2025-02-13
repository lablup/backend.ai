import uuid
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, Self

from ai.backend.common.dto.manager.context import KeypairCtx, UserIdentityCtx
from ai.backend.common.dto.manager.field import (
    VFolderItemField,
)
from ai.backend.common.dto.manager.request import VFolderCreateReq
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderRow,
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

    @property
    def is_admin(self) -> bool:
        return self.user_role == UserRole.ADMIN

    @property
    def is_superadmin(self) -> bool:
        return self.user_role == UserRole.SUPERADMIN

    @property
    def has_privilege_role(self) -> bool:
        return (self.user_role == UserRole.ADMIN) or (self.user_role == UserRole.SUPERADMIN)

    @property
    def is_normal_user(self) -> bool:
        return (self.user_role != UserRole.ADMIN) and (self.user_role != UserRole.SUPERADMIN)


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
class VFolderMetadataToCreate:
    name: str
    domain_name: str
    quota_scope_id: str
    usage_mode: VFolderUsageMode
    permission: VFolderPermission
    host: str
    creator: str
    ownership_type: VFolderOwnershipType
    cloneable: bool
    user: str | None = None
    group: str | None = None
    unmanaged_path: str | None = None
    status: VFolderOperationStatus = VFolderOperationStatus.READY

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    user_email: Optional[str]
    group_name: Optional[str]
    type: str  # legacy
    max_files: int
    cur_size: int

    @classmethod
    def from_orm(
        cls,
        orm: VFolderRow,
        is_owner,
        include_relations=False,
        override_with_group_member_permission=False,
    ):
        user_email = orm.user_row.email if include_relations and orm.user_row else None
        group_name = orm.group_row.name if include_relations and orm.group_row else None
        permission = (
            orm.permission_rows.permission
            if override_with_group_member_permission
            else orm.permission
        )
        type = (
            VFolderOwnershipType.USER
            if orm.ownership_type == VFolderOwnershipType.USER
            else VFolderOwnershipType.GROUP
        )
        user = str(orm.user) if type == VFolderOwnershipType.USER else None
        group = str(orm.group) if type == VFolderOwnershipType.GROUP else None

        return cls(
            id=orm.id.hex,
            name=orm.name,
            quota_scope_id=orm.quota_scope_id,
            host=orm.host,
            usage_mode=orm.usage_mode,
            created_at=orm.created_at.isoformat(),
            permission=permission,
            max_size=orm.max_size,
            creator=orm.creator,
            ownership_type=orm.ownership_type,
            user=user,
            group=group,
            cloneable=orm.cloneable,
            status=orm.status,
            is_owner=is_owner,
            user_email=user_email,
            group_name=group_name,
            type=type,
            max_files=orm.max_files,
            cur_size=orm.cur_size,
        )

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


@dataclass
class VFolderResourceLimit:
    max_vfolder_count: int
    max_quota_scope_size: int
