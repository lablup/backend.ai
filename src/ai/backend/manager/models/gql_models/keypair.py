from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Self, Sequence

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.engine.row import Row

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.defs import REDIS_RATE_LIMIT_DB, RedisRole
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.keypair.types import KeyPairCreator, KeyPairData
from ai.backend.manager.models.gql_models.session import ComputeSession
from ai.backend.manager.models.keypair import (
    keypairs,
    prepare_new_keypair,
)

if TYPE_CHECKING:
    from ..gql import GraphQueryContext
    from .vfolder import VirtualFolder

__all__ = (
    "UserInfo",
    "KeyPair",
    "KeyPairInput",
    "KeyPairList",
    "ModifyKeyPairInput",
    "CreateKeyPair",
    "ModifyKeyPair",
    "DeleteKeyPair",
)

from ..base import (
    Item,
    PaginatedList,
    batch_multiresult,
    batch_result,
    set_if_set,
    simple_db_mutate,
    simple_db_mutate_returning_item,
)
from ..minilang.ordering import OrderSpecItem, QueryOrderParser
from ..minilang.queryfilter import FieldSpecItem, QueryFilterParser
from ..user import UserRole
from ..utils import agg_to_array


class UserInfo(graphene.ObjectType):
    email = graphene.String()
    full_name = graphene.String()

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row,
    ) -> Optional[UserInfo]:
        if row is None:
            return None
        return cls(email=row["email"], full_name=row["full_name"])

    @classmethod
    async def batch_load_by_uuid(
        cls,
        ctx: GraphQueryContext,
        user_uuids: Sequence[uuid.UUID],
    ) -> Sequence[Optional[UserInfo]]:
        async with ctx.db.begin_readonly() as conn:
            from .user import users

            query = (
                sa.select([users.c.uuid, users.c.email, users.c.full_name])
                .select_from(users)
                .where(users.c.uuid.in_(user_uuids))
            )
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                user_uuids,
                lambda row: row["uuid"],
            )


