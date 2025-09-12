from __future__ import annotations

import logging
from collections.abc import Container, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    List,
    Optional,
    Self,
    Sequence,
    TypeAlias,
    TypedDict,
    cast,
    override,
)

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, relationship

from ai.backend.common import msgpack
from ai.backend.common.types import VFolderHostPermissionMap
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.domain.types import DomainCreator, DomainData

from ..defs import RESERVED_DOTFILES
from .base import (
    Base,
    ResourceSlotColumn,
    SlugType,
    VFolderHostPermissionColumn,
    mapper_registry,
)
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    RBACModel,
    ScopeType,
    UserScope,
    get_predefined_roles_in_scope,
    required_permission,
)
from .rbac.context import ClientContext
from .rbac.permission_defs import DomainPermission

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "domains",
    "DomainRow",
    "DomainDotfile",
    "MAXIMUM_DOTFILE_SIZE",
    "query_domain_dotfiles",
    "verify_dotfile_name",
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB

domains = sa.Table(
    "domains",
    mapper_registry.metadata,
    sa.Column("name", SlugType(length=64, allow_unicode=True, allow_dot=True), primary_key=True),
    sa.Column("description", sa.String(length=512)),
    sa.Column("is_active", sa.Boolean, default=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    ),
    # TODO: separate resource-related fields with new domain resource policy table when needed.
    sa.Column("total_resource_slots", ResourceSlotColumn(), default=dict),
    sa.Column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default=dict,
    ),
    sa.Column("allowed_docker_registries", pgsql.ARRAY(sa.String), nullable=False, default=list),
    #: Field for synchronization with external services.
    sa.Column("integration_id", sa.String(length=512)),
    # dotfiles column, \x90 means empty list in msgpack
    sa.Column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    ),
)


def row_to_data(row: DomainRow | Row) -> DomainData:
    return DomainData(
        name=row.name,
        description=row.description,
        is_active=row.is_active,
        created_at=row.created_at,
        modified_at=row.modified_at,
        total_resource_slots=row.total_resource_slots,
        allowed_vfolder_hosts=row.allowed_vfolder_hosts,
        allowed_docker_registries=row.allowed_docker_registries,
        integration_id=row.integration_id,
        dotfiles=row.dotfiles,
    )


class DomainRow(Base):
    __table__ = domains
    sessions = relationship("SessionRow", back_populates="domain")
    users = relationship("UserRow", back_populates="domain")
    groups = relationship("GroupRow", back_populates="domain")
    sgroup_for_domains_rows = relationship(
        "ScalingGroupForDomainRow",
        back_populates="domain_row",
    )
    networks = relationship(
        "NetworkRow",
        back_populates="domain_row",
        primaryjoin="DomainRow.name==foreign(NetworkRow.domain_name)",
    )

    @classmethod
    def from_input(cls, input: DomainCreator) -> Self:
        return cls(
            name=input.name,
            description=input.description,
            is_active=input.is_active if input.is_active is not None else True,
            total_resource_slots=input.total_resource_slots if input.total_resource_slots else {},
            allowed_vfolder_hosts=input.allowed_vfolder_hosts
            if input.allowed_vfolder_hosts
            else {},
            allowed_docker_registries=input.allowed_docker_registries
            if input.allowed_docker_registries
            else [],
            integration_id=input.integration_id,
            dotfiles=input.dotfiles if input.dotfiles else b"\x90",
        )

    def to_data(self) -> DomainData:
        return row_to_data(self)


@dataclass
class DomainModel(RBACModel[DomainPermission]):
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    modified_at: datetime

    _total_resource_slots: Optional[dict]
    _allowed_vfolder_hosts: VFolderHostPermissionMap
    _allowed_docker_registries: list[str]
    _integration_id: Optional[str]
    _dotfiles: str

    orm_obj: DomainRow
    _permissions: frozenset[DomainPermission] = field(default_factory=frozenset)

    @property
    def permissions(self) -> Container[DomainPermission]:
        return self._permissions

    @property
    @required_permission(DomainPermission.READ_SENSITIVE_ATTRIBUTE)
    def total_resource_slots(self) -> Optional[dict]:
        return self._total_resource_slots

    @property
    @required_permission(DomainPermission.READ_SENSITIVE_ATTRIBUTE)
    def allowed_vfolder_hosts(self) -> VFolderHostPermissionMap:
        return self._allowed_vfolder_hosts

    @property
    @required_permission(DomainPermission.READ_SENSITIVE_ATTRIBUTE)
    def allowed_docker_registries(self) -> list[str]:
        return self._allowed_docker_registries

    @property
    @required_permission(DomainPermission.READ_SENSITIVE_ATTRIBUTE)
    def integration_id(self) -> Optional[str]:
        return self._integration_id

    @property
    @required_permission(DomainPermission.READ_SENSITIVE_ATTRIBUTE)
    def dotfiles(self) -> str:
        return self._dotfiles

    @classmethod
    def from_row(cls, row: DomainRow, permissions: Iterable[DomainPermission]) -> Self:
        return cls(
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            modified_at=row.modified_at,
            _total_resource_slots=row.total_resource_slots,
            _allowed_vfolder_hosts=row.allowed_vfolder_hosts,
            _allowed_docker_registries=row.allowed_docker_registries,
            _integration_id=row.integration_id,
            _dotfiles=row.dotfiles,
            _permissions=frozenset(permissions),
            orm_obj=row,
        )


