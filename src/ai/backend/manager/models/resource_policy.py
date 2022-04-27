from __future__ import annotations

import logging
from typing import (
    Any,
    Dict,
    Sequence,
    TYPE_CHECKING,
)

import graphene
from graphene.types.datetime import DateTime as GQLDateTime
import sqlalchemy as sa
from sqlalchemy.engine.row import Row
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from .base import (
    metadata, BigInt, EnumType, ResourceSlotColumn,
    simple_db_mutate,
    simple_db_mutate_returning_item,
    set_if_set,
    batch_result,
)
from .keypair import keypairs
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger('ai.backend.manager.models'))

__all__: Sequence[str] = (
    'keypair_resource_policies',
    'KeyPairResourcePolicy',
    'DefaultForUnspecified',
    'CreateKeyPairResourcePolicy',
    'ModifyKeyPairResourcePolicy',
    'DeleteKeyPairResourcePolicy',
)


keypair_resource_policies = sa.Table(
    'keypair_resource_policies', metadata,
    sa.Column('name', sa.String(length=256), primary_key=True),
    sa.Column('created_at', sa.DateTime(timezone=True),
              server_default=sa.func.now()),
    sa.Column('default_for_unspecified',
              EnumType(DefaultForUnspecified),
              default=DefaultForUnspecified.LIMITED,
              nullable=False),
    sa.Column('total_resource_slots', ResourceSlotColumn(), nullable=False),
    sa.Column('max_session_lifetime', sa.Integer(), nullable=False, server_default=sa.text('0')),
    sa.Column('max_concurrent_sessions', sa.Integer(), nullable=False),
    sa.Column('max_containers_per_session', sa.Integer(), nullable=False),
    sa.Column('max_vfolder_count', sa.Integer(), nullable=False),
    sa.Column('max_vfolder_size', sa.BigInteger(), nullable=False),
    sa.Column('idle_timeout', sa.BigInteger(), nullable=False),
    sa.Column('allowed_vfolder_hosts', pgsql.ARRAY(sa.String), nullable=False),
    # TODO: implement with a many-to-many association table
    # sa.Column('allowed_scaling_groups', sa.Array(sa.String), nullable=False),
)