class KeyPair(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    user_id = graphene.String()
    full_name = graphene.String()
    access_key = graphene.String()
    secret_key = graphene.String()
    is_active = graphene.Boolean()
    is_admin = graphene.Boolean()
    resource_policy = graphene.String()
    created_at = GQLDateTime()
    last_used = GQLDateTime()
    rate_limit = graphene.Int()
    num_queries = graphene.Int()
    rolling_count = graphene.Int(description="Added in 24.09.0.")
    user = graphene.UUID()
    projects = graphene.List(lambda: graphene.String)

    ssh_public_key = graphene.String()

    vfolders = graphene.List("ai.backend.manager.models.VirtualFolder")
    compute_sessions = graphene.List(
        ComputeSession,
        status=graphene.String(),
    )
    concurrency_used = graphene.Int()

    user_info = graphene.Field(lambda: UserInfo)

    # Deprecated
    concurrency_limit = graphene.Int(
        deprecation_reason=(
            "Moved to KeyPairResourcePolicy object as the max_concurrent_sessions field."
        )
    )

    async def resolve_user_info(
        self,
        info: graphene.ResolveInfo,
    ) -> UserInfo:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "UserInfo.by_uuid")
        return await loader.load(self.user)

    @classmethod
    def from_data(cls, data: KeyPairData) -> Self:
        return cls(
            access_key=data.access_key,
            secret_key=data.secret_key,
            is_active=data.is_active,
            is_admin=data.is_admin,
            resource_policy=data.resource_policy_name,
            created_at=data.created_at,
            rate_limit=data.rate_limit,
            user=data.user_id,
            ssh_public_key=data.ssh_public_key,
        )

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row,
    ) -> KeyPair:
        return cls(
            id=row["access_key"],
            user_id=row["user_id"],
            full_name=row["full_name"] if "full_name" in row.keys() else None,
            access_key=row["access_key"],
            secret_key=row["secret_key"],
            is_active=row["is_active"],
            is_admin=row["is_admin"],
            resource_policy=row["resource_policy"],
            created_at=row["created_at"],
            rate_limit=row["rate_limit"],
            user=row["user"],
            ssh_public_key=row["ssh_public_key"],
            concurrency_limit=0,  # deprecated
            projects=row["groups_name"] if "groups_name" in row.keys() else [],
        )

    async def resolve_num_queries(self, info: graphene.ResolveInfo) -> int:
        ctx: GraphQueryContext = info.context
        return await ctx.valkey_stat.get_keypair_query_count(self.access_key)

    async def resolve_rolling_count(self, info: graphene.ResolveInfo) -> int:
        ctx: GraphQueryContext = info.context
        valkey_profile_target = ctx.config_provider.config.redis.to_valkey_profile_target()
        valkey_target = valkey_profile_target.profile_target(RedisRole.RATE_LIMIT)
        valkey_client = await ValkeyRateLimitClient.create(
            valkey_target=valkey_target,
            db_id=REDIS_RATE_LIMIT_DB,
            human_readable_name="ratelimit",
        )
        try:
            return await valkey_client.get_rolling_count(self.access_key)
        finally:
            await valkey_client.close()

    async def resolve_vfolders(self, info: graphene.ResolveInfo) -> Sequence[VirtualFolder]:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "VirtualFolder")
        return await loader.load(self.access_key)

    async def resolve_compute_sessions(
        self, info: graphene.ResolveInfo, raw_status: Optional[str] = None
    ):
        ctx: GraphQueryContext = info.context

        if raw_status is not None:
            status = KernelStatus[raw_status]
        loader = ctx.dataloader_manager.get_loader(ctx, "ComputeSession", status=status)
        return await loader.load(self.access_key)

    async def resolve_concurrency_used(self, info: graphene.ResolveInfo) -> int:
        ctx: GraphQueryContext = info.context

        # Get repository from context
        repository = ctx.scheduler_repository

        # Get concurrency through repository (cache-through pattern)
        # Convert graphene.String to str, then to AccessKey type
        access_key = AccessKey(str(self.access_key))
        return await repository.get_keypair_concurrency(access_key, is_sftp=False)

    async def resolve_last_used(self, info: graphene.ResolveInfo) -> datetime | None:
        ctx: GraphQueryContext = info.context
        row_ts = await ctx.valkey_stat.get_keypair_last_used_time(self.access_key)
        if row_ts is None:
            return None
        return datetime.fromtimestamp(row_ts)

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> Sequence[KeyPair]:
        from .user import users

        j = sa.join(
            keypairs,
            users,
            keypairs.c.user == users.c.uuid,
        )
        query = sa.select([keypairs]).select_from(j)
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if is_active is not None:
            query = query.where(keypairs.c.is_active == is_active)
        if limit is not None:
            query = query.limit(limit)
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "access_key": ("keypairs_access_key", None),
        "user_id": ("users_uuid", None),
        "email": ("users_email", None),
        "full_name": ("users_full_name", None),
        "is_active": ("keypairs_is_active", None),
        "is_admin": ("keypairs_is_admin", None),
        "resource_policy": ("keypairs_resource_policy", None),
        "created_at": ("keypairs_created_at", dtparse),
        "last_used": ("keypairs_last_used", dtparse),
        "rate_limit": ("keypairs_rate_limit", None),
        "num_queries": ("keypairs_num_queries", None),
        "ssh_public_key": ("keypairs_ssh_public_key", None),
        "projects": ("groups_name", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "access_key": ("keypairs_access_key", None),
        "email": ("users_email", None),
        "full_name": ("users_full_name", None),
        "is_active": ("keypairs_is_active", None),
        "is_admin": ("keypairs_is_admin", None),
        "resource_policy": ("keypairs_resource_policy", None),
        "created_at": ("keypairs_created_at", None),
        "last_used": ("keypairs_last_used", None),
        "rate_limit": ("keypairs_rate_limit", None),
        "num_queries": ("keypairs_num_queries", None),
        "projects": ("groups_name", agg_to_array),
    }

    @classmethod
    async def load_count(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
        filter: Optional[str] = None,
    ) -> int:
        from .group import association_groups_users, groups
        from .user import users

        j = (
            sa.join(keypairs, users, keypairs.c.user == users.c.uuid)
            .outerjoin(association_groups_users, users.c.uuid == association_groups_users.c.user_id)
            .outerjoin(groups, association_groups_users.c.group_id == groups.c.id)
        )
        query = sa.select([sa.func.count()]).group_by(keypairs.c.access_key).select_from(j)
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if email is not None:
            query = query.where(keypairs.c.user_id == email)
        if is_active is not None:
            query = query.where(keypairs.c.is_active == is_active)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return len(result.all())

    @classmethod
    async def load_slice(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[KeyPair]:
        from .group import association_groups_users, groups
        from .user import users

        j = (
            sa.join(keypairs, users, keypairs.c.user == users.c.uuid)
            .outerjoin(association_groups_users, users.c.uuid == association_groups_users.c.user_id)
            .outerjoin(groups, association_groups_users.c.group_id == groups.c.id)
        )
        query = (
            sa.select([
                keypairs,
                users.c.email,
                users.c.full_name,
                agg_to_array(groups.c.name).label("groups_name"),
            ])
            .select_from(j)
            .group_by(keypairs, users.c.email, users.c.full_name)
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if email is not None:
            query = query.where(keypairs.c.user_id == email)
        if is_active is not None:
            query = query.where(keypairs.c.is_active == is_active)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(keypairs.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_email(
        cls,
        graph_ctx: GraphQueryContext,
        user_ids: Sequence[uuid.UUID],
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[Sequence[Optional[KeyPair]]]:
        from .group import association_groups_users, groups
        from .user import users

        j = (
            sa.join(keypairs, users, keypairs.c.user == users.c.uuid)
            .join(association_groups_users, users.c.uuid == association_groups_users.c.user_id)
            .join(groups, association_groups_users.c.group_id == groups.c.id)
        )
        query = (
            sa.select([
                keypairs,
                users.c.email,
                users.c.full_name,
                agg_to_array(groups.c.name).label("groups_name"),
            ])
            .select_from(j)
            .where(keypairs.c.user_id.in_(user_ids))
            .group_by(keypairs, users.c.email, users.c.full_name)
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if is_active is not None:
            query = query.where(keypairs.c.is_active == is_active)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx,
                conn,
                query,
                cls,
                user_ids,
                lambda row: row["user_id"],
            )

    @classmethod
    async def batch_load_by_ak(
        cls,
        graph_ctx: GraphQueryContext,
        access_keys: Sequence[AccessKey],
        *,
        domain_name: Optional[str] = None,
    ) -> Sequence[Optional[KeyPair]]:
        from .group import association_groups_users, groups
        from .user import users

        j = (
            sa.join(keypairs, users, keypairs.c.user == users.c.uuid)
            .join(association_groups_users, users.c.uuid == association_groups_users.c.user_id)
            .join(groups, association_groups_users.c.group_id == groups.c.id)
        )
        query = (
            sa.select([
                keypairs,
                users.c.email,
                users.c.full_name,
                agg_to_array(groups.c.name).label("groups_name"),
            ])
            .select_from(j)
            .where(keypairs.c.access_key.in_(access_keys))
            .group_by(keypairs, users.c.email, users.c.full_name)
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_result(
                graph_ctx,
                conn,
                query,
                cls,
                access_keys,
                lambda row: row["access_key"],
            )


class KeyPairList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(KeyPair, required=True)


class KeyPairInput(graphene.InputObjectType):
    is_active = graphene.Boolean(required=False, default_value=True)
    is_admin = graphene.Boolean(required=False, default_value=False)
    resource_policy = graphene.String(required=True)
    concurrency_limit = graphene.Int(required=False)  # deprecated and ignored
    rate_limit = graphene.Int(required=True)

    # When creating, you MUST set all fields.
    # When modifying, set the field to "None" to skip setting the value.

    def to_creator(self) -> KeyPairCreator:
        return KeyPairCreator(
            is_active=self.is_active,
            is_admin=self.is_admin,
            resource_policy=self.resource_policy,
            rate_limit=self.rate_limit,
        )


class ModifyKeyPairInput(graphene.InputObjectType):
    is_active = graphene.Boolean(required=False)
    is_admin = graphene.Boolean(required=False)
    resource_policy = graphene.String(required=False)
    concurrency_limit = graphene.Int(required=False)  # deprecated and ignored
    rate_limit = graphene.Int(required=False)


class CreateKeyPair(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        user_id = graphene.String(required=True)
        props = KeyPairInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    keypair = graphene.Field(lambda: KeyPair, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        user_id: str,
        props: KeyPairInput,
    ) -> CreateKeyPair:
        from .user import users  # noqa

        graph_ctx: GraphQueryContext = info.context
        data = prepare_new_keypair(user_id, props.to_creator())
        insert_query = sa.insert(keypairs).values(
            **data,
            user=sa.select([users.c.uuid]).where(users.c.email == user_id).as_scalar(),
        )
        return await simple_db_mutate_returning_item(cls, graph_ctx, insert_query, item_cls=KeyPair)


class ModifyKeyPair(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        access_key = graphene.String(required=True)
        props = ModifyKeyPairInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        access_key: AccessKey,
        props: ModifyKeyPairInput,
    ) -> ModifyKeyPair:
        ctx: GraphQueryContext = info.context
        data: Dict[str, Any] = {}
        set_if_set(props, data, "is_active")
        set_if_set(props, data, "is_admin")
        set_if_set(props, data, "resource_policy")
        set_if_set(props, data, "rate_limit")
        # props.concurrency_limit is always ignored
        update_query = sa.update(keypairs).values(data).where(keypairs.c.access_key == access_key)
        return await simple_db_mutate(cls, ctx, update_query)


class DeleteKeyPair(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        access_key: AccessKey,
    ) -> DeleteKeyPair:
        from .user import UserRow

        ctx: GraphQueryContext = info.context
        async with ctx.db.begin_readonly_session() as db_session:
            user_query = (
                sa.select([sa.func.count()])
                .select_from(UserRow)
                .where(UserRow.main_access_key == access_key)
            )
            if (await db_session.scalar(user_query)) > 0:
                return DeleteKeyPair(False, "the keypair is used as main access key by any user")
        delete_query = sa.delete(keypairs).where(keypairs.c.access_key == access_key)
        result = await simple_db_mutate(cls, ctx, delete_query)
        if result.ok:
            await ctx.valkey_stat.delete_keypair_concurrency(
                access_key=str(access_key),
                is_private=False,
            )
        return result
