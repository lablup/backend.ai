from __future__ import annotations

import logging
from collections.abc import Container, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    TypedDict,
    override,
)

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import Mapped, foreign, load_only, mapped_column, relationship

from ai.backend.common import msgpack
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.defs import RESERVED_DOTFILES
from ai.backend.manager.models.base import (
    Base,
    ResourceSlotColumn,
    SlugType,
    VFolderHostPermissionColumn,
)
from ai.backend.manager.models.rbac import (
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
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.rbac.permission_defs import DomainPermission

if TYPE_CHECKING:
    from ai.backend.manager.models.group import GroupRow
    from ai.backend.manager.models.network import NetworkRow
    from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
    from ai.backend.manager.models.session import SessionRow
    from ai.backend.manager.models.user import UserRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "MAXIMUM_DOTFILE_SIZE",
    "DomainDotfile",
    "DomainRow",
    "domains",
    "query_domain_dotfiles",
    "verify_dotfile_name",
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB


def row_to_data(row: DomainRow | Row[Any]) -> DomainData:
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


def _get_network_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.network import NetworkRow

    return DomainRow.name == foreign(NetworkRow.domain_name)


class DomainRow(Base):  # type: ignore[misc]
    __tablename__ = "domains"

    name: Mapped[str] = mapped_column(
        "name", SlugType(length=64, allow_unicode=True, allow_dot=True), primary_key=True
    )
    description: Mapped[str | None] = mapped_column("description", sa.String(length=512))
    is_active: Mapped[bool] = mapped_column("is_active", sa.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    modified_at: Mapped[datetime] = mapped_column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
        nullable=False,
    )
    # TODO: separate resource-related fields with new domain resource policy table when needed.
    total_resource_slots: Mapped[ResourceSlot] = mapped_column(
        "total_resource_slots", ResourceSlotColumn(), default=dict, nullable=False
    )
    allowed_vfolder_hosts: Mapped[VFolderHostPermissionMap] = mapped_column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default=dict,
    )
    allowed_docker_registries: Mapped[list[str]] = mapped_column(
        "allowed_docker_registries", pgsql.ARRAY(sa.String), nullable=False, default=list
    )
    #: Field for synchronization with external services.
    integration_id: Mapped[str | None] = mapped_column("integration_id", sa.String(length=512))
    # dotfiles column, \x90 means empty list in msgpack
    dotfiles: Mapped[bytes] = mapped_column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    )

    sessions: Mapped[list[SessionRow]] = relationship("SessionRow", back_populates="domain")
    users: Mapped[list[UserRow]] = relationship("UserRow", back_populates="domain")
    groups: Mapped[list[GroupRow]] = relationship("GroupRow", back_populates="domain")
    sgroup_for_domains_rows: Mapped[list[ScalingGroupForDomainRow]] = relationship(
        "ScalingGroupForDomainRow",
        back_populates="domain_row",
    )
    networks: Mapped[list[NetworkRow]] = relationship(
        "NetworkRow",
        back_populates="domain_row",
        primaryjoin=_get_network_join_condition,
    )

    def to_data(self) -> DomainData:
        return row_to_data(self)


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use DomainRow class directly for new code.
domains = DomainRow.__table__


@dataclass
class DomainModel(RBACModel[DomainPermission]):
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    modified_at: datetime

    _total_resource_slots: ResourceSlot
    _allowed_vfolder_hosts: VFolderHostPermissionMap
    _allowed_docker_registries: list[str]
    _integration_id: str | None
    _dotfiles: bytes

    orm_obj: DomainRow
    _permissions: frozenset[DomainPermission] = field(default_factory=frozenset)

    @property
    def permissions(self) -> Container[DomainPermission]:
        return self._permissions

    @property
    @required_permission(DomainPermission.READ_SENSITIVE_ATTRIBUTE)
    def total_resource_slots(self) -> ResourceSlot:
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
    def integration_id(self) -> str | None:
        return self._integration_id

    @property
    @required_permission(DomainPermission.READ_SENSITIVE_ATTRIBUTE)
    def dotfiles(self) -> bytes:
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
) -> tuple[list[DomainDotfile], int]:
    query = sa.select(DomainRow.dotfiles).where(DomainRow.name == name)
    packed_dotfile = await conn.scalar(query)
    if packed_dotfile is None:
        return [], MAXIMUM_DOTFILE_SIZE
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


def verify_dotfile_name(dotfile: str) -> bool:
    return dotfile not in RESERVED_DOTFILES


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

type WhereClauseType = sa.sql.expression.BinaryExpression[Any] | sa.sql.expression.BooleanClauseList


@dataclass
class DomainPermissionContext(AbstractPermissionContext[DomainPermission, DomainRow, str]):
    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression[Any],
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

    async def build_query(self) -> sa.sql.Select[Any] | None:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(DomainRow).where(cond)

    async def calculate_final_permission(self, rbac_obj: DomainRow) -> frozenset[DomainPermission]:
        domain_row = rbac_obj
        domain_name = domain_row.name
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
        return await self._calculate_permission_by_predefined_roles(roles)

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> DomainPermissionContext:
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
    return await builder.build(ctx, target_scope, requested_permission)


async def get_domains(
    target_scope: ScopeType,
    requested_permission: DomainPermission,
    domain_names: Iterable[str] | None = None,
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
