from __future__ import annotations

import uuid
from collections.abc import Container, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
    Self,
    Set,
    TypeAlias,
    cast,
    overload,
    override,
)

import attr
import graphene
import sqlalchemy as sa
import trafaret as t
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, relationship, selectinload
from sqlalchemy.sql.expression import true

from ai.backend.common import validators as tx
from ai.backend.common.config import agent_selector_config_iv
from ai.backend.common.types import (
    AgentSelectionStrategy,
    JSONSerializableMixin,
    ResourceSlot,
    SessionTypes,
)

from .agent import AgentStatus
from .base import (
    Base,
    IDColumn,
    StructuredJSONObjectColumn,
    batch_multiresult,
    batch_result,
    set_if_set,
    simple_db_mutate,
    simple_db_mutate_returning_item,
)
from .group import resolve_group_name_or_id, resolve_groups
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    RBACModel,
    ScopeType,
    UserScope,
    get_predefined_roles_in_scope,
)
from .rbac.context import ClientContext
from .rbac.permission_defs import ScalingGroupPermission
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

__all__: Sequence[str] = (
    # table defs
    "scaling_groups",
    "ScalingGroupOpts",
    "ScalingGroupRow",
    "sgroups_for_domains",
    "sgroups_for_groups",
    "sgroups_for_keypairs",
    # functions
    "query_allowed_sgroups",
    "ScalingGroup",
    "CreateScalingGroup",
    "ModifyScalingGroup",
    "DeleteScalingGroup",
    "AssociateScalingGroupWithDomain",
    "AssociateScalingGroupWithUserGroup",
    "AssociateScalingGroupWithKeyPair",
    "DisassociateScalingGroupWithDomain",
    "DisassociateScalingGroupWithUserGroup",
    "DisassociateScalingGroupWithKeyPair",
)


@attr.define(slots=True)
class ScalingGroupOpts(JSONSerializableMixin):
    allowed_session_types: list[SessionTypes] = attr.Factory(
        lambda: [
            SessionTypes.INTERACTIVE,
            SessionTypes.BATCH,
            SessionTypes.INFERENCE,
        ],
    )
    pending_timeout: timedelta = timedelta(seconds=0)
    config: Mapping[str, Any] = attr.field(factory=dict)

    # Scheduler has a dedicated database column to store its name,
    # but agent selector configuration is stored as a part of the scheduler_opts column.
    agent_selection_strategy: AgentSelectionStrategy = AgentSelectionStrategy.DISPERSED
    agent_selector_config: Mapping[str, Any] = attr.field(factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "allowed_session_types": [item.value for item in self.allowed_session_types],
            "pending_timeout": self.pending_timeout.total_seconds(),
            "config": self.config,
            "agent_selection_strategy": self.agent_selection_strategy,
            "agent_selector_config": self.agent_selector_config,
        }

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> ScalingGroupOpts:
        return cls(**cls.as_trafaret().check(obj))

    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return t.Dict({
            t.Key("allowed_session_types", default=["interactive", "batch"]): t.List(
                tx.Enum(SessionTypes), min_length=1
            ),
            t.Key("pending_timeout", default=0): tx.TimeDuration(allow_negative=False),
            # Each scheduler impl refers an additional "config" key.
            t.Key("config", default={}): t.Mapping(t.String, t.Any),
            t.Key("agent_selection_strategy", default=AgentSelectionStrategy.DISPERSED): tx.Enum(
                AgentSelectionStrategy
            ),
            t.Key("agent_selector_config", default={}): agent_selector_config_iv,
        }).allow_extra("*")


# When scheduling, we take the union of allowed scaling groups for
# each domain, group, and keypair.


