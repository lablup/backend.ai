from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, TypeAlias, cast, override

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, relationship, selectinload, with_loader_criteria
from sqlalchemy.sql.expression import false, true

from ai.backend.common.types import AccessKey, AgentId, ResourceSlot

from .base import (
    Base,
    CurvePublicKeyColumn,
    EnumType,
    ResourceSlotColumn,
    mapper_registry,
)
from .kernel import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, KernelRow
from .keypair import KeyPairRow
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    ScopeType,
    UserScope,
    get_predefined_roles_in_scope,
)
from .rbac.context import ClientContext
from .rbac.permission_defs import AgentPermission, ScalingGroupPermission

if TYPE_CHECKING:
    pass


__all__: Sequence[str] = (
    "agents",
    "AgentRow",
    "AgentStatus",
    "recalc_agent_resource_occupancy",
    "list_schedulable_agents_by_sgroup",
)


class AgentStatus(enum.Enum):
    ALIVE = 0
    LOST = 1
    RESTARTING = 2
    TERMINATED = 3


agents = sa.Table(
    "agents",
    mapper_registry.metadata,
    sa.Column("id", sa.String(length=64), primary_key=True),
    sa.Column(
        "status", EnumType(AgentStatus), nullable=False, index=True, default=AgentStatus.ALIVE
    ),
    sa.Column("status_changed", sa.DateTime(timezone=True), nullable=True),
    sa.Column("region", sa.String(length=64), index=True, nullable=False),
    sa.Column(
        "scaling_group",
        sa.ForeignKey("scaling_groups.name"),
        index=True,
        nullable=False,
        server_default="default",
        default="default",
    ),
    sa.Column("schedulable", sa.Boolean(), nullable=False, server_default=true(), default=True),
    sa.Column("available_slots", ResourceSlotColumn(), nullable=False),
    sa.Column("occupied_slots", ResourceSlotColumn(), nullable=False),
    sa.Column("addr", sa.String(length=128), nullable=False),
    sa.Column("public_host", sa.String(length=256), nullable=True),
    sa.Column("public_key", CurvePublicKeyColumn(), nullable=True),
    sa.Column("first_contact", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("lost_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("version", sa.String(length=64), nullable=False),
    sa.Column("architecture", sa.String(length=32), nullable=False),
    sa.Column("compute_plugins", pgsql.JSONB(), nullable=False, default={}),
    sa.Column(
        "auto_terminate_abusing_kernel",
        sa.Boolean(),
        nullable=False,
        server_default=false(),
        default=False,
    ),
)


class AgentRow(Base):
    __table__ = agents
    kernels = relationship("KernelRow", back_populates="agent_row")
    scaling_group_row = relationship("ScalingGroupRow", back_populates="agents")


async def list_schedulable_agents_by_sgroup(
    db_sess: SASession,
    sgroup_name: str,
) -> Sequence[AgentRow]:
    query = sa.select(AgentRow).where(
        (AgentRow.status == AgentStatus.ALIVE)
        & (AgentRow.scaling_group == sgroup_name)
        & (AgentRow.schedulable == true()),
    )

    result = await db_sess.execute(query)
    return result.scalars().all()


async def recalc_agent_resource_occupancy(db_session: SASession, agent_id: AgentId) -> None:
    _stmt = (
        sa.select(KernelRow)
        .where(
            (KernelRow.agent == agent_id)
            & (KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        .options(load_only(KernelRow.occupied_slots))
    )
    kernel_rows = cast(list[KernelRow], (await db_session.scalars(_stmt)).all())
    occupied_slots = ResourceSlot()
    for row in kernel_rows:
        occupied_slots += row.occupied_slots

    _update_stmt = (
        sa.update(AgentRow).values(occupied_slots=occupied_slots).where(AgentRow.id == agent_id)
    )
    await db_session.execute(_update_stmt)


async def recalc_agent_resource_occupancy_using_orm(
    db_session: SASession, agent_id: AgentId
) -> None:
    agent_query = (
        sa.select(AgentRow)
        .where(AgentRow.id == agent_id)
        .options(
            selectinload(AgentRow.kernels),
            with_loader_criteria(
                KernelRow, KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)
            ),
        )
    )
    occupied_slots = ResourceSlot()
    agent_row = cast(AgentRow, await db_session.scalar(agent_query))
    kernel_rows = cast(list[KernelRow], agent_row.kernels)
    for kernel in kernel_rows:
        if kernel.status in AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES:
            occupied_slots += kernel.occupied_slots
    agent_row.occupied_slots = occupied_slots


WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)
# TypeAlias is deprecated since 3.12 but mypy does not follow up yet

OWNER_PERMISSIONS: frozenset[AgentPermission] = frozenset([perm for perm in AgentPermission])
ADMIN_PERMISSIONS: frozenset[AgentPermission] = frozenset([perm for perm in AgentPermission])
MONITOR_PERMISSIONS: frozenset[AgentPermission] = frozenset([
    AgentPermission.READ_ATTRIBUTE,
    AgentPermission.UPDATE_ATTRIBUTE,
])
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[AgentPermission] = frozenset([
    AgentPermission.CREATE_COMPUTE_SESSION,
    AgentPermission.CREATE_SERVICE,
])
MEMBER_PERMISSIONS: frozenset[AgentPermission] = frozenset([
    AgentPermission.CREATE_COMPUTE_SESSION,
    AgentPermission.CREATE_SERVICE,
])


@dataclass
class AgentPermissionContext(AbstractPermissionContext[AgentPermission, AgentRow, AgentId]):
    from .scaling_group import ScalingGroupPermissionContext

    sgroup_permission_ctx: Optional[ScalingGroupPermissionContext] = None

    @property
    def query_condition(self) -> Optional[WhereClauseType]:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: Optional[WhereClauseType],
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, AgentRow.id.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, AgentRow.id.in_(self.object_id_to_overriding_permission_map.keys())
            )

        if self.sgroup_permission_ctx is not None:
            if cond is not None:
                sgroup_names = self.sgroup_permission_ctx.sgroup_to_permissions_map.keys()
                cond = cond & AgentRow.scaling_group.in_(sgroup_names)
        return cond

    def apply_sgroup_permission_ctx(
        self, sgroup_permission_ctx: ScalingGroupPermissionContext
    ) -> None:
        self.sgroup_permission_ctx = sgroup_permission_ctx

    async def build_query(self) -> Optional[sa.sql.Select]:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(AgentRow).where(cond)

    async def calculate_final_permission(self, rbac_obj: AgentRow) -> frozenset[AgentPermission]:
        agent_row = rbac_obj
        agent_id = cast(AgentId, agent_row.id)
        permissions: set[AgentPermission] = set()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(agent_id)
        ) is not None:
            permissions = set(overriding_perm)
        else:
            permissions |= self.object_id_to_additional_permission_map.get(agent_id, set())

        if self.sgroup_permission_ctx is not None:
            sgroup_permission_map = self.sgroup_permission_ctx.sgroup_to_permissions_map
            sgroup_perms = sgroup_permission_map.get(agent_row.scaling_group)
            if sgroup_perms is None or ScalingGroupPermission.AGENT_PERMISSIONS not in sgroup_perms:
                permissions = set()

        return frozenset(permissions)


