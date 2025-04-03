from __future__ import annotations

import logging
from collections.abc import Container, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Optional,
    Self,
    Sequence,
    TypeAlias,
    TypedDict,
    cast,
    override,
)

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, relationship

from ai.backend.common import msgpack
from ai.backend.common.types import ResourceSlot, Sentinel, VFolderHostPermissionMap
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.types import OptionalState, State, TriState

from ..defs import RESERVED_DOTFILES
from .base import (
    Base,
    ResourceSlotColumn,
    SlugType,
    VFolderHostPermissionColumn,
    batch_result,
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
from .scaling_group import ScalingGroup
from .user import UserRole

if TYPE_CHECKING:
    from ai.backend.manager.services.domain.actions.create_domain import (
        CreateDomainAction,
        CreateDomainActionResult,
    )
    from ai.backend.manager.services.domain.actions.delete_domain import (
        DeleteDomainAction,
        DeleteDomainActionResult,
    )
    from ai.backend.manager.services.domain.actions.modify_domain import (
        ModifyDomainAction,
        ModifyDomainActionResult,
    )
    from ai.backend.manager.services.domain.actions.purge_domain import (
        PurgeDomainAction,
        PurgeDomainActionResult,
    )
    from ai.backend.manager.services.domain.types import DomainData

    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "domains",
    "DomainRow",
    "Domain",
    "DomainInput",
    "ModifyDomainInput",
    "CreateDomain",
    "ModifyDomain",
    "DeleteDomain",
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
    sa.Column("total_resource_slots", ResourceSlotColumn(), default="{}"),
    sa.Column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default={},
    ),
    sa.Column("allowed_docker_registries", pgsql.ARRAY(sa.String), nullable=False, default="{}"),
    #: Field for synchronization with external services.
    sa.Column("integration_id", sa.String(length=512)),
    # dotfiles column, \x90 means empty list in msgpack
    sa.Column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    ),
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


class Domain(graphene.ObjectType):
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    total_resource_slots = graphene.JSONString()
    allowed_vfolder_hosts = graphene.JSONString()
    allowed_docker_registries = graphene.List(lambda: graphene.String)
    integration_id = graphene.String()

    # Dynamic fields.
    scaling_groups = graphene.List(lambda: graphene.String)

    async def resolve_scaling_groups(self, info: graphene.ResolveInfo) -> Sequence[str]:
        sgroups = await ScalingGroup.load_by_domain(info.context, self.name)
        return [sg.name for sg in sgroups]

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[Domain]:
        if row is None:
            return None
        return cls(
            name=row["name"],
            description=row["description"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            total_resource_slots=(
                row["total_resource_slots"].to_json()
                if row["total_resource_slots"] is not None
                else {}
            ),
            allowed_vfolder_hosts=row["allowed_vfolder_hosts"].to_json(),
            allowed_docker_registries=row["allowed_docker_registries"],
            integration_id=row["integration_id"],
        )

    @classmethod
    def from_dto(cls, dto: DomainData) -> Domain:
        return cls(
            name=dto.name,
            description=dto.description,
            is_active=dto.is_active,
            created_at=dto.created_at,
            modified_at=dto.modified_at,
            total_resource_slots=dto.total_resource_slots.to_json()
            if dto.total_resource_slots
            else {},
            allowed_vfolder_hosts=dto.allowed_vfolder_hosts.to_json(),
            allowed_docker_registries=dto.allowed_docker_registries,
            integration_id=dto.integration_id,
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        is_active: Optional[bool] = None,
    ) -> Sequence[Domain]:
        async with ctx.db.begin_readonly() as conn:
            query = sa.select([domains]).select_from(domains)
            if is_active is not None:
                query = query.where(domains.c.is_active == is_active)
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_name(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
        *,
        is_active: Optional[bool] = None,
    ) -> Sequence[Optional[Domain]]:
        async with ctx.db.begin_readonly() as conn:
            query = sa.select([domains]).select_from(domains).where(domains.c.name.in_(names))
            if is_active is not None:
                query = query.where(domains.c.is_active == is_active)
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                names,
                lambda row: row["name"],
            )


