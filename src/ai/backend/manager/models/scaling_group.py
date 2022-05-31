from __future__ import annotations

from datetime import timedelta
from typing import (
    Any,
    Dict,
    Mapping,
    Sequence,
    Set,
    TYPE_CHECKING,
    Union,
)
import uuid

import attr
import graphene
from graphene.types.datetime import DateTime as GQLDateTime
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.types import SessionTypes, JSONSerializableMixin

from .base import (
    metadata,
    simple_db_mutate,
    simple_db_mutate_returning_item,
    set_if_set,
    batch_result,
    batch_multiresult,
    StructuredJSONObjectColumn,
)
from .group import resolve_group_name_or_id
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

__all__: Sequence[str] = (
    # table defs
    'scaling_groups',
    'sgroups_for_domains',
    'sgroups_for_groups',
    'sgroups_for_keypairs',
    # functions
    'query_allowed_sgroups',
    'ScalingGroup',
    'CreateScalingGroup',
    'ModifyScalingGroup',
    'DeleteScalingGroup',
    'AssociateScalingGroupWithDomain',
    'AssociateScalingGroupWithUserGroup',
    'AssociateScalingGroupWithKeyPair',
    'DisassociateScalingGroupWithDomain',
    'DisassociateScalingGroupWithUserGroup',
    'DisassociateScalingGroupWithKeyPair',
)


@attr.define(slots=True)
class ScalingGroupOpts(JSONSerializableMixin):
    allowed_session_types: list[SessionTypes] = attr.Factory(
        lambda: [SessionTypes.INTERACTIVE, SessionTypes.BATCH],
    )
    pending_timeout: timedelta = timedelta(seconds=0)
    config: Mapping[str, Any] = attr.Factory(dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "allowed_session_types": [
                item.value for item in self.allowed_session_types
            ],
            "pending_timeout": self.pending_timeout.total_seconds(),
            "config": self.config,
        }

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> ScalingGroupOpts:
        return cls(**cls.as_trafaret().check(obj))

    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return t.Dict({
            t.Key('allowed_session_types', default=['interactive', 'batch']):
                t.List(tx.Enum(SessionTypes), min_length=1),
            t.Key('pending_timeout', default=0):
                tx.TimeDuration(allow_negative=False),
            # Each scheduler impl refers an additional "config" key.
            t.Key("config", default={}): t.Mapping(t.String, t.Any),
        }).allow_extra('*')


scaling_groups = sa.Table(
    'scaling_groups', metadata,
    sa.Column('name', sa.String(length=64), primary_key=True),
    sa.Column('description', sa.String(length=512)),
    sa.Column('is_active', sa.Boolean, index=True, default=True),
    sa.Column('created_at', sa.DateTime(timezone=True),
              server_default=sa.func.now()),
    sa.Column('wsproxy_addr', sa.String(length=1024), nullable=True),
    sa.Column('driver', sa.String(length=64), nullable=False),
    sa.Column('driver_opts', pgsql.JSONB(), nullable=False, default={}),
    sa.Column('scheduler', sa.String(length=64), nullable=False),
    sa.Column(
        'scheduler_opts', StructuredJSONObjectColumn(ScalingGroupOpts),
        nullable=False, default={},
    ),
)


# When scheduling, we take the union of allowed scaling groups for
# each domain, group, and keypair.


sgroups_for_domains = sa.Table(
    'sgroups_for_domains', metadata,
    sa.Column('scaling_group',
              sa.ForeignKey('scaling_groups.name',
                            onupdate='CASCADE',
                            ondelete='CASCADE'),
              index=True, nullable=False),
    sa.Column('domain',
              sa.ForeignKey('domains.name',
                            onupdate='CASCADE',
                            ondelete='CASCADE'),
              index=True, nullable=False),
    sa.UniqueConstraint('scaling_group', 'domain', name='uq_sgroup_domain'),
)


