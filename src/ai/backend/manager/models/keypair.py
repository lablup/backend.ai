from __future__ import annotations

import base64
import secrets
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence, Tuple, TypedDict

import graphene
import sqlalchemy as sa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import false

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.types import AccessKey, SecretKey

if TYPE_CHECKING:
    from .gql import GraphQueryContext
    from .vfolder import VirtualFolder

from ..defs import RESERVED_DOTFILES
from .base import (
    Base,
    ForeignKeyIDColumn,
    Item,
    PaginatedList,
    batch_multiresult,
    batch_result,
    mapper_registry,
    set_if_set,
    simple_db_mutate,
    simple_db_mutate_returning_item,
)
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser
from .user import ModifyUserInput, UserRole
from .utils import agg_to_array

__all__: Sequence[str] = (
    "keypairs",
    "KeyPairRow",
    "KeyPair",
    "KeyPairList",
    "UserInfo",
    "KeyPairInput",
    "CreateKeyPair",
    "ModifyKeyPair",
    "DeleteKeyPair",
    "Dotfile",
    "MAXIMUM_DOTFILE_SIZE",
    "query_owned_dotfiles",
    "query_bootstrap_script",
    "verify_dotfile_name",
)


MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB

keypairs = sa.Table(
    "keypairs",
    mapper_registry.metadata,
    sa.Column("user_id", sa.String(length=256), index=True),
    sa.Column("access_key", sa.String(length=20), primary_key=True),
    sa.Column("secret_key", sa.String(length=40)),
    sa.Column("is_active", sa.Boolean, index=True),
    sa.Column("is_admin", sa.Boolean, index=True, default=False, server_default=false()),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    ),
    sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
    sa.Column("rate_limit", sa.Integer),
    sa.Column("num_queries", sa.Integer, server_default="0"),
    # SSH Keypairs.
    sa.Column("ssh_public_key", sa.Text, nullable=True),
    sa.Column("ssh_private_key", sa.Text, nullable=True),
    ForeignKeyIDColumn("user", "users.uuid", nullable=False),
    sa.Column(
        "resource_policy",
        sa.String(length=256),
        sa.ForeignKey("keypair_resource_policies.name"),
        nullable=False,
    ),
    # dotfiles column, \x90 means empty list in msgpack
    sa.Column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    ),
    sa.Column(
        "bootstrap_script", sa.String(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=""
    ),
)


class KeyPairRow(Base):
    __table__ = keypairs
    sessions = relationship("SessionRow", back_populates="access_key_row")
    resource_policy_row = relationship("KeyPairResourcePolicyRow", back_populates="keypairs")
    scaling_groups = relationship(
        "ScalingGroupRow",
        secondary="sgroups_for_keypairs",
        back_populates="keypairs",
    )

    user_row = relationship("UserRow", back_populates="keypairs", foreign_keys=keypairs.c.user)


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
    user = graphene.UUID()
    projects = graphene.List(lambda: graphene.String)

    ssh_public_key = graphene.String()

    vfolders = graphene.List("ai.backend.manager.models.VirtualFolder")
    compute_sessions = graphene.List(
        "ai.backend.manager.models.ComputeSession",
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
        n = await redis_helper.execute(
            ctx.redis_stat, lambda r: r.get(f"kp:{self.access_key}:num_queries")
        )
        if n is not None:
            return n
        return 0

    async def resolve_vfolders(self, info: graphene.ResolveInfo) -> Sequence[VirtualFolder]:
        ctx: GraphQueryContext = info.context
        loader = ctx.dataloader_manager.get_loader(ctx, "VirtualFolder")
        return await loader.load(self.access_key)

    async def resolve_compute_sessions(self, info: graphene.ResolveInfo, raw_status: str = None):
        ctx: GraphQueryContext = info.context
        from . import KernelStatus  # noqa: avoid circular imports

        if raw_status is not None:
            status = KernelStatus[raw_status]
        loader = ctx.dataloader_manager.get_loader(ctx, "ComputeSession", status=status)
        return await loader.load(self.access_key)

    async def resolve_concurrency_used(self, info: graphene.ResolveInfo) -> int:
        ctx: GraphQueryContext = info.context
        kp_key = "keypair.concurrency_used"
        concurrency_used = await redis_helper.execute(
            ctx.redis_stat,
            lambda r: r.get(f"{kp_key}.{self.access_key}"),
        )
        if concurrency_used is not None:
            return int(concurrency_used)
        return 0

    async def resolve_last_used(self, info: graphene.ResolveInfo) -> datetime | None:
        ctx: GraphQueryContext = info.context
        last_call_time_key = f"kp:{self.access_key}:last_call_time"
        row_ts = await redis_helper.execute(ctx.redis_stat, lambda r: r.get(last_call_time_key))
        if row_ts is None:
            return None
        return datetime.fromtimestamp(float(row_ts))

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: str = None,
        is_active: bool = None,
        limit: int = None,
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
        domain_name: str = None,
        email: str = None,
        is_active: bool = None,
        filter: str = None,
    ) -> int:
        from .group import association_groups_users, groups
        from .user import users

        j = (
            sa.join(keypairs, users, keypairs.c.user == users.c.uuid)
            .join(association_groups_users, users.c.uuid == association_groups_users.c.user_id)
            .join(groups, association_groups_users.c.group_id == groups.c.id)
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
        domain_name: str = None,
        email: str = None,
        is_active: bool = None,
        filter: str = None,
        order: str = None,
    ) -> Sequence[KeyPair]:
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
        domain_name: str = None,
        is_active: bool = None,
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
        domain_name: str = None,
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


