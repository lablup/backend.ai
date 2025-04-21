from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, Self, Sequence

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import relationship, selectinload

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    KeyPairResourcePolicyCreator,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    KeyPairResourcePolicyModifier,
)
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    ProjectResourcePolicyCreator,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ProjectResourcePolicyModifier,
)
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    UserResourcePolicyCreator,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    UserResourcePolicyModifier,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import (
    Base,
    BigInt,
    EnumType,
    ResourceSlotColumn,
    VFolderHostPermissionColumn,
    batch_result,
    mapper_registry,
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

    def to_dataclass(
        self,
    ) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            name=self.name,
            created_at=self.created_at,
            default_for_unspecified=self.default_for_unspecified,
            total_resource_slots=self.total_resource_slots,
            max_session_lifetime=self.max_session_lifetime,
            max_concurrent_sessions=self.max_concurrent_sessions,
            max_pending_session_count=self.max_pending_session_count,
            max_pending_session_resource_slots=self.max_pending_session_resource_slots,
            max_concurrent_sftp_sessions=self.max_concurrent_sftp_sessions,
            max_containers_per_session=self.max_containers_per_session,
            idle_timeout=self.idle_timeout,
            allowed_vfolder_hosts=self.allowed_vfolder_hosts,
        )

    @classmethod
    def from_dataclass(cls, data: KeyPairResourcePolicyData) -> Self:
        return cls(
            name=data.name,
            created_at=data.created_at,
            default_for_unspecified=data.default_for_unspecified,
            total_resource_slots=data.total_resource_slots,
            max_session_lifetime=data.max_session_lifetime,
            max_concurrent_sessions=data.max_concurrent_sessions,
            max_pending_session_count=data.max_pending_session_count,
            max_pending_session_resource_slots=data.max_pending_session_resource_slots,
            max_concurrent_sftp_sessions=data.max_concurrent_sftp_sessions,
            max_containers_per_session=data.max_containers_per_session,
            idle_timeout=data.idle_timeout,
            allowed_vfolder_hosts=data.allowed_vfolder_hosts,
        )


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

    @classmethod
    def from_dataclass(cls, data: UserResourcePolicyData) -> Self:
        return cls(
            name=data.name,
            max_vfolder_count=data.max_vfolder_count,
            max_quota_scope_size=data.max_quota_scope_size,
            max_session_count_per_model_session=data.max_session_count_per_model_session,
            max_customized_image_count=data.max_customized_image_count,
        )

    def to_dataclass(self) -> UserResourcePolicyData:
        return UserResourcePolicyData(
            name=self.name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_session_count_per_model_session=self.max_session_count_per_model_session,
            max_customized_image_count=self.max_customized_image_count,
        )


