from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, Sequence

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import relationship, selectinload

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.models.utils import execute_with_retry

from .base import (
    Base,
    BigInt,
    EnumType,
    ResourceSlotColumn,
    VFolderHostPermissionColumn,
    batch_result,
    mapper_registry,
    set_if_set,
    simple_db_mutate,
    simple_db_mutate_returning_item,
)
from .keypair import keypairs
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models"))

__all__: Sequence[str] = (
    "keypair_resource_policies",
    "user_resource_policies",
    "project_resource_policies",
    "KeyPairResourcePolicyRow",
    "KeyPairResourcePolicy",
    "DefaultForUnspecified",
    "CreateKeyPairResourcePolicy",
    "ModifyKeyPairResourcePolicy",
    "DeleteKeyPairResourcePolicy",
    "UserResourcePolicyRow",
    "UserResourcePolicy",
    "CreateUserResourcePolicy",
    "ModifyUserResourcePolicy",
    "DeleteUserResourcePolicy",
    "ProjectResourcePolicyRow",
    "ProjectResourcePolicy",
    "CreateProjectResourcePolicy",
    "ModifyProjectResourcePolicy",
    "DeleteProjectResourcePolicy",
)


keypair_resource_policies = sa.Table(
    "keypair_resource_policies",
    mapper_registry.metadata,
    sa.Column("name", sa.String(length=256), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "default_for_unspecified",
        EnumType(DefaultForUnspecified),
        default=DefaultForUnspecified.LIMITED,
        nullable=False,
    ),
    sa.Column("total_resource_slots", ResourceSlotColumn(), nullable=False),
    sa.Column("max_session_lifetime", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("max_concurrent_sessions", sa.Integer(), nullable=False),
    sa.Column("max_pending_session_count", sa.Integer(), nullable=True),
    sa.Column("max_pending_session_resource_slots", ResourceSlotColumn(), nullable=True),
    sa.Column(
        "max_concurrent_sftp_sessions", sa.Integer(), nullable=False, server_default=sa.text("1")
    ),
    sa.Column("max_containers_per_session", sa.Integer(), nullable=False),
    sa.Column("idle_timeout", sa.BigInteger(), nullable=False),
    sa.Column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default={},
    ),
    # TODO: implement with a many-to-many association table
    # sa.Column('allowed_scaling_groups', sa.Array(sa.String), nullable=False),
)


class KeyPairResourcePolicyRow(Base):
    __table__ = keypair_resource_policies
    keypairs = relationship("KeyPairRow", back_populates="resource_policy_row")