class KeyPairInputTD(TypedDict):
    is_active: bool
    is_admin: bool
    resource_policy: str
    rate_limit: int


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
        data = cls.prepare_new_keypair(
            user_id,
            {
                "is_active": props.is_active,
                "is_admin": props.is_admin,
                "resource_policy": props.resource_policy,
                "rate_limit": props.rate_limit,
                # props.concurrency_limit is always ignored
            },
        )
        insert_query = sa.insert(keypairs).values(
            **data,
            user=sa.select([users.c.uuid]).where(users.c.email == user_id).as_scalar(),
        )
        return await simple_db_mutate_returning_item(cls, graph_ctx, insert_query, item_cls=KeyPair)

    @classmethod
    def prepare_new_keypair(cls, user_email: str, props: KeyPairInputTD) -> Dict[str, Any]:
        ak, sk = generate_keypair()
        pubkey, privkey = generate_ssh_keypair()
        data = {
            "user_id": user_email,
            "access_key": ak,
            "secret_key": sk,
            "is_active": props["is_active"],
            "is_admin": props["is_admin"],
            "resource_policy": props["resource_policy"],
            "rate_limit": props["rate_limit"],
            "num_queries": 0,
            "ssh_public_key": pubkey,
            "ssh_private_key": privkey,
        }
        return data


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
        props: ModifyUserInput,
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
            await redis_helper.execute(
                ctx.redis_stat,
                lambda r: r.delete(f"keypair.concurrency_used.{access_key}"),
            )
        return result


class Dotfile(TypedDict):
    data: str
    path: str
    perm: str


def generate_keypair() -> Tuple[AccessKey, SecretKey]:
    """
    AWS-like access key and secret key generation.
    """
    ak = "AKIA" + base64.b32encode(secrets.token_bytes(10)).decode("ascii")
    sk = secrets.token_urlsafe(30)
    return AccessKey(ak), SecretKey(sk)


def generate_ssh_keypair() -> Tuple[str, str]:
    """
    Generate RSA keypair for SSH/SFTP connection.
    """
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048,
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    ).decode("utf-8")
    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH,
        )
        .decode("utf-8")
    )
    public_key = f"{public_key.rstrip()}\n"
    private_key = f"{private_key.rstrip()}\n"
    return (public_key, private_key)


async def query_owned_dotfiles(
    conn: SAConnection,
    access_key: AccessKey,
) -> Tuple[List[Dotfile], int]:
    query = (
        sa.select([keypairs.c.dotfiles])
        .select_from(keypairs)
        .where(keypairs.c.access_key == access_key)
    )
    packed_dotfile = (await conn.execute(query)).scalar()
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


async def query_bootstrap_script(
    conn: SAConnection,
    access_key: AccessKey,
) -> Tuple[str, int]:
    query = (
        sa.select([keypairs.c.bootstrap_script])
        .select_from(keypairs)
        .where(keypairs.c.access_key == access_key)
    )
    script = (await conn.execute(query)).scalar()
    return script, MAXIMUM_DOTFILE_SIZE - len(script)


def verify_dotfile_name(dotfile: str) -> bool:
    if dotfile in RESERVED_DOTFILES:
        return False
    return True