project_resource_policies = sa.Table(
    "project_resource_policies",
    mapper_registry.metadata,
    sa.Column("name", sa.String(length=256), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("max_vfolder_count", sa.Integer(), nullable=False),
    sa.Column("max_quota_scope_size", sa.BigInteger(), nullable=False),
    sa.Column("max_network_count", sa.Integer(), nullable=False),
)


class ProjectResourcePolicyRow(Base):
    __table__ = project_resource_policies
    projects = relationship("GroupRow", back_populates="resource_policy_row")

    def __init__(self, name, max_vfolder_count, max_quota_scope_size, max_network_count) -> None:
        self.name = name
        self.max_vfolder_count = max_vfolder_count
        self.max_quota_scope_size = max_quota_scope_size
        self.max_network_count = max_network_count

    @classmethod
    def from_dataclass(cls, data: ProjectResourcePolicyData) -> Self:
        return cls(
            name=data.name,
            max_vfolder_count=data.max_vfolder_count,
            max_quota_scope_size=data.max_quota_scope_size,
            max_network_count=data.max_network_count,
        )

    def to_dataclass(self) -> ProjectResourcePolicyData:
        return ProjectResourcePolicyData(
            name=self.name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_network_count=self.max_network_count,
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

    def to_creator(self, name: str) -> KeyPairResourcePolicyCreator:
        default_for_unspecified = DefaultForUnspecified[self.default_for_unspecified]
        total_resource_slots = ResourceSlot.from_user_input(self.total_resource_slots, None)

        max_pending_session_resource_slots = (
            ResourceSlot.from_user_input(self.max_pending_session_resource_slots, None)
            if self.max_pending_session_resource_slots
            else None
        )

        def value_or_none(value):
            return value if value is not Undefined else None

        return KeyPairResourcePolicyCreator(
            name=name,
            default_for_unspecified=default_for_unspecified,
            total_resource_slots=total_resource_slots,
            max_session_lifetime=value_or_none(self.max_session_lifetime),
            max_concurrent_sessions=value_or_none(self.max_concurrent_sessions),
            max_concurrent_sftp_sessions=value_or_none(self.max_concurrent_sftp_sessions),
            max_containers_per_session=value_or_none(self.max_containers_per_session),
            idle_timeout=value_or_none(self.idle_timeout),
            allowed_vfolder_hosts=value_or_none(self.allowed_vfolder_hosts),
            max_vfolder_count=value_or_none(self.max_vfolder_count),
            max_vfolder_size=value_or_none(self.max_vfolder_size),
            max_quota_scope_size=value_or_none(self.max_quota_scope_size),
            max_pending_session_count=value_or_none(self.max_pending_session_count),
            max_pending_session_resource_slots=value_or_none(max_pending_session_resource_slots),
        )


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

    def to_modifier(self) -> KeyPairResourcePolicyModifier:
        default_for_unspecified = (
            DefaultForUnspecified[self.default_for_unspecified]
            if self.default_for_unspecified
            else Undefined
        )

        total_resource_slots = (
            ResourceSlot.from_user_input(self.total_resource_slots, None)
            if self.total_resource_slots
            else Undefined
        )

        return KeyPairResourcePolicyModifier(
            default_for_unspecified=OptionalState[DefaultForUnspecified].from_graphql(
                default_for_unspecified
            ),
            total_resource_slots=OptionalState[ResourceSlot].from_graphql(total_resource_slots),
            max_session_lifetime=OptionalState[int].from_graphql(self.max_session_lifetime),
            max_concurrent_sessions=OptionalState[int].from_graphql(self.max_concurrent_sessions),
            max_concurrent_sftp_sessions=OptionalState[int].from_graphql(
                self.max_concurrent_sftp_sessions
            ),
            max_containers_per_session=OptionalState[int].from_graphql(
                self.max_containers_per_session
            ),
            idle_timeout=OptionalState[int].from_graphql(self.idle_timeout),
            allowed_vfolder_hosts=OptionalState[dict[str, Any]].from_graphql(
                self.allowed_vfolder_hosts
            ),
            max_vfolder_count=OptionalState[int].from_graphql(self.max_vfolder_count),
            max_vfolder_size=OptionalState[int].from_graphql(self.max_vfolder_size),
            max_quota_scope_size=OptionalState[int].from_graphql(self.max_quota_scope_size),
            max_pending_session_count=TriState[int].from_graphql(self.max_pending_session_count),
            max_pending_session_resource_slots=TriState[dict[str, Any]].from_graphql(
                self.max_pending_session_resource_slots
            ),
        )


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
        from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
            CreateKeyPairResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await graph_ctx.processors.keypair_resource_policy.create_keypair_resource_policy.wait_for_complete(
            CreateKeyPairResourcePolicyAction(props.to_creator(name))
        )

        return CreateKeyPairResourcePolicy(
            ok=True,
            msg="",
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
        from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
            ModifyKeyPairResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await graph_ctx.processors.keypair_resource_policy.modify_keypair_resource_policy.wait_for_complete(
            ModifyKeyPairResourcePolicyAction(name, props.to_modifier())
        )

        return ModifyKeyPairResourcePolicy(
            ok=True,
            msg="",
        )


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
        from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
            DeleteKeyPairResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await graph_ctx.processors.keypair_resource_policy.delete_keypair_resource_policy.wait_for_complete(
            DeleteKeyPairResourcePolicyAction(name)
        )
        return DeleteKeyPairResourcePolicy(
            ok=True,
            msg="",
        )


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

    def to_creator(self, name: str) -> UserResourcePolicyCreator:
        def value_or_none(value):
            return value if value is not Undefined else None

        return UserResourcePolicyCreator(
            name=name,
            max_vfolder_count=value_or_none(self.max_vfolder_count),
            max_quota_scope_size=value_or_none(self.max_quota_scope_size),
            max_session_count_per_model_session=value_or_none(
                self.max_session_count_per_model_session
            ),
            max_vfolder_size=value_or_none(self.max_vfolder_size),
            max_customized_image_count=value_or_none(self.max_customized_image_count),
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

    def to_modifier(self) -> UserResourcePolicyModifier:
        return UserResourcePolicyModifier(
            max_vfolder_count=OptionalState[int].from_graphql(self.max_vfolder_count),
            max_quota_scope_size=OptionalState[int].from_graphql(self.max_quota_scope_size),
            max_session_count_per_model_session=OptionalState[int].from_graphql(
                self.max_session_count_per_model_session
            ),
            max_customized_image_count=OptionalState[int].from_graphql(
                self.max_customized_image_count
            ),
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
        from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
            CreateUserResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await (
            graph_ctx.processors.user_resource_policy.create_user_resource_policy.wait_for_complete(
                CreateUserResourcePolicyAction(props.to_creator(name))
            )
        )

        return CreateUserResourcePolicy(
            ok=True,
            msg="",
        )


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
        from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
            ModifyUserResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await (
            graph_ctx.processors.user_resource_policy.modify_user_resource_policy.wait_for_complete(
                ModifyUserResourcePolicyAction(name, props.to_modifier())
            )
        )

        return ModifyUserResourcePolicy(
            ok=True,
            msg="",
        )


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
        from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
            DeleteUserResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await (
            graph_ctx.processors.user_resource_policy.delete_user_resource_policy.wait_for_complete(
                DeleteUserResourcePolicyAction(name)
            )
        )

        return DeleteUserResourcePolicy(
            ok=True,
            msg="",
        )


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
    max_network_count = graphene.Int(
        description="Added in 24.12.0. Limitation of the number of networks created on behalf of project."
    )

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
            max_network_count=row.max_network_count,
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
    max_network_count = graphene.Int(
        description="Added in 24.12.0. Limitation of the number of networks created on behalf of project. Set as -1 to allow creating unlimited networks."
    )

    def to_creator(self, name: str) -> ProjectResourcePolicyCreator:
        def value_or_none(value):
            return value if value is not Undefined else None

        return ProjectResourcePolicyCreator(
            name=name,
            max_vfolder_count=value_or_none(self.max_vfolder_count),
            max_quota_scope_size=value_or_none(self.max_quota_scope_size),
            max_vfolder_size=value_or_none(self.max_vfolder_size),
            max_network_count=value_or_none(self.max_network_count),
        )


class ModifyProjectResourcePolicyInput(graphene.InputObjectType):
    max_vfolder_count = graphene.Int(
        description="Added in 24.03.1 and 23.09.6. Limitation of the number of project vfolders."
    )  #  Added in (24.03.1, 23.09.6)
    max_quota_scope_size = BigInt(
        description="Added in 24.03.1 and 23.09.2. Limitation of the quota size of project vfolders."
    )  #  Added in (24.03.1, 23.09.2)
    max_vfolder_size = BigInt(deprecation_reason="Deprecated since 23.09.2.")
    max_network_count = graphene.Int(
        description="Added in 24.12.0. Limitation of the number of networks created on behalf of project. Set as -1 to allow creating unlimited networks."
    )

    def to_modifier(self) -> ProjectResourcePolicyModifier:
        return ProjectResourcePolicyModifier(
            max_vfolder_count=OptionalState[int].from_graphql(self.max_vfolder_count),
            max_quota_scope_size=OptionalState[int].from_graphql(self.max_quota_scope_size),
            max_vfolder_size=OptionalState[int].from_graphql(self.max_vfolder_size),
            max_network_count=OptionalState[int].from_graphql(self.max_network_count),
        )


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
        from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
            CreateProjectResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await graph_ctx.processors.project_resource_policy.create_project_resource_policy.wait_for_complete(
            CreateProjectResourcePolicyAction(props.to_creator(name))
        )

        return CreateProjectResourcePolicy(
            ok=True,
            msg="",
        )


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
        from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
            ModifyProjectResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await graph_ctx.processors.project_resource_policy.modify_project_resource_policy.wait_for_complete(
            ModifyProjectResourcePolicyAction(name, props.to_modifier())
        )

        return ModifyProjectResourcePolicy(
            ok=True,
            msg="",
        )


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
        from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
            DeleteProjectResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await graph_ctx.processors.project_resource_policy.delete_project_resource_policy.wait_for_complete(
            DeleteProjectResourcePolicyAction(name)
        )

        return DeleteProjectResourcePolicy(
            ok=True,
            msg="",
        )