class KeyPairResourcePolicy(graphene.ObjectType):
    name = graphene.String()
    created_at = GQLDateTime()
    default_for_unspecified = graphene.String()
    total_resource_slots = graphene.JSONString()
    max_session_lifetime = graphene.Int()
    max_concurrent_sessions = graphene.Int()
    max_containers_per_session = graphene.Int()
    idle_timeout = BigInt()
    max_vfolder_count = graphene.Int()
    max_vfolder_size = BigInt()
    allowed_vfolder_hosts = graphene.List(lambda: graphene.String)

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row | None,
    ) -> KeyPairResourcePolicy | None:
        if row is None:
            return None
        return cls(
            name=row['name'],
            created_at=row['created_at'],
            default_for_unspecified=row['default_for_unspecified'].name,
            total_resource_slots=row['total_resource_slots'].to_json(),
            max_session_lifetime=row['max_session_lifetime'],
            max_concurrent_sessions=row['max_concurrent_sessions'],
            max_containers_per_session=row['max_containers_per_session'],
            idle_timeout=row['idle_timeout'],
            max_vfolder_count=row['max_vfolder_count'],
            max_vfolder_size=row['max_vfolder_size'],
            allowed_vfolder_hosts=row['allowed_vfolder_hosts'],
        )

    @classmethod
    async def load_all(cls, ctx: GraphQueryContext) -> Sequence[KeyPairResourcePolicy]:
        query = (
            sa.select([keypair_resource_policies])
            .select_from(keypair_resource_policies)
        )
        async with ctx.db.begin_readonly() as conn:
            return [
                obj async for r in (await conn.stream(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]

    @classmethod
    async def load_all_user(
        cls,
        ctx: GraphQueryContext,
        access_key: str,
    ) -> Sequence[KeyPairResourcePolicy]:
        j = sa.join(
            keypairs, keypair_resource_policies,
            keypairs.c.resource_policy == keypair_resource_policies.c.name,
        )
        query = (
            sa.select([keypair_resource_policies])
            .select_from(j)
            .where(
                keypairs.c.user_id == (
                    sa.select([keypairs.c.user_id])
                    .select_from(keypairs)
                    .where(keypairs.c.access_key == access_key)
                    .as_scalar()
                ),
            )
        )
        async with ctx.db.begin_readonly() as conn:
            return [
                obj async for r in (await conn.stream(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]

    @classmethod
    async def batch_load_by_name(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
    ) -> Sequence[KeyPairResourcePolicy | None]:
        query = (
            sa.select([keypair_resource_policies])
            .select_from(keypair_resource_policies)
            .where(keypair_resource_policies.c.name.in_(names))
            .order_by(keypair_resource_policies.c.name)
        )
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx, conn, query, cls,
                names, lambda row: row['name'],
            )

    @classmethod
    async def batch_load_by_name_user(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
    ) -> Sequence[KeyPairResourcePolicy | None]:
        access_key = ctx.access_key
        j = sa.join(
            keypairs, keypair_resource_policies,
            keypairs.c.resource_policy == keypair_resource_policies.c.name,
        )
        query = (
            sa.select([keypair_resource_policies])
            .select_from(j)
            .where(
                (keypair_resource_policies.c.name.in_(names)) &
                (keypairs.c.access_key == access_key),
            )
            .order_by(keypair_resource_policies.c.name)
        )
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx, conn, query, cls,
                names, lambda row: row['name'],
            )

    @classmethod
    async def batch_load_by_ak(
        cls,
        ctx: GraphQueryContext,
        access_keys: Sequence[str],
    ) -> Sequence[KeyPairResourcePolicy]:
        j = sa.join(
            keypairs, keypair_resource_policies,
            keypairs.c.resource_policy == keypair_resource_policies.c.name,
        )
        query = (
            sa.select([keypair_resource_policies])
            .select_from(j)
            .where((keypairs.c.access_key.in_(access_keys)))
            .order_by(keypair_resource_policies.c.name)
        )
        async with ctx.db.begin_readonly() as conn:
            return [
                obj async for r in (await conn.stream(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]


class CreateKeyPairResourcePolicyInput(graphene.InputObjectType):
    default_for_unspecified = graphene.String(required=True)
    total_resource_slots = graphene.JSONString(required=True)
    max_session_lifetime = graphene.Int(required=True, default_value=0)
    max_concurrent_sessions = graphene.Int(required=True)
    max_containers_per_session = graphene.Int(required=True)
    idle_timeout = BigInt(required=True)
    max_vfolder_count = graphene.Int(required=True)
    max_vfolder_size = BigInt(required=True)
    allowed_vfolder_hosts = graphene.List(lambda: graphene.String)


class ModifyKeyPairResourcePolicyInput(graphene.InputObjectType):
    default_for_unspecified = graphene.String(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    max_session_lifetime = graphene.Int(required=False)
    max_concurrent_sessions = graphene.Int(required=False)
    max_containers_per_session = graphene.Int(required=False)
    idle_timeout = BigInt(required=False)
    max_vfolder_count = graphene.Int(required=False)
    max_vfolder_size = BigInt(required=False)
    allowed_vfolder_hosts = graphene.List(lambda: graphene.String, required=False)


class CreateKeyPairResourcePolicy(graphene.Mutation):

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = CreateKeyPairResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    resource_policy = graphene.Field(lambda: KeyPairResourcePolicy, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: CreateKeyPairResourcePolicyInput,
    ) -> CreateKeyPairResourcePolicy:
        data = {
            'name': name,
            'default_for_unspecified':
                DefaultForUnspecified[props.default_for_unspecified],
            'total_resource_slots': ResourceSlot.from_user_input(
                props.total_resource_slots, None),
            'max_session_lifetime': props.max_session_lifetime,
            'max_concurrent_sessions': props.max_concurrent_sessions,
            'max_containers_per_session': props.max_containers_per_session,
            'idle_timeout': props.idle_timeout,
            'max_vfolder_count': props.max_vfolder_count,
            'max_vfolder_size': props.max_vfolder_size,
            'allowed_vfolder_hosts': props.allowed_vfolder_hosts,
        }
        insert_query = (
            sa.insert(keypair_resource_policies).values(data)
        )
        return await simple_db_mutate_returning_item(
            cls, info.context, insert_query, item_cls=KeyPairResourcePolicy,
        )


class ModifyKeyPairResourcePolicy(graphene.Mutation):

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyKeyPairResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyKeyPairResourcePolicyInput,
    ) -> ModifyKeyPairResourcePolicy:
        data: Dict[str, Any] = {}
        set_if_set(props, data, 'default_for_unspecified',
                   clean_func=lambda v: DefaultForUnspecified[v])
        set_if_set(props, data, 'total_resource_slots',
                   clean_func=lambda v: ResourceSlot.from_user_input(v, None))
        set_if_set(props, data, 'max_session_lifetime')
        set_if_set(props, data, 'max_concurrent_sessions')
        set_if_set(props, data, 'max_containers_per_session')
        set_if_set(props, data, 'idle_timeout')
        set_if_set(props, data, 'max_vfolder_count')
        set_if_set(props, data, 'max_vfolder_size')
        set_if_set(props, data, 'allowed_vfolder_hosts')
        update_query = (
            sa.update(keypair_resource_policies)
            .values(data)
            .where(keypair_resource_policies.c.name == name)
        )
        return await simple_db_mutate(cls, info.context, update_query)


class DeleteKeyPairResourcePolicy(graphene.Mutation):

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
    ) -> DeleteKeyPairResourcePolicy:
        delete_query = (
            sa.delete(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == name)
        )
        return await simple_db_mutate(cls, info.context, delete_query)
