from __future__ import annotations

import logging
import uuid
from collections.abc import Container, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    TypedDict,
    cast,
    overload,
    override,
)

import sqlalchemy as sa
import trafaret as t
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    Mapped,
    foreign,
    joinedload,
    load_only,
    mapped_column,
    relationship,
    selectinload,
)
from sqlalchemy.orm.strategy_options import _AbstractLoad

from ai.backend.common import msgpack
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.group.types import GroupData, ProjectType
from ai.backend.manager.defs import RESERVED_DOTFILES
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    EnumValueType,
    ResourceSlotColumn,
    SlugType,
    StructuredJSONColumn,
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
from ai.backend.manager.models.rbac.permission_defs import ProjectPermission
from ai.backend.manager.models.types import (
    QueryCondition,
    QueryOption,
    load_related_field,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry

if TYPE_CHECKING:
    from ai.backend.manager.models.domain import DomainRow
    from ai.backend.manager.models.kernel import KernelRow
    from ai.backend.manager.models.network import NetworkRow
    from ai.backend.manager.models.rbac import ContainerRegistryScope
    from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
    from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow
    from ai.backend.manager.models.session import SessionRow
    from ai.backend.manager.models.user import UserRow
    from ai.backend.manager.models.vfolder import VFolderRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _get_networks_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.network import NetworkRow

    return GroupRow.id == foreign(NetworkRow.project)


def _get_vfolder_rows_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.vfolder import VFolderRow

    return GroupRow.id == foreign(VFolderRow.group)


def _get_association_container_registries_groups_join_condition() -> sa.ColumnElement[bool]:
    return GroupRow.id == foreign(AssociationContainerRegistriesGroupsRow.group_id)


__all__: Sequence[str] = (
    "MAXIMUM_DOTFILE_SIZE",
    "AssocGroupUserRow",
    "GroupDotfile",
    "GroupRow",
    "ProjectType",
    "association_groups_users",
    "groups",
    "query_group_domain",
    "query_group_dotfiles",
    "resolve_group_name_or_id",
    "verify_dotfile_name",
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB


container_registry_iv = t.Dict({}) | t.Dict({
    t.Key("registry"): t.String(),
    t.Key("project"): t.String(),
})


class AssocGroupUserRow(Base):  # type: ignore[misc]
    __tablename__ = "association_groups_users"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "group_id", name="uq_association_user_id_group_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        "user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        "group_id",
        GUID,
        sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped[UserRow] = relationship("UserRow", back_populates="groups")
    group: Mapped[GroupRow] = relationship("GroupRow", back_populates="users")


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use AssocGroupUserRow class directly for new code.
association_groups_users = AssocGroupUserRow.__table__


class GroupRow(Base):  # type: ignore[misc]
    __tablename__ = "groups"
    __table_args__ = (
        sa.UniqueConstraint("name", "domain_name", name="uq_groups_name_domain_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(
        "name", SlugType(length=64, allow_unicode=True, allow_dot=True), nullable=False
    )
    description: Mapped[str | None] = mapped_column("description", sa.String(length=512))
    is_active: Mapped[bool | None] = mapped_column("is_active", sa.Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    modified_at: Mapped[datetime | None] = mapped_column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    )
    #: Field for synchronization with external services.
    integration_id: Mapped[str | None] = mapped_column("integration_id", sa.String(length=512))
    domain_name: Mapped[str] = mapped_column(
        "domain_name",
        sa.String(length=64),
        sa.ForeignKey("domains.name", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
    # dotfiles column, \x90 means empty list in msgpack
    dotfiles: Mapped[bytes] = mapped_column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    )
    resource_policy: Mapped[str] = mapped_column(
        "resource_policy",
        sa.String(length=256),
        sa.ForeignKey("project_resource_policies.name"),
        nullable=False,
    )
    type: Mapped[ProjectType] = mapped_column(
        "type",
        EnumValueType(ProjectType),
        nullable=False,
        default=ProjectType.GENERAL,
    )
    container_registry: Mapped[dict[str, Any] | None] = mapped_column(
        "container_registry",
        StructuredJSONColumn(container_registry_iv),
        nullable=True,
        default=None,
    )

    # Relationships (defined with deferred join conditions to avoid circular imports)
    sessions: Mapped[list[SessionRow]] = relationship("SessionRow", back_populates="group")
    domain: Mapped[DomainRow] = relationship("DomainRow", back_populates="groups")
    sgroup_for_groups_rows: Mapped[list[ScalingGroupForProjectRow]] = relationship(
        "ScalingGroupForProjectRow", back_populates="project_row"
    )
    users: Mapped[list[AssocGroupUserRow]] = relationship(
        "AssocGroupUserRow", back_populates="group"
    )
    resource_policy_row: Mapped[ProjectResourcePolicyRow] = relationship(
        "ProjectResourcePolicyRow", back_populates="projects"
    )
    kernels: Mapped[list[KernelRow]] = relationship("KernelRow", back_populates="group_row")
    networks: Mapped[list[NetworkRow]] = relationship(
        "NetworkRow",
        back_populates="project_row",
        primaryjoin=_get_networks_join_condition,
    )
    vfolder_rows: Mapped[list[VFolderRow]] = relationship(
        "VFolderRow",
        back_populates="group_row",
        primaryjoin=_get_vfolder_rows_join_condition,
    )
    association_container_registries_groups_rows: Mapped[
        list[AssociationContainerRegistriesGroupsRow]
    ] = relationship(
        "AssociationContainerRegistriesGroupsRow",
        back_populates="group_row",
        primaryjoin=_get_association_container_registries_groups_join_condition,
    )

    def to_data(self) -> GroupData:
        return GroupData(
            id=self.id,
            name=self.name,
            description=self.description,
            is_active=self.is_active,
            created_at=self.created_at,
            modified_at=self.modified_at,
            integration_id=self.integration_id,
            domain_name=self.domain_name,
            total_resource_slots=self.total_resource_slots,
            allowed_vfolder_hosts=self.allowed_vfolder_hosts,
            dotfiles=self.dotfiles,
            resource_policy=self.resource_policy,
            type=self.type,
            container_registry=self.container_registry,
        )

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        project_id: uuid.UUID,
        load_resource_policy: bool = False,
    ) -> GroupRow:
        query = sa.select(GroupRow).filter(GroupRow.id == project_id)
        if load_resource_policy:
            query = query.options(selectinload(GroupRow.resource_policy_row))
        row = await session.scalar(query)
        if not row:
            raise NoResultFound

        return row

    @classmethod
    def load_resource_policy(cls) -> _AbstractLoad:
        return joinedload(GroupRow.resource_policy_row)

    @classmethod
    async def query_by_condition(
        cls,
        conditions: Sequence[QueryCondition],
        options: Sequence[QueryOption] = tuple(),
        *,
        db: ExtendedAsyncSAEngine,
    ) -> Sequence[GroupRow]:
        """
        Args:
            condition: QueryCondition.
            options: A sequence of query options.
            db: Database engine.
        Returns:
            A list of GroupRow instances that match the condition.
        Raises:
            EmptySQLCondition: If the condition is empty.
        """
        query_stmt = sa.select(GroupRow)
        for cond in conditions:
            query_stmt = cond(query_stmt)

        for option in options:
            query_stmt = option(query_stmt)

        async def fetch(db_session: AsyncSession) -> Sequence[GroupRow]:
            return (await db_session.scalars(query_stmt)).all()

        async with db.connect() as db_conn:
            return await execute_with_txn_retry(
                fetch,
                db.begin_readonly_session,
                db_conn,
            )

    @classmethod
    async def get_by_id_with_policies(
        cls,
        project_id: uuid.UUID,
        *,
        db: ExtendedAsyncSAEngine,
    ) -> Self:
        """
        Query a project by its ID with related resource policies.
        Args:
            project_id: The ID of the project.
            db: Database engine.
        Returns:
            The GroupRow instance that matches the project ID.
        Raises:
            ObjectNotFound: If the project not found.
        """
        rows = await cls.query_by_condition(
            [by_id(project_id)],
            [load_related_field(cls.load_resource_policy())],
            db=db,
        )
        if not rows:
            raise ObjectNotFound(f"Project with id {project_id} not found")
        return rows[0]


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use GroupRow class directly for new code.
groups = GroupRow.__table__


def by_id(project_id: uuid.UUID) -> QueryCondition:
    def _by_id(
        query_stmt: sa.sql.Select[Any],
    ) -> sa.sql.Select[Any]:
        return query_stmt.where(GroupRow.id == project_id)

    return _by_id


@dataclass
class ProjectModel(RBACModel[ProjectPermission]):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool | None
    created_at: datetime | None
    modified_at: datetime | None
    domain_name: str
    type: str

    _integration_id: str | None
    _total_resource_slots: ResourceSlot
    _allowed_vfolder_hosts: VFolderHostPermissionMap
    _dotfiles: bytes
    _resource_policy: str
    _container_registry: dict[str, str] | None

    _permissions: frozenset[ProjectPermission] = field(default_factory=frozenset)

    @property
    def permissions(self) -> Container[ProjectPermission]:
        return self._permissions

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def integration_id(self) -> str | None:
        return self._integration_id

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def total_resource_slots(self) -> ResourceSlot:
        return self._total_resource_slots

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def allowed_vfolder_hosts(self) -> VFolderHostPermissionMap:
        return self._allowed_vfolder_hosts

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def dotfiles(self) -> bytes:
        return self._dotfiles

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def resource_policy(self) -> str:
        return self._resource_policy

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def container_registry(self) -> dict[str, Any] | None:
        return self._container_registry

    @classmethod
    def from_row(cls, row: GroupRow, permissions: Iterable[ProjectPermission]) -> Self:
        return cls(
            id=row.id,
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            modified_at=row.modified_at,
            domain_name=row.domain_name,
            type=row.type,
            _integration_id=row.integration_id,
            _total_resource_slots=row.total_resource_slots,
            _allowed_vfolder_hosts=row.allowed_vfolder_hosts,
            _dotfiles=row.dotfiles,
            _resource_policy=row.resource_policy,
            _container_registry=row.container_registry,
            _permissions=frozenset(permissions),
        )


def _build_group_query(
    cond: sa.sql.expression.BinaryExpression[Any], domain_name: str
) -> sa.sql.Select[Any]:
    return (
        sa.select(groups.c.id)
        .select_from(groups)
        .where(
            cond & (groups.c.domain_name == domain_name),
        )
    )


async def resolve_group_name_or_id(
    db_conn: SAConnection,
    domain_name: str,
    value: str | uuid.UUID,
) -> uuid.UUID | None:
    match value:
        case uuid.UUID():
            cond = groups.c.id == value
        case str():
            cond = groups.c.name == value
        case _:
            raise TypeError("unexpected type for group_name_or_id")
    query = _build_group_query(cond, domain_name)
    return await db_conn.scalar(query)


@overload
async def resolve_groups(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[uuid.UUID],
) -> Iterable[uuid.UUID]: ...


@overload
async def resolve_groups(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[str],
) -> Iterable[uuid.UUID]: ...


async def resolve_groups(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[uuid.UUID] | Iterable[str],
) -> Iterable[uuid.UUID]:
    listed_val = [*values]
    match listed_val:
        case [uuid.UUID(), *_]:
            query = _build_group_query((groups.c.id.in_(listed_val)), domain_name)
        case [str(), *_]:
            query = _build_group_query((groups.c.name.in_(listed_val)), domain_name)
        case []:
            return []
        case _:
            raise TypeError("unexpected type for group_name_or_id")

    rows = (await db_conn.execute(query)).fetchall()
    return [row.id for row in rows]


class GroupDotfile(TypedDict):
    data: str
    path: str
    perm: str


async def query_group_dotfiles(
    db_conn: SAConnection,
    group_id: GUID | uuid.UUID,
) -> tuple[list[GroupDotfile], int]:
    query = sa.select(groups.c.dotfiles).select_from(groups).where(groups.c.id == group_id)
    packed_dotfile = await db_conn.scalar(query)
    if packed_dotfile is None:
        return [], MAXIMUM_DOTFILE_SIZE
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


async def query_group_domain(
    db_conn: SAConnection,
    group_id: GUID | uuid.UUID,
) -> str | None:
    query = sa.select(groups.c.domain_name).select_from(groups).where(groups.c.id == group_id)
    return await db_conn.scalar(query)


def verify_dotfile_name(dotfile: str) -> bool:
    return dotfile not in RESERVED_DOTFILES


ALL_PROJECT_PERMISSIONS = frozenset([perm for perm in ProjectPermission])
OWNER_PERMISSIONS: frozenset[ProjectPermission] = ALL_PROJECT_PERMISSIONS
ADMIN_PERMISSIONS: frozenset[ProjectPermission] = ALL_PROJECT_PERMISSIONS
MONITOR_PERMISSIONS: frozenset[ProjectPermission] = frozenset([
    ProjectPermission.READ_ATTRIBUTE,
    ProjectPermission.READ_SENSITIVE_ATTRIBUTE,
    ProjectPermission.UPDATE_ATTRIBUTE,
])
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[ProjectPermission] = frozenset([
    ProjectPermission.READ_ATTRIBUTE
])
MEMBER_PERMISSIONS: frozenset[ProjectPermission] = frozenset([ProjectPermission.READ_ATTRIBUTE])

type WhereClauseType = (
    sa.sql.expression.BinaryExpression[Any]
    | sa.sql.expression.BooleanClauseList
    | sa.sql.elements.ColumnElement[bool]
)


@dataclass
class ProjectPermissionContext(AbstractPermissionContext[ProjectPermission, GroupRow, uuid.UUID]):
    registry_id_to_additional_permission_map: dict[uuid.UUID, frozenset[ProjectPermission]] = field(
        default_factory=dict
    )

    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: WhereClauseType,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.registry_id_to_additional_permission_map:
            registry_id = list(self.registry_id_to_additional_permission_map)[0]

            cond = _OR_coalesce(
                cond,
                GroupRow.association_container_registries_groups_rows.any(
                    AssociationContainerRegistriesGroupsRow.registry_id == registry_id
                ),
            )
        if self.domain_name_to_permission_map:
            cond = _OR_coalesce(
                cond, GroupRow.domain_name.in_(self.domain_name_to_permission_map.keys())
            )
        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, GroupRow.id.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, GroupRow.id.in_(self.object_id_to_overriding_permission_map.keys())
            )
        return cond

    async def build_query(self) -> sa.sql.Select[Any] | None:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(GroupRow).where(cond)

    async def calculate_final_permission(self, rbac_obj: GroupRow) -> frozenset[ProjectPermission]:
        project_row = rbac_obj
        project_id = project_row.id
        permissions: frozenset[ProjectPermission] = frozenset()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(project_id)
        ) is not None:
            permissions = overriding_perm
        else:
            permissions |= self.object_id_to_additional_permission_map.get(project_id, set())
            permissions |= self.domain_name_to_permission_map.get(project_row.domain_name, set())
        return permissions


class ProjectPermissionContextBuilder(
    AbstractPermissionContextBuilder[ProjectPermission, ProjectPermissionContext]
):
    db_session: AsyncSession

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[ProjectPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        return await self._calculate_permission_by_predefined_roles(roles)

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> ProjectPermissionContext:
        from ai.backend.manager.models.domain import DomainRow

        perm_ctx = ProjectPermissionContext()
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
    ) -> ProjectPermissionContext:
        permissions = await self.calculate_permission(ctx, scope)
        return ProjectPermissionContext(
            domain_name_to_permission_map={scope.domain_name: permissions}
        )

    @override
    async def build_ctx_in_project_scope(
        self, ctx: ClientContext, scope: ProjectScope
    ) -> ProjectPermissionContext:
        permissions = await self.calculate_permission(ctx, scope)
        return ProjectPermissionContext(
            object_id_to_additional_permission_map={scope.project_id: permissions}
        )

    @override
    async def build_ctx_in_user_scope(
        self, ctx: ClientContext, scope: UserScope
    ) -> ProjectPermissionContext:
        return ProjectPermissionContext()

    async def build_ctx_in_container_registry_scope(
        self, _ctx: ClientContext, scope: ContainerRegistryScope
    ) -> ProjectPermissionContext:
        permissions = MEMBER_PERMISSIONS
        return ProjectPermissionContext(
            registry_id_to_additional_permission_map={scope.registry_id: permissions}
        )

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[ProjectPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[ProjectPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[ProjectPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[ProjectPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[ProjectPermission]:
        return MEMBER_PERMISSIONS


async def get_projects(
    target_scope: ScopeType,
    requested_permission: ProjectPermission,
    project_id: uuid.UUID | None = None,
    project_name: str | None = None,
    *,
    ctx: ClientContext,
    db_conn: SAConnection,
) -> list[ProjectModel]:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        builder = ProjectPermissionContextBuilder(db_session)
        permission_ctx = await builder.build(ctx, target_scope, requested_permission)
        query_stmt = await permission_ctx.build_query()
        if query_stmt is None:
            return []
        if project_id is not None:
            query_stmt = query_stmt.where(GroupRow.id == project_id)
        if project_name is not None:
            query_stmt = query_stmt.where(GroupRow.name == project_name)
        result: list[ProjectModel] = []
        async for row in await db_session.stream_scalars(query_stmt):
            permissions = await permission_ctx.calculate_final_permission(row)
            result.append(ProjectModel.from_row(row, permissions))
    return result


async def get_permission_ctx(
    db_conn: SAConnection,
    ctx: ClientContext,
    requested_permission: ProjectPermission,
    target_scope: ScopeType,
    container_registry_scope: ContainerRegistryScope | None = None,
) -> ProjectPermissionContext:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        builder = ProjectPermissionContextBuilder(db_session)

        if container_registry_scope is not None:
            return await builder.build_ctx_in_container_registry_scope(
                ctx, container_registry_scope
            )
        return await builder.build(ctx, target_scope, requested_permission)