user_resource_policies = sa.Table(
    "user_resource_policies",
    mapper_registry.metadata,
    sa.Column("name", sa.String(length=256), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("max_vfolder_count", sa.Integer(), nullable=False),
    sa.Column("max_quota_scope_size", sa.BigInteger(), nullable=False),
    sa.Column("max_session_count_per_model_session", sa.Integer(), nullable=False),
    sa.Column("max_customized_image_count", sa.Integer(), nullable=False, default=3),
)


class UserResourcePolicyRow(Base):
    __table__ = user_resource_policies
    users = relationship("UserRow", back_populates="resource_policy_row")

    def __init__(
        self,
        name,
        max_vfolder_count,
        max_quota_scope_size,
        max_session_count_per_model_session,
        max_customized_image_count,
    ) -> None:
        self.name = name
        self.max_vfolder_count = max_vfolder_count
        self.max_quota_scope_size = max_quota_scope_size
        self.max_session_count_per_model_session = max_session_count_per_model_session
        self.max_customized_image_count = max_customized_image_count


project_resource_policies = sa.Table(
    "project_resource_policies",
    mapper_registry.metadata,
    sa.Column("name", sa.String(length=256), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("max_vfolder_count", sa.Integer(), nullable=False),
    sa.Column("max_quota_scope_size", sa.BigInteger(), nullable=False),
)


class ProjectResourcePolicyRow(Base):
    __table__ = project_resource_policies
    projects = relationship("GroupRow", back_populates="resource_policy_row")

    def __init__(self, name, max_vfolder_count, max_quota_scope_size) -> None:
        self.name = name
        self.max_vfolder_count = max_vfolder_count
        self.max_quota_scope_size = max_quota_scope_size


class KeyPairResourcePolicy(graphene.ObjectType):
    name = graphene.String()
    created_at = GQLDateTime()
    default_for_unspecified = graphene.String()
    total_resource_slots = graphene.JSONString()
    max_session_lifetime = graphene.Int()
    max_concurrent_sessions = graphene.Int()
    max_containers_per_session = graphene.Int()
    idle_timeout = BigInt()
    allowed_vfolder_hosts = graphene.JSONString()

    max_vfolder_count = graphene.Int(deprecation_reason="Deprecated since 23.09.4.")
    max_vfolder_size = BigInt(deprecation_reason="Deprecated since 23.09.4.")
    max_quota_scope_size = BigInt(deprecation_reason="Deprecated since 23.09.6.")
    max_concurrent_sftp_sessions = graphene.Int(description="Added in 23.03.3.")
    max_pending_session_count = graphene.Int(description="Added in 24.03.4.")
    max_pending_session_resource_slots = graphene.JSONString(description="Added in 24.03.4.")

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row | None,
    ) -> KeyPairResourcePolicy | None:
        if row is None:
            return None

        if row["max_pending_session_resource_slots"] is not None:
            max_pending_session_resource_slots = row["max_pending_session_resource_slots"].to_json()
        else:
            max_pending_session_resource_slots = None
        return cls(
            name=row["name"],
            created_at=row["created_at"],
            default_for_unspecified=row["default_for_unspecified"].name,
            total_resource_slots=row["total_resource_slots"].to_json(),
            max_session_lifetime=row["max_session_lifetime"],
            max_concurrent_sessions=row["max_concurrent_sessions"],
            max_concurrent_sftp_sessions=row["max_concurrent_sftp_sessions"],
            max_containers_per_session=row["max_containers_per_session"],
            idle_timeout=row["idle_timeout"],
            allowed_vfolder_hosts=row["allowed_vfolder_hosts"].to_json(),
            max_pending_session_count=row["max_pending_session_count"],
            max_pending_session_resource_slots=max_pending_session_resource_slots,
        )

    @classmethod
    async def load_all(cls, ctx: GraphQueryContext) -> Sequence[KeyPairResourcePolicy]:
        query = sa.select([keypair_resource_policies]).select_from(keypair_resource_policies)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]

    @classmethod
    async def load_all_user(
        cls,
        ctx: GraphQueryContext,
        access_key: str,
    ) -> Sequence[KeyPairResourcePolicy]:
        j = sa.join(
            keypairs,
            keypair_resource_policies,
            keypairs.c.resource_policy == keypair_resource_policies.c.name,
        )
        query = (
            sa.select([keypair_resource_policies])
            .select_from(j)
            .where(
                keypairs.c.user_id
                == (
                    sa.select([keypairs.c.user_id])
                    .select_from(keypairs)
                    .where(keypairs.c.access_key == access_key)
                    .as_scalar()
                ),
            )
        )
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
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
                ctx,
                conn,
                query,
                cls,
                names,
                lambda row: row["name"],
            )

    @classmethod
    async def batch_load_by_name_user(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
    ) -> Sequence[KeyPairResourcePolicy | None]:
        access_key = ctx.access_key
        j = sa.join(
            keypairs,
            keypair_resource_policies,
            keypairs.c.resource_policy == keypair_resource_policies.c.name,
        )
        query = (
            sa.select([keypair_resource_policies])
            .select_from(j)
            .where(
                (keypair_resource_policies.c.name.in_(names))
                & (keypairs.c.access_key == access_key),
            )
            .order_by(keypair_resource_policies.c.name)
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

    @classmethod
    async def batch_load_by_ak(
        cls,
        ctx: GraphQueryContext,
        access_keys: Sequence[str],
    ) -> Sequence[KeyPairResourcePolicy]:
        j = sa.join(
            keypairs,
            keypair_resource_policies,
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
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]


class CreateKeyPairResourcePolicyInput(graphene.InputObjectType):
    default_for_unspecified = graphene.String(required=True)
    total_resource_slots = graphene.JSONString(required=False, default_value={})
    max_session_lifetime = graphene.Int(required=False, default_value=0)
    max_concurrent_sessions = graphene.Int(required=True)
    max_concurrent_sftp_sessions = graphene.Int(required=False, default_value=1)
    max_containers_per_session = graphene.Int(required=True)
    idle_timeout = BigInt(required=True)
    allowed_vfolder_hosts = graphene.JSONString(required=False)
    max_vfolder_count = graphene.Int(required=False, deprecation_reason="Deprecated since 23.09.4.")
    max_vfolder_size = BigInt(required=False, deprecation_reason="Deprecated since 23.09.4.")
    max_quota_scope_size = BigInt(required=False, deprecation_reason="Deprecated since 23.09.6.")
    max_pending_session_count = graphene.Int(description="Added in 24.03.4.")
    max_pending_session_resource_slots = graphene.JSONString(description="Added in 24.03.4.")


class ModifyKeyPairResourcePolicyInput(graphene.InputObjectType):
    default_for_unspecified = graphene.String(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    max_session_lifetime = graphene.Int(required=False)
    max_concurrent_sessions = graphene.Int(required=False)
    max_concurrent_sftp_sessions = graphene.Int(required=False)
    max_containers_per_session = graphene.Int(required=False)
    idle_timeout = BigInt(required=False)
    allowed_vfolder_hosts = graphene.JSONString(required=False)
    max_vfolder_count = graphene.Int(required=False, deprecation_reason="Deprecated since 23.09.4.")
    max_vfolder_size = BigInt(required=False, deprecation_reason="Deprecated since 23.09.4.")
    max_quota_scope_size = BigInt(required=False, deprecation_reason="Deprecated since 23.09.6.")
    max_pending_session_count = graphene.Int(description="Added in 24.03.4.")
    max_pending_session_resource_slots = graphene.JSONString(description="Added in 24.03.4.")


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
            "name": name,
            "default_for_unspecified": DefaultForUnspecified[props.default_for_unspecified],
            "total_resource_slots": ResourceSlot.from_user_input(props.total_resource_slots, None),
            "max_session_lifetime": props.max_session_lifetime,
            "max_concurrent_sessions": props.max_concurrent_sessions,
            "max_concurrent_sftp_sessions": props.max_concurrent_sessions,
            "max_containers_per_session": props.max_containers_per_session,
            "idle_timeout": props.idle_timeout,
            "allowed_vfolder_hosts": props.allowed_vfolder_hosts,
        }
        set_if_set(props, data, "max_pending_session_count")
        set_if_set(
            props,
            data,
            "max_pending_session_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None) if v is not None else None,
        )
        insert_query = sa.insert(keypair_resource_policies).values(data)
        return await simple_db_mutate_returning_item(
            cls,
            info.context,
            insert_query,
            item_cls=KeyPairResourcePolicy,
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
        set_if_set(
            props,
            data,
            "default_for_unspecified",
            clean_func=lambda v: DefaultForUnspecified[v],
        )
        set_if_set(
            props,
            data,
            "total_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        set_if_set(props, data, "max_session_lifetime")
        set_if_set(props, data, "max_concurrent_sessions")
        set_if_set(props, data, "max_concurrent_sftp_sessions")
        set_if_set(props, data, "max_containers_per_session")
        set_if_set(props, data, "idle_timeout")
        set_if_set(props, data, "allowed_vfolder_hosts")
        set_if_set(props, data, "max_pending_session_count")
        set_if_set(
            props,
            data,
            "max_pending_session_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
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
        delete_query = sa.delete(keypair_resource_policies).where(
            keypair_resource_policies.c.name == name
        )
        return await simple_db_mutate(cls, info.context, delete_query)


class UserResourcePolicy(graphene.ObjectType):
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    created_at = GQLDateTime(required=True)
    max_vfolder_count = graphene.Int(
        description="Added in 24.03.1 and 23.09.6. Limitation of the number of user vfolders."
    )  # Added in (24.03.1, 23.09.6)
    max_quota_scope_size = BigInt(
        description="Added in 24.03.1 and 23.09.2. Limitation of the quota size of user vfolders."
    )  # Added in (24.03.1, 23.09.2)
    max_vfolder_size = BigInt(deprecation_reason="Deprecated since 23.09.2.")
    max_session_count_per_model_session = graphene.Int(
        description="Added in 24.03.1 and 23.09.10. Maximum available number of sessions per single model service which the user is in charge of."
    )
    max_customized_image_count = graphene.Int(
        description="Added in 24.03.0. Maximum available number of customized images one can publish to."
    )

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: UserResourcePolicyRow | None,
    ) -> UserResourcePolicy | None:
        if row is None:
            return None
        return cls(
            id=f"UserResourcePolicy:{row.name}",
            name=row.name,
            created_at=row.created_at,
            max_vfolder_count=row.max_vfolder_count,
            max_quota_scope_size=row.max_quota_scope_size,
            max_session_count_per_model_session=row.max_session_count_per_model_session,
            max_customized_image_count=row.max_customized_image_count,
        )

    @classmethod
    async def load_all(cls, ctx: GraphQueryContext) -> Sequence[UserResourcePolicy]:
        query = sa.select(UserResourcePolicyRow)
        async with ctx.db.begin_readonly_session() as sess:
            return [
                obj
                async for r in (await sess.stream_scalars(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]

    @classmethod
    async def batch_load_by_name(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
    ) -> Sequence[UserResourcePolicy | None]:
        query = (
            sa.select(UserResourcePolicyRow)
            .where(UserResourcePolicyRow.name.in_(names))
            .order_by(UserResourcePolicyRow.name)
        )
        async with ctx.db.begin_readonly_session() as sess:
            return await batch_result(
                ctx,
                sess,
                query,
                cls,
                names,
                lambda row: row.name,
            )

    @classmethod
    async def batch_load_by_user(
        cls,
        ctx: GraphQueryContext,
        user_uuids: Sequence[uuid.UUID],
    ) -> Sequence[UserResourcePolicy]:
        from .user import UserRow

        query = (
            sa.select(UserRow)
            .where((UserRow.uuid.in_(user_uuids)))
            .options(selectinload(UserRow.resource_policy_row))
            .order_by(UserRow.resource_policy)
        )
        async with ctx.db.begin_readonly_session() as sess:
            return [
                obj
                async for r in (await sess.stream_scalars(query))
                if (obj := cls.from_row(ctx, r.resource_policy_row)) is not None
            ]


class CreateUserResourcePolicyInput(graphene.InputObjectType):
    max_vfolder_count = graphene.Int(
        description="Added in 24.03.1 and 23.09.6. Limitation of the number of user vfolders."
    )  # Added in (24.03.1, 23.09.6)
    max_quota_scope_size = BigInt(
        description="Added in 24.03.1 and 23.09.2. Limitation of the quota size of user vfolders."
    )  # Added in (24.03.1, 23.09.2)
    max_session_count_per_model_session = graphene.Int(
        description="Added in 24.03.1 and 23.09.10. Maximum available number of sessions per single model service which the user is in charge of."
    )
    max_vfolder_size = BigInt(deprecation_reason="Deprecated since 23.09.2.")
    max_customized_image_count = graphene.Int(
        description="Added in 24.03.0. Maximum available number of customized images one can publish to."
    )


class ModifyUserResourcePolicyInput(graphene.InputObjectType):
    max_vfolder_count = graphene.Int(
        description="Added in 24.03.1 and 23.09.6. Limitation of the number of user vfolders."
    )  # Added in (24.03.1, 23.09.6)
    max_quota_scope_size = BigInt(
        description="Added in 24.03.1 and 23.09.2. Limitation of the quota size of user vfolders."
    )  # Added in (24.03.1, 23.09.2)
    max_session_count_per_model_session = graphene.Int(
        description="Added in 24.03.1 and 23.09.10. Maximum available number of sessions per single model service which the user is in charge of."
    )
    max_customized_image_count = graphene.Int(
        description="Added in 24.03.0. Maximum available number of customized images one can publish to."
    )


class CreateUserResourcePolicy(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = CreateUserResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    resource_policy = graphene.Field(lambda: UserResourcePolicy, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: CreateUserResourcePolicyInput,
    ) -> CreateUserResourcePolicy:
        graph_ctx: GraphQueryContext = info.context

        async def _do_mutate() -> UserResourcePolicy:
            async with graph_ctx.db.begin_session() as sess:
                row = UserResourcePolicyRow(
                    name,
                    props.max_vfolder_count,
                    props.max_quota_scope_size,
                    props.max_session_count_per_model_session,
                    props.max_customized_image_count,
                )
                sess.add(row)
                await sess.flush()
                query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
                return cls(
                    True,
                    "success",
                    UserResourcePolicy.from_row(graph_ctx, await sess.scalar(query)),
                )

        return await execute_with_retry(_do_mutate)


class ModifyUserResourcePolicy(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyUserResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyUserResourcePolicyInput,
    ) -> ModifyUserResourcePolicy:
        data: Dict[str, Any] = {}
        set_if_set(props, data, "max_vfolder_count")
        set_if_set(props, data, "max_quota_scope_size")
        set_if_set(props, data, "max_session_count_per_model_session")
        set_if_set(props, data, "max_customized_image_count")
        update_query = (
            sa.update(UserResourcePolicyRow).values(data).where(UserResourcePolicyRow.name == name)
        )
        return await simple_db_mutate(cls, info.context, update_query)


class DeleteUserResourcePolicy(graphene.Mutation):
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
    ) -> DeleteUserResourcePolicy:
        delete_query = sa.delete(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
        return await simple_db_mutate(cls, info.context, delete_query)


class ProjectResourcePolicy(graphene.ObjectType):
    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    created_at = GQLDateTime(required=True)
    max_vfolder_count = graphene.Int(
        description="Added in 24.03.1 and 23.09.6. Limitation of the number of project vfolders."
    )  #  Added in (24.03.1, 23.09.6)
    max_quota_scope_size = BigInt(
        description="Added in 24.03.1 and 23.09.2. Limitation of the quota size of project vfolders."
    )  #  Added in (24.03.1, 23.09.2)
    max_vfolder_size = BigInt(deprecation_reason="Deprecated since 23.09.2.")

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: ProjectResourcePolicyRow | None,
    ) -> ProjectResourcePolicy | None:
        if row is None:
            return None
        return cls(
            id=f"ProjectResourcePolicy:{row.name}",
            name=row.name,
            created_at=row.created_at,
            max_vfolder_count=row.max_vfolder_count,
            max_vfolder_size=row.max_quota_scope_size,
            max_quota_scope_size=row.max_quota_scope_size,
        )

    @classmethod
    async def load_all(cls, ctx: GraphQueryContext) -> Sequence[ProjectResourcePolicy]:
        query = sa.select(ProjectResourcePolicyRow)
        async with ctx.db.begin_readonly_session() as sess:
            return [
                obj
                async for r in (await sess.stream_scalars(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]

    @classmethod
    async def batch_load_by_name(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
    ) -> Sequence[ProjectResourcePolicy | None]:
        query = (
            sa.select(ProjectResourcePolicyRow)
            .where(ProjectResourcePolicyRow.name.in_(names))
            .order_by(ProjectResourcePolicyRow.name)
        )
        async with ctx.db.begin_readonly_session() as sess:
            return await batch_result(
                ctx,
                sess,
                query,
                cls,
                names,
                lambda row: row.name,
            )

    @classmethod
    async def batch_load_by_project(
        cls,
        ctx: GraphQueryContext,
        project_uuids: Sequence[uuid.UUID],
    ) -> Sequence[ProjectResourcePolicy]:
        from .group import GroupRow

        query = (
            sa.select(GroupRow)
            .where((GroupRow.id.in_(project_uuids)))
            .order_by(GroupRow.resource_policy)
            .options(selectinload(GroupRow.resource_policy_row))
        )
        async with ctx.db.begin_readonly_session() as sess:
            return [
                obj
                async for r in (await sess.stream(query))
                if (obj := cls.from_row(ctx, r.resource_policy_row)) is not None
            ]


class CreateProjectResourcePolicyInput(graphene.InputObjectType):
    max_vfolder_count = graphene.Int(
        description="Added in 24.03.1 and 23.09.6. Limitation of the number of project vfolders."
    )  #  Added in (24.03.1, 23.09.6)
    max_quota_scope_size = BigInt(
        description="Added in 24.03.1 and 23.09.2. Limitation of the quota size of project vfolders."
    )  #  Added in (24.03.1, 23.09.2)
    max_vfolder_size = BigInt(deprecation_reason="Deprecated since 23.09.2.")


class ModifyProjectResourcePolicyInput(graphene.InputObjectType):
    max_vfolder_count = graphene.Int(
        description="Added in 24.03.1 and 23.09.6. Limitation of the number of project vfolders."
    )  #  Added in (24.03.1, 23.09.6)
    max_quota_scope_size = BigInt(
        description="Added in 24.03.1 and 23.09.2. Limitation of the quota size of project vfolders."
    )  #  Added in (24.03.1, 23.09.2)
    max_vfolder_size = BigInt(deprecation_reason="Deprecated since 23.09.2.")


class CreateProjectResourcePolicy(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = CreateProjectResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    resource_policy = graphene.Field(lambda: ProjectResourcePolicy, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: CreateProjectResourcePolicyInput,
    ) -> CreateProjectResourcePolicy:
        graph_ctx: GraphQueryContext = info.context

        async def _do_mutate() -> ProjectResourcePolicy:
            async with graph_ctx.db.begin_session() as sess:
                row = ProjectResourcePolicyRow(
                    name, props.max_vfolder_count, props.max_quota_scope_size
                )
                sess.add(row)
                await sess.flush()
                query = sa.select(ProjectResourcePolicyRow).where(
                    ProjectResourcePolicyRow.name == name
                )
                return cls(
                    True,
                    "success",
                    ProjectResourcePolicy.from_row(graph_ctx, await sess.scalar(query)),
                )

        return await execute_with_retry(_do_mutate)


class ModifyProjectResourcePolicy(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyProjectResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyProjectResourcePolicyInput,
    ) -> ModifyProjectResourcePolicy:
        data: Dict[str, Any] = {}
        set_if_set(props, data, "max_vfolder_count")
        set_if_set(props, data, "max_quota_scope_size")
        update_query = (
            sa.update(ProjectResourcePolicyRow)
            .values(data)
            .where(ProjectResourcePolicyRow.name == name)
        )
        return await simple_db_mutate(cls, info.context, update_query)


class DeleteProjectResourcePolicy(graphene.Mutation):
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
    ) -> DeleteProjectResourcePolicy:
        delete_query = sa.delete(ProjectResourcePolicyRow).where(
            ProjectResourcePolicyRow.name == name
        )
        return await simple_db_mutate(cls, info.context, delete_query)