class ScalingGroupForDomainRow(Base):
    __tablename__ = "sgroups_for_domains"
    id = IDColumn()
    scaling_group = sa.Column(
        "scaling_group",
        sa.ForeignKey("scaling_groups.name", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    domain = sa.Column(
        "domain",
        sa.ForeignKey("domains.name", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("scaling_group", "domain", name="uq_sgroup_domain"),
    )
    sgroup_row = relationship(
        "ScalingGroupRow",
        back_populates="sgroup_for_domains_rows",
    )
    domain_row = relationship(
        "DomainRow",
        back_populates="sgroup_for_domains_rows",
    )


# For compatibility
sgroups_for_domains = ScalingGroupForDomainRow.__table__


class ScalingGroupForProjectRow(Base):
    __tablename__ = "sgroups_for_groups"
    id = IDColumn()
    scaling_group = sa.Column(
        "scaling_group",
        sa.ForeignKey("scaling_groups.name", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    group = sa.Column(
        "group",
        sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    __table_args__ = (
        # constraint
        sa.UniqueConstraint("scaling_group", "group", name="uq_sgroup_ugroup"),
    )
    sgroup_row = relationship(
        "ScalingGroupRow",
        back_populates="sgroup_for_groups_rows",
    )
    project_row = relationship(
        "GroupRow",
        back_populates="sgroup_for_groups_rows",
    )


# For compatibility
sgroups_for_groups = ScalingGroupForProjectRow.__table__


class ScalingGroupForKeypairsRow(Base):
    __tablename__ = "sgroups_for_keypairs"
    id = IDColumn()
    scaling_group = sa.Column(
        "scaling_group",
        sa.ForeignKey("scaling_groups.name", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    access_key = sa.Column(
        "access_key",
        sa.ForeignKey("keypairs.access_key", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("scaling_group", "access_key", name="uq_sgroup_akey"),
    )
    sgroup_row = relationship(
        "ScalingGroupRow",
        back_populates="sgroup_for_keypairs_rows",
    )
    keypair_row = relationship(
        "KeyPairRow",
        back_populates="sgroup_for_keypairs_rows",
    )


# For compatibility
sgroups_for_keypairs = ScalingGroupForKeypairsRow.__table__


class ScalingGroupRow(Base):
    __tablename__ = "scaling_groups"
    name = sa.Column("name", sa.String(length=64), primary_key=True)
    description = sa.Column("description", sa.String(length=512))
    is_active = sa.Column("is_active", sa.Boolean, index=True, default=True)
    is_public = sa.Column(
        "is_public", sa.Boolean, index=True, default=True, server_default=true(), nullable=False
    )
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    wsproxy_addr = sa.Column("wsproxy_addr", sa.String(length=1024), nullable=True)
    wsproxy_api_token = sa.Column("wsproxy_api_token", sa.String(length=128), nullable=True)
    driver = sa.Column("driver", sa.String(length=64), nullable=False)
    driver_opts = sa.Column("driver_opts", pgsql.JSONB(), nullable=False, default={})
    scheduler = sa.Column("scheduler", sa.String(length=64), nullable=False)
    use_host_network = sa.Column("use_host_network", sa.Boolean, nullable=False, default=False)
    scheduler_opts = sa.Column(
        "scheduler_opts",
        StructuredJSONObjectColumn(ScalingGroupOpts),
        nullable=False,
        default={},
    )

    sessions = relationship("SessionRow", back_populates="scaling_group")
    agents = relationship("AgentRow", back_populates="scaling_group_row")

    sgroup_for_domains_rows = relationship(
        "ScalingGroupForDomainRow",
        back_populates="sgroup_row",
    )
    sgroup_for_groups_rows = relationship(
        "ScalingGroupForProjectRow",
        back_populates="sgroup_row",
    )
    sgroup_for_keypairs_rows = relationship(
        "ScalingGroupForKeypairsRow",
        back_populates="sgroup_row",
    )


# For compatibility
scaling_groups = ScalingGroupRow.__table__


@dataclass
class ScalingGroupModel(RBACModel[ScalingGroupPermission]):
    name: str
    description: Optional[str]
    is_active: bool
    is_public: bool
    created_at: datetime

    wsproxy_addr: Optional[str]
    wsproxy_api_token: Optional[str]
    driver: str
    driver_opts: dict
    scheduler: str
    use_host_network: bool
    scheduler_opts: ScalingGroupOpts

    orm_obj: ScalingGroupRow
    _permissions: frozenset[ScalingGroupPermission] = field(default_factory=frozenset)

    @property
    def permissions(self) -> Container[ScalingGroupPermission]:
        return self._permissions

    @classmethod
    def from_row(cls, row: ScalingGroupRow, permissions: Iterable[ScalingGroupPermission]) -> Self:
        return cls(
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            is_public=row.is_public,
            created_at=row.created_at,
            wsproxy_addr=row.wsproxy_addr,
            wsproxy_api_token=row.wsproxy_api_token,
            driver=row.driver,
            driver_opts=row.driver_opts,
            scheduler=row.scheduler,
            use_host_network=row.use_host_network,
            scheduler_opts=row.scheduler_opts,
            _permissions=frozenset(permissions),
            orm_obj=row,
        )


@overload
async def query_allowed_sgroups(
    db_conn: SAConnection,
    domain_name: str,
    group: uuid.UUID,
    access_key: str,
) -> Sequence[Row]: ...


@overload
async def query_allowed_sgroups(
    db_conn: SAConnection,
    domain_name: str,
    group: Iterable[uuid.UUID],
    access_key: str,
) -> Sequence[Row]: ...


@overload
async def query_allowed_sgroups(
    db_conn: SAConnection,
    domain_name: str,
    group: str,
    access_key: str,
) -> Sequence[Row]: ...


@overload
async def query_allowed_sgroups(
    db_conn: SAConnection,
    domain_name: str,
    group: Iterable[str],
    access_key: str,
) -> Sequence[Row]: ...


async def query_allowed_sgroups(
    db_conn: SAConnection,
    domain_name: str,
    group: uuid.UUID | Iterable[uuid.UUID] | str | Iterable[str],
    access_key: str,
) -> Sequence[Row]:
    query = sa.select([sgroups_for_domains]).where(sgroups_for_domains.c.domain == domain_name)
    result = await db_conn.execute(query)
    from_domain = {row["scaling_group"] for row in result}

    group_ids: Iterable[uuid.UUID] = []
    match group:
        case uuid.UUID() | str():
            if group_id := await resolve_group_name_or_id(db_conn, domain_name, group):
                group_ids = [group_id]
            else:
                group_ids = []
        case list() | tuple() | set():
            group_ids = await resolve_groups(db_conn, domain_name, cast(Iterable, group))
    from_group: Set[str]
    if not group_ids:
        from_group = set()  # empty
    else:
        group_cond = sgroups_for_groups.c.group.in_(group_ids)
        query = sa.select([sgroups_for_groups]).where(group_cond)
        result = await db_conn.execute(query)
        from_group = {row["scaling_group"] for row in result}

    query = sa.select([sgroups_for_keypairs]).where(sgroups_for_keypairs.c.access_key == access_key)
    result = await db_conn.execute(query)
    from_keypair = {row["scaling_group"] for row in result}

    sgroups = from_domain | from_group | from_keypair
    query = (
        sa.select([scaling_groups])
        .where(
            (scaling_groups.c.name.in_(sgroups)) & (scaling_groups.c.is_active),
        )
        .order_by(scaling_groups.c.name)
    )
    result = await db_conn.execute(query)
    return [row for row in result]


class ScalingGroup(graphene.ObjectType):
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    is_public = graphene.Boolean()
    created_at = GQLDateTime()
    wsproxy_addr = graphene.String()
    wsproxy_api_token = graphene.String()
    driver = graphene.String()
    driver_opts = graphene.JSONString()
    scheduler = graphene.String()
    scheduler_opts = graphene.JSONString()
    use_host_network = graphene.Boolean()

    # Dynamic fields.
    agent_count_by_status = graphene.Field(
        graphene.Int,
        description="Added in 24.03.7.",
        status=graphene.String(
            default_value=AgentStatus.ALIVE.name,
            description=f"Possible states of an agent. Should be one of {[s.name for s in AgentStatus]}. Default is 'ALIVE'.",
        ),
    )

    agent_total_resource_slots_by_status = graphene.Field(
        graphene.JSONString,
        description="Added in 24.03.7.",
        status=graphene.String(
            default_value=AgentStatus.ALIVE.name,
            description=f"Possible states of an agent. Should be one of {[s.name for s in AgentStatus]}. Default is 'ALIVE'.",
        ),
    )

    async def resolve_agent_count_by_status(
        self, info: graphene.ResolveInfo, status: str = AgentStatus.ALIVE.name
    ) -> int:
        from .gql_models.agent import Agent

        return await Agent.load_count(
            info.context,
            raw_status=status,
            scaling_group=self.name,
        )

    async def resolve_agent_total_resource_slots_by_status(
        self, info: graphene.ResolveInfo, status: str = AgentStatus.ALIVE.name
    ) -> Mapping[str, Any]:
        from .agent import AgentRow, AgentStatus

        graph_ctx = info.context
        async with graph_ctx.db.begin_readonly_session() as db_session:
            query_stmt = (
                sa.select(AgentRow)
                .where(
                    (AgentRow.scaling_group == self.name) & (AgentRow.status == AgentStatus[status])
                )
                .options(load_only(AgentRow.occupied_slots, AgentRow.available_slots))
            )
            result = (await db_session.scalars(query_stmt)).all()
            agent_rows = cast(list[AgentRow], result)

            total_occupied_slots = ResourceSlot()
            total_available_slots = ResourceSlot()

            for agent_row in agent_rows:
                total_occupied_slots += agent_row.occupied_slots
                total_available_slots += agent_row.available_slots

            return {
                "occupied_slots": total_occupied_slots.to_json(),
                "available_slots": total_available_slots.to_json(),
            }

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row | None,
    ) -> ScalingGroup | None:
        if row is None:
            return None
        return cls(
            name=row["name"],
            description=row["description"],
            is_active=row["is_active"],
            is_public=row["is_public"],
            created_at=row["created_at"],
            wsproxy_addr=row["wsproxy_addr"],
            wsproxy_api_token=row["wsproxy_api_token"],
            driver=row["driver"],
            driver_opts=row["driver_opts"],
            scheduler=row["scheduler"],
            scheduler_opts=row["scheduler_opts"].to_json(),
            use_host_network=row["use_host_network"],
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        is_active: Optional[bool] = None,
    ) -> Sequence[ScalingGroup]:
        query = sa.select([scaling_groups]).select_from(scaling_groups)
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_domain(
        cls,
        ctx: GraphQueryContext,
        domain: str,
        *,
        is_active: Optional[bool] = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            scaling_groups,
            sgroups_for_domains,
            scaling_groups.c.name == sgroups_for_domains.c.scaling_group,
        )
        query = (
            sa.select([scaling_groups]).select_from(j).where(sgroups_for_domains.c.domain == domain)
        )
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_group(
        cls,
        ctx: GraphQueryContext,
        group: uuid.UUID,
        *,
        is_active: Optional[bool] = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            scaling_groups,
            sgroups_for_groups,
            scaling_groups.c.name == sgroups_for_groups.c.scaling_group,
        )
        query = (
            sa.select([scaling_groups]).select_from(j).where(sgroups_for_groups.c.group == group)
        )
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_keypair(
        cls,
        ctx: GraphQueryContext,
        access_key: str,
        *,
        is_active: Optional[bool] = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            scaling_groups,
            sgroups_for_keypairs,
            scaling_groups.c.name == sgroups_for_keypairs.c.scaling_group,
        )
        query = (
            sa.select([scaling_groups])
            .select_from(j)
            .where(sgroups_for_keypairs.c.access_key == access_key)
        )
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_group(
        cls,
        ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
    ) -> Sequence[Sequence[ScalingGroup | None]]:
        j = sa.join(
            scaling_groups,
            sgroups_for_groups,
            scaling_groups.c.name == sgroups_for_groups.c.scaling_group,
        )
        query = (
            sa.select([scaling_groups, sgroups_for_groups.c.group])
            .select_from(j)
            .where(sgroups_for_groups.c.group.in_(group_ids))
        )
        async with ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                ctx,
                conn,
                query,
                cls,
                group_ids,
                lambda row: row["group"],
            )

    @classmethod
    async def batch_load_by_name(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
    ) -> Sequence[ScalingGroup | None]:
        query = (
            sa.select([scaling_groups])
            .select_from(scaling_groups)
            .where(scaling_groups.c.name.in_(names))
        )
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                names,
                lambda row: row["name"],
            )


class CreateScalingGroupInput(graphene.InputObjectType):
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    is_public = graphene.Boolean(required=False, default_value=True)
    wsproxy_addr = graphene.String(required=False, default_value=None)
    wsproxy_api_token = graphene.String(required=False, default_value=None)
    driver = graphene.String(required=True)
    driver_opts = graphene.JSONString(required=False, default_value={})
    scheduler = graphene.String(required=True)
    scheduler_opts = graphene.JSONString(required=False, default_value={})
    use_host_network = graphene.Boolean(required=False, default_value=False)


class ModifyScalingGroupInput(graphene.InputObjectType):
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    is_public = graphene.Boolean(required=False)
    wsproxy_addr = graphene.String(required=False)
    wsproxy_api_token = graphene.String(required=False)
    driver = graphene.String(required=False)
    driver_opts = graphene.JSONString(required=False)
    scheduler = graphene.String(required=False)
    scheduler_opts = graphene.JSONString(required=False)
    use_host_network = graphene.Boolean(required=False)


class CreateScalingGroup(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = CreateScalingGroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    scaling_group = graphene.Field(lambda: ScalingGroup, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: CreateScalingGroupInput,
    ) -> CreateScalingGroup:
        data = {
            "name": name,
            "description": props.description,
            "is_active": bool(props.is_active),
            "is_public": bool(props.is_public),
            "wsproxy_addr": props.wsproxy_addr,
            "wsproxy_api_token": props.wsproxy_api_token,
            "driver": props.driver,
            "driver_opts": props.driver_opts,
            "scheduler": props.scheduler,
            "scheduler_opts": ScalingGroupOpts.from_json(props.scheduler_opts),
            "use_host_network": bool(props.use_host_network),
        }
        insert_query = sa.insert(scaling_groups).values(data)
        return await simple_db_mutate_returning_item(
            cls,
            info.context,
            insert_query,
            item_cls=ScalingGroup,
        )


class ModifyScalingGroup(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyScalingGroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyScalingGroupInput,
    ) -> ModifyScalingGroup:
        data: Dict[str, Any] = {}
        set_if_set(props, data, "description")
        set_if_set(props, data, "is_active")
        set_if_set(props, data, "is_public")
        set_if_set(props, data, "wsproxy_addr")
        set_if_set(props, data, "wsproxy_api_token")
        set_if_set(props, data, "driver")
        set_if_set(props, data, "driver_opts")
        set_if_set(props, data, "scheduler")
        set_if_set(
            props, data, "scheduler_opts", clean_func=lambda v: ScalingGroupOpts.from_json(v)
        )
        set_if_set(props, data, "use_host_network")
        update_query = sa.update(scaling_groups).values(data).where(scaling_groups.c.name == name)
        return await simple_db_mutate(cls, info.context, update_query)


class DeleteScalingGroup(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
    ) -> DeleteScalingGroup:
        delete_query = sa.delete(scaling_groups).where(scaling_groups.c.name == name)
        return await simple_db_mutate(cls, info.context, delete_query)


class AssociateScalingGroupWithDomain(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_group: str,
        domain: str,
    ) -> AssociateScalingGroupWithDomain:
        insert_query = sa.insert(sgroups_for_domains).values({
            "scaling_group": scaling_group,
            "domain": domain,
        })
        return await simple_db_mutate(cls, info.context, insert_query)


class AssociateScalingGroupsWithDomain(graphene.Mutation):
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        domain: str,
    ) -> AssociateScalingGroupsWithDomain:
        insert_query = sa.insert(sgroups_for_domains).values([
            {"scaling_group": scaling_group, "domain": domain} for scaling_group in scaling_groups
        ])
        return await simple_db_mutate(cls, info.context, insert_query)


class DisassociateScalingGroupWithDomain(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_group: str,
        domain: str,
    ) -> DisassociateScalingGroupWithDomain:
        delete_query = sa.delete(sgroups_for_domains).where(
            (sgroups_for_domains.c.scaling_group == scaling_group)
            & (sgroups_for_domains.c.domain == domain),
        )
        return await simple_db_mutate(cls, info.context, delete_query)


class DisassociateScalingGroupsWithDomain(graphene.Mutation):
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        domain: str,
    ) -> DisassociateScalingGroupsWithDomain:
        delete_query = sa.delete(sgroups_for_domains).where(
            (sgroups_for_domains.c.scaling_group.in_(scaling_groups))
            & (sgroups_for_domains.c.domain == domain),
        )
        return await simple_db_mutate(cls, info.context, delete_query)


class DisassociateAllScalingGroupsWithDomain(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        domain: str,
    ) -> DisassociateAllScalingGroupsWithDomain:
        delete_query = sa.delete(sgroups_for_domains).where(sgroups_for_domains.c.domain == domain)
        return await simple_db_mutate(cls, info.context, delete_query)


class AssociateScalingGroupWithUserGroup(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_group: str,
        user_group: uuid.UUID,
    ) -> AssociateScalingGroupWithUserGroup:
        insert_query = sa.insert(sgroups_for_groups).values({
            "scaling_group": scaling_group,
            "group": user_group,
        })
        return await simple_db_mutate(cls, info.context, insert_query)


class AssociateScalingGroupsWithUserGroup(graphene.Mutation):
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        user_group: uuid.UUID,
    ) -> AssociateScalingGroupsWithUserGroup:
        insert_query = sa.insert(sgroups_for_groups).values([
            {"scaling_group": scaling_group, "group": user_group}
            for scaling_group in scaling_groups
        ])
        return await simple_db_mutate(cls, info.context, insert_query)


class DisassociateScalingGroupWithUserGroup(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_group: str,
        user_group: uuid.UUID,
    ) -> DisassociateScalingGroupWithUserGroup:
        delete_query = sa.delete(sgroups_for_groups).where(
            (sgroups_for_groups.c.scaling_group == scaling_group)
            & (sgroups_for_groups.c.group == user_group),
        )
        return await simple_db_mutate(cls, info.context, delete_query)


class DisassociateScalingGroupsWithUserGroup(graphene.Mutation):
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        user_group: uuid.UUID,
    ) -> DisassociateScalingGroupsWithUserGroup:
        delete_query = sa.delete(sgroups_for_groups).where(
            (sgroups_for_groups.c.scaling_group.in_(scaling_groups))
            & (sgroups_for_groups.c.group == user_group),
        )
        return await simple_db_mutate(cls, info.context, delete_query)


class DisassociateAllScalingGroupsWithGroup(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        user_group: uuid.UUID,
    ) -> DisassociateAllScalingGroupsWithGroup:
        delete_query = sa.delete(sgroups_for_groups).where(sgroups_for_groups.c.group == user_group)
        return await simple_db_mutate(cls, info.context, delete_query)


class AssociateScalingGroupWithKeyPair(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_group: str,
        access_key: str,
    ) -> AssociateScalingGroupWithKeyPair:
        insert_query = sa.insert(sgroups_for_keypairs).values({
            "scaling_group": scaling_group,
            "access_key": access_key,
        })
        return await simple_db_mutate(cls, info.context, insert_query)


class AssociateScalingGroupsWithKeyPair(graphene.Mutation):
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        access_key: str,
    ) -> AssociateScalingGroupsWithKeyPair:
        insert_query = sa.insert(sgroups_for_keypairs).values([
            {"scaling_group": scaling_group, "access_key": access_key}
            for scaling_group in scaling_groups
        ])
        return await simple_db_mutate(cls, info.context, insert_query)


class DisassociateScalingGroupWithKeyPair(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_group: str,
        access_key: str,
    ) -> DisassociateScalingGroupWithKeyPair:
        delete_query = sa.delete(sgroups_for_keypairs).where(
            (sgroups_for_keypairs.c.scaling_group == scaling_group)
            & (sgroups_for_keypairs.c.access_key == access_key),
        )
        return await simple_db_mutate(cls, info.context, delete_query)


class DisassociateScalingGroupsWithKeyPair(graphene.Mutation):
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        access_key: str,
    ) -> DisassociateScalingGroupsWithKeyPair:
        delete_query = sa.delete(sgroups_for_keypairs).where(
            (sgroups_for_keypairs.c.scaling_group.in_(scaling_groups))
            & (sgroups_for_keypairs.c.access_key == access_key),
        )
        return await simple_db_mutate(cls, info.context, delete_query)


ALL_SCALING_GROUP_PERMISSIONS: frozenset[ScalingGroupPermission] = frozenset([
    perm for perm in ScalingGroupPermission
])

OWNER_PERMISSIONS: frozenset[ScalingGroupPermission] = ALL_SCALING_GROUP_PERMISSIONS
ADMIN_PERMISSIONS: frozenset[ScalingGroupPermission] = frozenset({
    # Admin permissions
    ScalingGroupPermission.READ_ATTRIBUTE,
    # sub-scope permissions
    ScalingGroupPermission.AGENT_PERMISSIONS,
    ScalingGroupPermission.COMPUTE_SESSION_PERMISSIONS,
    ScalingGroupPermission.INFERENCE_SERVICE_PERMISSIONS,
    ScalingGroupPermission.STORAGE_HOST_PERMISSIONS,
})
MONITOR_PERMISSIONS: frozenset[ScalingGroupPermission] = frozenset({
    # Admin permissions
    ScalingGroupPermission.READ_ATTRIBUTE,
    # sub-scope permissions
    ScalingGroupPermission.AGENT_PERMISSIONS,
    ScalingGroupPermission.COMPUTE_SESSION_PERMISSIONS,
    ScalingGroupPermission.INFERENCE_SERVICE_PERMISSIONS,
    ScalingGroupPermission.STORAGE_HOST_PERMISSIONS,
})
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[ScalingGroupPermission] = frozenset({
    ScalingGroupPermission.AGENT_PERMISSIONS,
    ScalingGroupPermission.COMPUTE_SESSION_PERMISSIONS,
    ScalingGroupPermission.INFERENCE_SERVICE_PERMISSIONS,
    ScalingGroupPermission.STORAGE_HOST_PERMISSIONS,
})
MEMBER_PERMISSIONS: frozenset[ScalingGroupPermission] = frozenset({
    ScalingGroupPermission.AGENT_PERMISSIONS,
    ScalingGroupPermission.COMPUTE_SESSION_PERMISSIONS,
    ScalingGroupPermission.INFERENCE_SERVICE_PERMISSIONS,
    ScalingGroupPermission.STORAGE_HOST_PERMISSIONS,
})

ScalingGroupToPermissionMap = Mapping[str, frozenset[ScalingGroupPermission]]

WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)