class AgentPermissionContextBuilder(
    AbstractPermissionContextBuilder[AgentPermission, AgentPermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[AgentPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        permissions = await self._calculate_permission_by_predefined_roles(roles)
        return permissions

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> AgentPermissionContext:
        from .domain import DomainRow

        perm_ctx = AgentPermissionContext()
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
    ) -> AgentPermissionContext:
        from .scaling_group import ScalingGroupForDomainRow, ScalingGroupRow

        permissions = await self.calculate_permission(ctx, scope)
        aid_permission_map: dict[AgentId, frozenset[AgentPermission]] = {}

        _stmt = (
            sa.select(ScalingGroupForDomainRow)
            .where(ScalingGroupForDomainRow.domain == scope.domain_name)
            .options(
                joinedload(ScalingGroupForDomainRow.sgroup_row).options(
                    selectinload(ScalingGroupRow.agents)
                )
            )
        )
        for row in await self.db_session.scalars(_stmt):
            sg_row = cast(ScalingGroupRow, row.sgroup_row)
            for ag in sg_row.agents:
                aid_permission_map[ag.id] = permissions
        return AgentPermissionContext(object_id_to_additional_permission_map=aid_permission_map)

    @override
    async def build_ctx_in_project_scope(
        self,
        ctx: ClientContext,
        scope: ProjectScope,
    ) -> AgentPermissionContext:
        from .scaling_group import ScalingGroupForProjectRow, ScalingGroupRow

        permissions = await self.calculate_permission(ctx, scope)
        aid_permission_map: dict[AgentId, frozenset[AgentPermission]] = {}

        _stmt = (
            sa.select(ScalingGroupForProjectRow)
            .where(ScalingGroupForProjectRow.group == scope.project_id)
            .options(
                joinedload(ScalingGroupForProjectRow.sgroup_row).options(
                    selectinload(ScalingGroupRow.agents)
                )
            )
        )
        for row in await self.db_session.scalars(_stmt):
            sg_row = cast(ScalingGroupRow, row.sgroup_row)
            for ag in sg_row.agents:
                aid_permission_map[ag.id] = permissions
        return AgentPermissionContext(object_id_to_additional_permission_map=aid_permission_map)

    @override
    async def build_ctx_in_user_scope(
        self,
        ctx: ClientContext,
        scope: UserScope,
    ) -> AgentPermissionContext:
        from .scaling_group import ScalingGroupForKeypairsRow, ScalingGroupRow

        permissions = await self.calculate_permission(ctx, scope)
        aid_permission_map: dict[AgentId, frozenset[AgentPermission]] = {}

        _kp_stmt = (
            sa.select(KeyPairRow)
            .where(KeyPairRow.user == scope.user_id)
            .options(load_only(KeyPairRow.access_key))
        )
        kp_rows = (await self.db_session.scalars(_kp_stmt)).all()
        access_keys = cast(list[AccessKey], [r.access_key for r in kp_rows])

        _stmt = (
            sa.select(ScalingGroupForKeypairsRow)
            .where(ScalingGroupForKeypairsRow.access_key.in_(access_keys))
            .options(
                joinedload(ScalingGroupForKeypairsRow.sgroup_row).options(
                    selectinload(ScalingGroupRow.agents)
                )
            )
        )
        for row in await self.db_session.scalars(_stmt):
            sg_row = cast(ScalingGroupRow, row.sgroup_row)
            for ag in sg_row.agents:
                aid_permission_map[ag.id] = permissions
        return AgentPermissionContext(object_id_to_additional_permission_map=aid_permission_map)

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[AgentPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[AgentPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[AgentPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[AgentPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[AgentPermission]:
        return MEMBER_PERMISSIONS


async def get_permission_ctx(
    db_conn: SAConnection,
    ctx: ClientContext,
    target_scope: ScopeType,
    requested_permission: AgentPermission,
) -> AgentPermissionContext:
    from .scaling_group import ScalingGroupPermissionContextBuilder

    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        sgroup_perm_ctx = await ScalingGroupPermissionContextBuilder(db_session).build(
            ctx, target_scope, ScalingGroupPermission.AGENT_PERMISSIONS
        )

        builder = AgentPermissionContextBuilder(db_session)
        permission_ctx = await builder.build(ctx, target_scope, requested_permission)
        permission_ctx.apply_sgroup_permission_ctx(sgroup_perm_ctx)
    return permission_ctx