sgroups_for_groups = sa.Table(
    'sgroups_for_groups', metadata,
    sa.Column('scaling_group',
              sa.ForeignKey('scaling_groups.name',
                            onupdate='CASCADE',
                            ondelete='CASCADE'),
              index=True, nullable=False),
    sa.Column('group',
              sa.ForeignKey('groups.id',
                            onupdate='CASCADE',
                            ondelete='CASCADE'),
              index=True, nullable=False),
    sa.UniqueConstraint('scaling_group', 'group', name='uq_sgroup_ugroup'),
)


sgroups_for_keypairs = sa.Table(
    'sgroups_for_keypairs', metadata,
    sa.Column('scaling_group',
              sa.ForeignKey('scaling_groups.name',
                            onupdate='CASCADE',
                            ondelete='CASCADE'),
              index=True, nullable=False),
    sa.Column('access_key',
              sa.ForeignKey('keypairs.access_key',
                            onupdate='CASCADE',
                            ondelete='CASCADE'),
              index=True, nullable=False),
    sa.UniqueConstraint('scaling_group', 'access_key', name='uq_sgroup_akey'),
)


async def query_allowed_sgroups(
    db_conn: SAConnection,
    domain_name: str,
    group: Union[uuid.UUID, str],
    access_key: str,
) -> Sequence[Row]:
    query = (
        sa.select([sgroups_for_domains])
        .where(sgroups_for_domains.c.domain == domain_name)
    )
    result = await db_conn.execute(query)
    from_domain = {row['scaling_group'] for row in result}

    group_id = await resolve_group_name_or_id(db_conn, domain_name, group)
    from_group: Set[str]
    if group_id is None:
        from_group = set()  # empty
    else:
        query = (
            sa.select([sgroups_for_groups])
            .where(
                (sgroups_for_groups.c.group == group_id),
            )
        )
        result = await db_conn.execute(query)
        from_group = {row['scaling_group'] for row in result}

    query = (sa.select([sgroups_for_keypairs])
               .where(sgroups_for_keypairs.c.access_key == access_key))
    result = await db_conn.execute(query)
    from_keypair = {row['scaling_group'] for row in result}

    sgroups = from_domain | from_group | from_keypair
    query = (
        sa.select([scaling_groups])
        .where(
            (scaling_groups.c.name.in_(sgroups)) &
            (scaling_groups.c.is_active),
        )
        .order_by(scaling_groups.c.name)
    )
    result = await db_conn.execute(query)
    return [row for row in result]