class DomainInput(graphene.InputObjectType):
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    total_resource_slots = graphene.JSONString(required=False, default_value={})
    allowed_vfolder_hosts = graphene.JSONString(required=False, default_value={})
    allowed_docker_registries = graphene.List(
        lambda: graphene.String, required=False, default_value=[]
    )
    integration_id = graphene.String(required=False, default_value=None)

    def to_action(self, domain_name: str) -> CreateDomainAction:
        def value_or_none(value):
            return value if value is not Undefined else None

        def define_state(value):
            if value is None:
                return State.NULLIFY
            elif value is Undefined:
                return State.NOP
            else:
                return State.UPDATE

        return CreateDomainAction(
            name=domain_name,
            description=TriState(
                "description",
                define_state(self.description),
                value_or_none(self.description),
            ),
            is_active=OptionalState(
                "is_active", define_state(self.is_active), value_or_none(self.is_active)
            ),
            total_resource_slots=TriState(
                "total_resource_slots",
                define_state(self.total_resource_slots),
                None
                if self.total_resource_slots is Undefined
                else ResourceSlot.from_user_input(self.total_resource_slots, None),
            ),
            allowed_vfolder_hosts=OptionalState(
                "allowed_vfolder_hosts",
                define_state(self.allowed_vfolder_hosts),
                value_or_none(self.allowed_vfolder_hosts),
            ),
            allowed_docker_registries=OptionalState(
                "allowed_docker_registries",
                define_state(self.allowed_docker_registries),
                value_or_none(self.allowed_vfolder_hosts),
            ),
            integration_id=TriState(
                "integration_id",
                define_state(self.integration_id),
                value_or_none(self.integration_id),
            ),
        )


class ModifyDomainInput(graphene.InputObjectType):
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    allowed_vfolder_hosts = graphene.JSONString(required=False)
    allowed_docker_registries = graphene.List(lambda: graphene.String, required=False)
    integration_id = graphene.String(required=False)

    def _convert_field(
        self, field_value: Any, converter: Optional[Callable[[Any], Any]] = None
    ) -> Any | Sentinel:
        if field_value is Undefined:
            return Sentinel.TOKEN
        if converter is not None:
            return converter(field_value)
        return field_value

    def to_action(self, domain_name: str) -> ModifyDomainAction:
        def value_or_none(value):
            return value if value is not Undefined else None

        def define_state(value):
            if value is None:
                return State.NULLIFY
            elif value is Undefined:
                return State.NOP
            else:
                return State.UPDATE

        return ModifyDomainAction(
            domain_name=domain_name,
            name=OptionalState("name", define_state(self.name), value_or_none(self.name)),
            description=TriState(
                "description",
                define_state(self.description),
                value_or_none(self.description),
            ),
            is_active=OptionalState(
                "is_active", define_state(self.is_active), value_or_none(self.is_active)
            ),
            total_resource_slots=TriState(
                "total_resource_slots",
                define_state(self.total_resource_slots),
                None
                if self.total_resource_slots is Undefined
                else ResourceSlot.from_user_input(self.total_resource_slots, None),
            ),
            allowed_vfolder_hosts=OptionalState(
                "allowed_vfolder_hosts",
                define_state(self.allowed_vfolder_hosts),
                value_or_none(self.allowed_vfolder_hosts),
            ),
            allowed_docker_registries=OptionalState(
                "allowed_docker_registries",
                define_state(self.allowed_docker_registries),
                value_or_none(self.allowed_vfolder_hosts),
            ),
            integration_id=TriState(
                "integration_id",
                define_state(self.integration_id),
                value_or_none(self.integration_id),
            ),
        )


class CreateDomain(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = DomainInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    domain = graphene.Field(lambda: Domain, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: DomainInput,
    ) -> CreateDomain:
        ctx: GraphQueryContext = info.context

        action: CreateDomainAction = props.to_action(name)
        res: CreateDomainActionResult = await ctx.processors.domain.create_domain.wait_for_complete(
            action
        )

        domain_data: Optional[DomainData] = res.domain_data

        return cls(
            ok=res.success,
            msg=res.description,
            domain=Domain.from_dto(domain_data) if domain_data else None,
        )


class ModifyDomain(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyDomainInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    domain = graphene.Field(lambda: Domain, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyDomainInput,
    ) -> ModifyDomain:
        ctx: GraphQueryContext = info.context

        action: ModifyDomainAction = props.to_action(name)
        res: ModifyDomainActionResult = await ctx.processors.domain.modify_domain.wait_for_complete(
            action
        )

        domain_data: Optional[DomainData] = res.domain_data

        return cls(
            ok=res.success,
            msg=res.description,
            domain=Domain.from_dto(domain_data) if domain_data else None,
        )


class DeleteDomain(graphene.Mutation):
    """
    Instead of deleting the domain, just mark it as inactive.
    """

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(cls, root, info: graphene.ResolveInfo, name: str) -> DeleteDomain:
        ctx: GraphQueryContext = info.context

        action = DeleteDomainAction(name)
        res: DeleteDomainActionResult = await ctx.processors.domain.delete_domain.wait_for_complete(
            action
        )

        return cls(ok=res.success, msg=res.description)


class PurgeDomain(graphene.Mutation):
    """
    Completely delete domain from DB.

    Domain-bound kernels will also be all deleted.
    To purge domain, there should be no users and groups in the target domain.
    """

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(cls, root, info: graphene.ResolveInfo, name: str) -> PurgeDomain:
        ctx: GraphQueryContext = info.context

        action = PurgeDomainAction(name)
        res: PurgeDomainActionResult = await ctx.processors.domain.purge_domain.wait_for_complete(
            action
        )

        return cls(ok=res.success, msg=res.description)


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