@dataclass
class ScalingGroupPermissionContext(AbstractPermissionContext[ScalingGroupPermission, str, str]):
    @property
    def sgroup_to_permissions_map(self) -> ScalingGroupToPermissionMap:
        return self.object_id_to_additional_permission_map

    @property
    def query_condition(self) -> Optional[WhereClauseType]:
        cond: Optional[WhereClauseType] = None

        def _OR_coalesce(
            base_cond: Optional[WhereClauseType],
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, ScalingGroupRow.name.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, ScalingGroupRow.name.in_(self.object_id_to_overriding_permission_map.keys())
            )
        return cond

    async def build_query(self) -> Optional[sa.sql.Select]:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(ScalingGroupRow).where(cond)

    async def calculate_final_permission(self, rbac_obj: str) -> frozenset[ScalingGroupPermission]:
        host_name = rbac_obj
        return self.object_id_to_additional_permission_map.get(host_name, frozenset())


class ScalingGroupPermissionContextBuilder(
    AbstractPermissionContextBuilder[ScalingGroupPermission, ScalingGroupPermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[ScalingGroupPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        permissions = await self._calculate_permission_by_predefined_roles(roles)
        permissions |= await self.apply_customized_role(ctx, target_scope)
        return permissions

    async def apply_customized_role(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[ScalingGroupPermission]:
        if ctx.user_role == UserRole.SUPERADMIN:
            return ALL_SCALING_GROUP_PERMISSIONS
        return frozenset()

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> ScalingGroupPermissionContext:
        from .domain import DomainRow

        perm_ctx = ScalingGroupPermissionContext()
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
    ) -> ScalingGroupPermissionContext:
        from .domain import DomainRow

        permissions = await self.calculate_permission(ctx, scope)
        if not permissions:
            # User is not part of the domain.
            return ScalingGroupPermissionContext()

        stmt = (
            sa.select(DomainRow)
            .where(DomainRow.name == scope.domain_name)
            .options(selectinload(DomainRow.sgroup_for_domains_rows))
        )
        domain_row = cast(DomainRow | None, await self.db_session.scalar(stmt))
        if domain_row is None:
            return ScalingGroupPermissionContext()
        scaling_groups = cast(list[ScalingGroupForDomainRow], domain_row.sgroup_for_domains_rows)
        result = ScalingGroupPermissionContext(
            object_id_to_additional_permission_map={
                row.scaling_group: permissions for row in scaling_groups
            }
        )
        return result

    @override
    async def build_ctx_in_project_scope(
        self,
        ctx: ClientContext,
        scope: ProjectScope,
    ) -> ScalingGroupPermissionContext:
        from .group import GroupRow

        project_permissions = await self.calculate_permission(ctx, scope)
        if not project_permissions:
            # User is not part of the domain.
            return ScalingGroupPermissionContext()

        stmt = (
            sa.select(GroupRow)
            .where(GroupRow.id == scope.project_id)
            .options(selectinload(GroupRow.sgroup_for_groups_rows))
        )
        project_row = cast(GroupRow | None, await self.db_session.scalar(stmt))
        if project_row is None:
            return ScalingGroupPermissionContext()
        scaling_groups = cast(list[ScalingGroupForProjectRow], project_row.sgroup_for_groups_rows)
        result = ScalingGroupPermissionContext(
            object_id_to_additional_permission_map={
                row.scaling_group: project_permissions for row in scaling_groups
            }
        )
        return result

    @override
    async def build_ctx_in_user_scope(
        self,
        ctx: ClientContext,
        scope: UserScope,
    ) -> ScalingGroupPermissionContext:
        from .keypair import KeyPairRow
        from .user import UserRow

        user_permissions = await self.calculate_permission(ctx, scope)
        if not user_permissions:
            # User is not part of the domain.
            return ScalingGroupPermissionContext()

        stmt = (
            sa.select(UserRow)
            .where(UserRow.uuid == scope.user_id)
            .options(
                selectinload(UserRow.keypairs).options(
                    joinedload(KeyPairRow.sgroup_for_keypairs_rows)
                )
            )
        )
        user_row = cast(UserRow | None, await self.db_session.scalar(stmt))
        if user_row is None:
            return ScalingGroupPermissionContext()

        object_id_to_additional_permission_map: dict[str, frozenset[ScalingGroupPermission]] = {}
        for keypair in user_row.keypairs:
            scaling_groups = cast(
                list[ScalingGroupForKeypairsRow], keypair.sgroup_for_keypairs_rows
            )
            for sg in scaling_groups:
                if sg.scaling_group not in object_id_to_additional_permission_map:
                    object_id_to_additional_permission_map[sg.scaling_group] = user_permissions
        result = ScalingGroupPermissionContext(
            object_id_to_additional_permission_map=object_id_to_additional_permission_map
        )
        return result

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return MEMBER_PERMISSIONS


async def get_scaling_groups(
    target_scope: ScopeType,
    requested_permission: ScalingGroupPermission,
    sgroup_names: Optional[Iterable[str]] = None,
    *,
    ctx: ClientContext,
    db_session: SASession,
) -> list[ScalingGroupModel]:
    ret: list[ScalingGroupModel] = []
    builder = ScalingGroupPermissionContextBuilder(db_session)
    permission_ctx = await builder.build(ctx, target_scope, requested_permission)
    cond = permission_ctx.query_condition
    if cond is None:
        return ret
    _stmt = sa.select(ScalingGroupRow).where(cond)
    if sgroup_names is not None:
        _stmt = _stmt.where(ScalingGroupRow.name.in_(sgroup_names))
    async for row in await db_session.stream_scalars(_stmt):
        permissions = await permission_ctx.calculate_final_permission(row)
        ret.append(ScalingGroupModel.from_row(row, permissions))
    return ret