class DomainDotfile(TypedDict):
    data: str
    path: str
    perm: str


async def query_domain_dotfiles(
    conn: SAConnection,
    name: str,
) -> tuple[List[DomainDotfile], int]:
    query = sa.select([domains.c.dotfiles]).select_from(domains).where(domains.c.name == name)
    packed_dotfile = await conn.scalar(query)
    if packed_dotfile is None:
        return [], MAXIMUM_DOTFILE_SIZE
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


def verify_dotfile_name(dotfile: str) -> bool:
    if dotfile in RESERVED_DOTFILES:
        return False
    return True


ALL_DOMAIN_PERMISSIONS = frozenset([perm for perm in DomainPermission])
OWNER_PERMISSIONS: frozenset[DomainPermission] = ALL_DOMAIN_PERMISSIONS
ADMIN_PERMISSIONS: frozenset[DomainPermission] = ALL_DOMAIN_PERMISSIONS
MONITOR_PERMISSIONS: frozenset[DomainPermission] = frozenset([
    DomainPermission.READ_ATTRIBUTE,
    DomainPermission.UPDATE_ATTRIBUTE,
])
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[DomainPermission] = frozenset([
    DomainPermission.READ_ATTRIBUTE
])
MEMBER_PERMISSIONS: frozenset[DomainPermission] = frozenset([DomainPermission.READ_ATTRIBUTE])

WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)


@dataclass
class DomainPermissionContext(AbstractPermissionContext[DomainPermission, DomainRow, str]):
    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, DomainRow.name.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, DomainRow.name.in_(self.object_id_to_overriding_permission_map.keys())
            )
        return cond

    async def build_query(self) -> sa.sql.Select | None:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(DomainRow).where(cond)

    async def calculate_final_permission(self, rbac_obj: DomainRow) -> frozenset[DomainPermission]:
        domain_row = rbac_obj
        domain_name = cast(str, domain_row.name)
        permissions: frozenset[DomainPermission] = frozenset()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(domain_name)
        ) is not None:
            permissions = overriding_perm
        else:
            permissions |= self.object_id_to_additional_permission_map.get(domain_name, set())
        return permissions


class DomainPermissionContextBuilder(
    AbstractPermissionContextBuilder[DomainPermission, DomainPermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[DomainPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        permissions = await self._calculate_permission_by_predefined_roles(roles)
        return permissions

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> DomainPermissionContext:
        from .domain import DomainRow

        perm_ctx = DomainPermissionContext()
        _domain_query_stmt = sa.select(DomainRow).options(load_only(DomainRow.name))
        for row in await self.db_session.scalars(_domain_query_stmt):
            to_be_merged = await self.build_ctx_in_domain_scope(ctx, DomainScope(row.name))
            perm_ctx.merge(to_be_merged)
        return perm_ctx

    @override
    async def build_ctx_in_domain_scope(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> DomainPermissionContext:
        permissions = await self.calculate_permission(ctx, scope)
        return DomainPermissionContext(
            object_id_to_additional_permission_map={scope.domain_name: permissions}
        )

    @override
    async def build_ctx_in_project_scope(
        self, ctx: ClientContext, scope: ProjectScope
    ) -> DomainPermissionContext:
        return DomainPermissionContext()

    @override
    async def build_ctx_in_user_scope(
        self, ctx: ClientContext, scope: UserScope
    ) -> DomainPermissionContext:
        return DomainPermissionContext()

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[DomainPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[DomainPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[DomainPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[DomainPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[DomainPermission]:
        return MEMBER_PERMISSIONS


async def get_permission_ctx(
    target_scope: ScopeType,
    requested_permission: DomainPermission,
    *,
    ctx: ClientContext,
    db_session: SASession,
) -> DomainPermissionContext:
    builder = DomainPermissionContextBuilder(db_session)
    permission_ctx = await builder.build(ctx, target_scope, requested_permission)
    return permission_ctx


async def get_domains(
    target_scope: ScopeType,
    requested_permission: DomainPermission,
    domain_names: Optional[Iterable[str]] = None,
    *,
    ctx: ClientContext,
    db_session: SASession,
) -> list[DomainModel]:
    ret: list[DomainModel] = []
    permission_ctx = await get_permission_ctx(
        target_scope, requested_permission, ctx=ctx, db_session=db_session
    )
    cond = permission_ctx.query_condition
    if cond is None:
        return ret
    query_stmt = sa.select(DomainRow).where(cond)
    if domain_names is not None:
        query_stmt = query_stmt.where(DomainRow.name.in_(domain_names))
    async for row in await db_session.stream_scalars(query_stmt):
        permissions = await permission_ctx.calculate_final_permission(row)
        ret.append(DomainModel.from_row(row, permissions))
    return ret