class ScalingGroup(graphene.ObjectType):
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    wsproxy_addr = graphene.String()
    driver = graphene.String()
    driver_opts = graphene.JSONString()
    scheduler = graphene.String()
    scheduler_opts = graphene.JSONString()

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row | None,
    ) -> ScalingGroup | None:
        if row is None:
            return None
        return cls(
            name=row['name'],
            description=row['description'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            wsproxy_addr=row['wsproxy_addr'],
            driver=row['driver'],
            driver_opts=row['driver_opts'],
            scheduler=row['scheduler'],
            scheduler_opts=row['scheduler_opts'].to_json(),
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        query = sa.select([scaling_groups]).select_from(scaling_groups)
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_domain(
        cls,
        ctx: GraphQueryContext,
        domain: str,
        *,
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            scaling_groups, sgroups_for_domains,
            scaling_groups.c.name == sgroups_for_domains.c.scaling_group)
        query = (
            sa.select([scaling_groups])
            .select_from(j)
            .where(sgroups_for_domains.c.domain == domain)
        )
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_group(
        cls,
        ctx: GraphQueryContext,
        group: uuid.UUID,
        *,
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            scaling_groups, sgroups_for_groups,
            scaling_groups.c.name == sgroups_for_groups.c.scaling_group,
        )
        query = (
            sa.select([scaling_groups])
            .select_from(j)
            .where(sgroups_for_groups.c.group == group)
        )
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_keypair(
        cls,
        ctx: GraphQueryContext,
        access_key: str,
        *,
        is_active: bool = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            scaling_groups, sgroups_for_keypairs,
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
                obj async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_group(
        cls,
        ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
    ) -> Sequence[Sequence[ScalingGroup | None]]:
        j = sa.join(
            scaling_groups, sgroups_for_groups,
            scaling_groups.c.name == sgroups_for_groups.c.scaling_group,
        )
        query = (
            sa.select([scaling_groups, sgroups_for_groups.c.group])
            .select_from(j)
            .where(sgroups_for_groups.c.group.in_(group_ids))
        )
        async with ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                ctx, conn, query, cls,
                group_ids, lambda row: row['group'],
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
                ctx, conn, query, cls,
                names, lambda row: row['name'],
            )


class CreateScalingGroupInput(graphene.InputObjectType):
    description = graphene.String(required=False, default='')
    is_active = graphene.Boolean(required=False, default=True)
    wsproxy_addr = graphene.String(required=False)
    driver = graphene.String(required=True)
    driver_opts = graphene.JSONString(required=False, default={})
    scheduler = graphene.String(required=True)
    scheduler_opts = graphene.JSONString(required=False, default={})


class ModifyScalingGroupInput(graphene.InputObjectType):
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    wsproxy_addr = graphene.String(required=False)
    driver = graphene.String(required=False)
    driver_opts = graphene.JSONString(required=False)
    scheduler = graphene.String(required=False)
    scheduler_opts = graphene.JSONString(required=False)


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
            'name': name,
            'description': props.description,
            'is_active': bool(props.is_active),
            'wsproxy_addr': props.wsproxy_addr,
            'driver': props.driver,
            'driver_opts': props.driver_opts,
            'scheduler': props.scheduler,
            'scheduler_opts': ScalingGroupOpts.from_json(props.scheduler_opts),
        }
        insert_query = (
            sa.insert(scaling_groups).values(data)
        )
        return await simple_db_mutate_returning_item(
            cls, info.context, insert_query, item_cls=ScalingGroup,
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
        set_if_set(props, data, 'description')
        set_if_set(props, data, 'is_active')
        set_if_set(props, data, 'driver')
        set_if_set(props, data, 'wsproxy_addr')
        set_if_set(props, data, 'driver_opts')
        set_if_set(props, data, 'scheduler')
        set_if_set(props, data, 'scheduler_opts', clean_func=lambda v: ScalingGroupOpts.from_json(v))
        update_query = (
            sa.update(scaling_groups)
            .values(data)
            .where(scaling_groups.c.name == name)
        )
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
        delete_query = (
            sa.delete(scaling_groups)
            .where(scaling_groups.c.name == name)
        )
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
        insert_query = (
            sa.insert(sgroups_for_domains)
            .values({
                'scaling_group': scaling_group,
                'domain': domain,
            })
        )
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
        delete_query = (
            sa.delete(sgroups_for_domains)
            .where(
                (sgroups_for_domains.c.scaling_group == scaling_group) &
                (sgroups_for_domains.c.domain == domain),
            )
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
        delete_query = (
            sa.delete(sgroups_for_domains)
            .where(sgroups_for_domains.c.domain == domain)
        )
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
        insert_query = (
            sa.insert(sgroups_for_groups)
            .values({
                'scaling_group': scaling_group,
                'group': user_group,
            })
        )
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
        delete_query = (
            sa.delete(sgroups_for_groups)
            .where(
                (sgroups_for_groups.c.scaling_group == scaling_group) &
                (sgroups_for_groups.c.group == user_group),
            )
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
        delete_query = (
            sa.delete(sgroups_for_groups)
            .where(sgroups_for_groups.c.group == user_group)
        )
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
        insert_query = (
            sa.insert(sgroups_for_keypairs)
            .values({
                'scaling_group': scaling_group,
                'access_key': access_key,
            })
        )
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
        delete_query = (
            sa.delete(sgroups_for_keypairs)
            .where(
                (sgroups_for_keypairs.c.scaling_group == scaling_group) &
                (sgroups_for_keypairs.c.access_key == access_key),
            )
        )
        return await simple_db_mutate(cls, info.context, delete_query)
