from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import selectinload

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
    keypair_resource_policies,
    project_resource_policies,
    user_resource_policies,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.types import OptionalState, TriState

from .base import (
    BigInt,
    batch_result,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.keypair_resource_policy.creators import (
        KeyPairResourcePolicyCreatorSpec,
    )
    from ai.backend.manager.repositories.keypair_resource_policy.updaters import (
        KeyPairResourcePolicyUpdaterSpec,
    )
    from ai.backend.manager.repositories.project_resource_policy.creators import (
        ProjectResourcePolicyCreatorSpec,
    )
    from ai.backend.manager.repositories.project_resource_policy.updaters import (
        ProjectResourcePolicyUpdaterSpec,
    )
    from ai.backend.manager.repositories.user_resource_policy.creators import (
        UserResourcePolicyCreatorSpec,
    )
    from ai.backend.manager.repositories.user_resource_policy.updaters import (
        UserResourcePolicyUpdaterSpec,
    )

    from .schema import GraphQueryContext


def _get_keypair_resource_policy_creator_spec() -> type[KeyPairResourcePolicyCreatorSpec]:
    from ai.backend.manager.repositories.keypair_resource_policy.creators import (
        KeyPairResourcePolicyCreatorSpec,
    )

    return KeyPairResourcePolicyCreatorSpec


def _get_keypair_resource_policy_updater_spec() -> type[KeyPairResourcePolicyUpdaterSpec]:
    from ai.backend.manager.repositories.keypair_resource_policy.updaters import (
        KeyPairResourcePolicyUpdaterSpec,
    )

    return KeyPairResourcePolicyUpdaterSpec


def _get_project_resource_policy_creator_spec() -> type[ProjectResourcePolicyCreatorSpec]:
    from ai.backend.manager.repositories.project_resource_policy.creators import (
        ProjectResourcePolicyCreatorSpec,
    )

    return ProjectResourcePolicyCreatorSpec


def _get_project_resource_policy_updater_spec() -> type[ProjectResourcePolicyUpdaterSpec]:
    from ai.backend.manager.repositories.project_resource_policy.updaters import (
        ProjectResourcePolicyUpdaterSpec,
    )

    return ProjectResourcePolicyUpdaterSpec


def _get_user_resource_policy_creator_spec() -> type[UserResourcePolicyCreatorSpec]:
    from ai.backend.manager.repositories.user_resource_policy.creators import (
        UserResourcePolicyCreatorSpec,
    )

    return UserResourcePolicyCreatorSpec


def _get_user_resource_policy_updater_spec() -> type[UserResourcePolicyUpdaterSpec]:
    from ai.backend.manager.repositories.user_resource_policy.updaters import (
        UserResourcePolicyUpdaterSpec,
    )

    return UserResourcePolicyUpdaterSpec


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__ = (
    "CreateKeyPairResourcePolicy",
    "CreateProjectResourcePolicy",
    "CreateUserResourcePolicy",
    "DeleteKeyPairResourcePolicy",
    "DeleteProjectResourcePolicy",
    "DeleteUserResourcePolicy",
    "KeyPairResourcePolicy",
    "ModifyKeyPairResourcePolicy",
    "ModifyProjectResourcePolicy",
    "ModifyUserResourcePolicy",
    "ProjectResourcePolicy",
    "UserResourcePolicy",
)


class KeyPairResourcePolicy(graphene.ObjectType):  # type: ignore[misc]
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

        if row.max_pending_session_resource_slots is not None:
            max_pending_session_resource_slots = row.max_pending_session_resource_slots.to_json()
        else:
            max_pending_session_resource_slots = None
        return cls(
            name=row.name,
            created_at=row.created_at,
            default_for_unspecified=row.default_for_unspecified.name,
            total_resource_slots=row.total_resource_slots.to_json(),
            max_session_lifetime=row.max_session_lifetime,
            max_concurrent_sessions=row.max_concurrent_sessions,
            max_concurrent_sftp_sessions=row.max_concurrent_sftp_sessions,
            max_containers_per_session=row.max_containers_per_session,
            idle_timeout=row.idle_timeout,
            allowed_vfolder_hosts=row.allowed_vfolder_hosts.to_json(),
            max_pending_session_count=row.max_pending_session_count,
            max_pending_session_resource_slots=max_pending_session_resource_slots,
        )

    @classmethod
    async def load_all(cls, ctx: GraphQueryContext) -> Sequence[KeyPairResourcePolicy]:
        query = sa.select(keypair_resource_policies).select_from(keypair_resource_policies)
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
            sa.select(keypair_resource_policies)
            .select_from(j)
            .where(
                keypairs.c.user_id
                == (
                    sa.select(keypairs.c.user_id)
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
            sa.select(keypair_resource_policies)
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
                lambda row: row.name,
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
            sa.select(keypair_resource_policies)
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
                lambda row: row.name,
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
            sa.select(keypair_resource_policies)
            .select_from(j)
            .where(keypairs.c.access_key.in_(access_keys))
            .order_by(keypair_resource_policies.c.name)
        )
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]


class CreateKeyPairResourcePolicyInput(graphene.InputObjectType):  # type: ignore[misc]
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

    def to_creator(self, name: str) -> Creator[KeyPairResourcePolicyRow]:
        default_for_unspecified = DefaultForUnspecified[self.default_for_unspecified]
        total_resource_slots = ResourceSlot.from_user_input(self.total_resource_slots, None)

        max_pending_session_resource_slots = (
            ResourceSlot.from_user_input(self.max_pending_session_resource_slots, None)
            if self.max_pending_session_resource_slots
            else None
        )

        def value_or_none(value: Any) -> Any:
            return value if value is not Undefined else None

        CreatorSpec = _get_keypair_resource_policy_creator_spec()
        return Creator(
            spec=CreatorSpec(
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
                max_pending_session_resource_slots=value_or_none(
                    max_pending_session_resource_slots
                ),
            )
        )


class ModifyKeyPairResourcePolicyInput(graphene.InputObjectType):  # type: ignore[misc]
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

    def to_updater(self, name: str) -> Updater[KeyPairResourcePolicyRow]:
        default_for_unspecified = (
            DefaultForUnspecified[self.default_for_unspecified]
            if self.default_for_unspecified is not Undefined
            else Undefined
        )

        total_resource_slots = (
            ResourceSlot.from_user_input(self.total_resource_slots, None)
            if self.total_resource_slots is not Undefined
            else Undefined
        )

        UpdaterSpec = _get_keypair_resource_policy_updater_spec()
        return Updater(
            spec=UpdaterSpec(
                default_for_unspecified=OptionalState[DefaultForUnspecified].from_graphql(
                    default_for_unspecified
                ),
                total_resource_slots=OptionalState[ResourceSlot].from_graphql(total_resource_slots),
                max_session_lifetime=OptionalState[int].from_graphql(self.max_session_lifetime),
                max_concurrent_sessions=OptionalState[int].from_graphql(
                    self.max_concurrent_sessions
                ),
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
                max_pending_session_count=TriState[int].from_graphql(
                    self.max_pending_session_count
                ),
                max_pending_session_resource_slots=TriState[dict[str, Any]].from_graphql(
                    self.max_pending_session_resource_slots
                ),
            ),
            pk_value=name,
        )


class CreateKeyPairResourcePolicy(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
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


class ModifyKeyPairResourcePolicy(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyKeyPairResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyKeyPairResourcePolicyInput,
    ) -> ModifyKeyPairResourcePolicy:
        from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
            ModifyKeyPairResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await graph_ctx.processors.keypair_resource_policy.modify_keypair_resource_policy.wait_for_complete(
            ModifyKeyPairResourcePolicyAction(name, props.to_updater(name))
        )

        return ModifyKeyPairResourcePolicy(
            ok=True,
            msg="",
        )


class DeleteKeyPairResourcePolicy(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
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


class UserResourcePolicy(graphene.ObjectType):  # type: ignore[misc]
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
            .where(user_resource_policies.c.name.in_(names))
            .order_by(user_resource_policies.c.name)
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
        from ai.backend.manager.models.user import UserRow

        query = (
            sa.select(UserRow)
            .where(UserRow.uuid.in_(user_uuids))
            .options(selectinload(UserRow.resource_policy_row))
            .order_by(UserRow.resource_policy)
        )
        async with ctx.db.begin_readonly_session() as sess:
            return [
                obj
                async for r in (await sess.stream_scalars(query))
                if (obj := cls.from_row(ctx, r.resource_policy_row)) is not None
            ]


class CreateUserResourcePolicyInput(graphene.InputObjectType):  # type: ignore[misc]
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

    def to_creator(self, name: str) -> Creator[UserResourcePolicyRow]:
        def value_or_default(value: Any, default: int) -> int:
            return value if value is not Undefined and value is not None else default

        CreatorSpec = _get_user_resource_policy_creator_spec()
        return Creator(
            spec=CreatorSpec(
                name=name,
                max_vfolder_count=value_or_default(self.max_vfolder_count, 0),
                max_quota_scope_size=value_or_default(self.max_quota_scope_size, 0),
                max_session_count_per_model_session=value_or_default(
                    self.max_session_count_per_model_session, 0
                ),
                max_customized_image_count=value_or_default(self.max_customized_image_count, 3),
            )
        )


class ModifyUserResourcePolicyInput(graphene.InputObjectType):  # type: ignore[misc]
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

    def to_updater(self, name: str) -> Updater[UserResourcePolicyRow]:
        UpdaterSpec = _get_user_resource_policy_updater_spec()
        return Updater(
            spec=UpdaterSpec(
                max_vfolder_count=OptionalState[int].from_graphql(self.max_vfolder_count),
                max_quota_scope_size=OptionalState[int].from_graphql(self.max_quota_scope_size),
                max_session_count_per_model_session=OptionalState[int].from_graphql(
                    self.max_session_count_per_model_session
                ),
                max_customized_image_count=OptionalState[int].from_graphql(
                    self.max_customized_image_count
                ),
            ),
            pk_value=name,
        )


class CreateUserResourcePolicy(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
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


class ModifyUserResourcePolicy(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyUserResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
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
                ModifyUserResourcePolicyAction(name, props.to_updater(name))
            )
        )

        return ModifyUserResourcePolicy(
            ok=True,
            msg="",
        )


class DeleteUserResourcePolicy(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
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


class ProjectResourcePolicy(graphene.ObjectType):  # type: ignore[misc]
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
            .where(project_resource_policies.c.name.in_(names))
            .order_by(project_resource_policies.c.name)
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
        from ai.backend.manager.models.group import GroupRow

        query = (
            sa.select(GroupRow)
            .where(GroupRow.id.in_(project_uuids))
            .order_by(GroupRow.resource_policy)
            .options(selectinload(GroupRow.resource_policy_row))
        )
        async with ctx.db.begin_readonly_session() as sess:
            return [
                obj
                async for r in (await sess.stream(query))
                if (obj := cls.from_row(ctx, r.resource_policy_row)) is not None
            ]


class CreateProjectResourcePolicyInput(graphene.InputObjectType):  # type: ignore[misc]
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

    def to_creator(self, name: str) -> Creator[ProjectResourcePolicyRow]:
        def value_or_default(value: Any, default: int) -> int:
            return value if value is not Undefined and value is not None else default

        CreatorSpec = _get_project_resource_policy_creator_spec()
        return Creator(
            spec=CreatorSpec(
                name=name,
                max_vfolder_count=value_or_default(self.max_vfolder_count, 0),
                max_quota_scope_size=value_or_default(self.max_quota_scope_size, 0),
                max_network_count=value_or_default(self.max_network_count, 0),
            )
        )


class ModifyProjectResourcePolicyInput(graphene.InputObjectType):  # type: ignore[misc]
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

    def to_updater(self, name: str) -> Updater[ProjectResourcePolicyRow]:
        UpdaterSpec = _get_project_resource_policy_updater_spec()
        return Updater(
            spec=UpdaterSpec(
                max_vfolder_count=OptionalState[int].from_graphql(self.max_vfolder_count),
                max_quota_scope_size=OptionalState[int].from_graphql(self.max_quota_scope_size),
                max_vfolder_size=OptionalState[int].from_graphql(self.max_vfolder_size),
                max_network_count=OptionalState[int].from_graphql(self.max_network_count),
            ),
            pk_value=name,
        )


class CreateProjectResourcePolicy(graphene.Mutation):  # type: ignore[misc]
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
        root: Any,
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


class ModifyProjectResourcePolicy(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyProjectResourcePolicyInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyProjectResourcePolicyInput,
    ) -> ModifyProjectResourcePolicy:
        from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
            ModifyProjectResourcePolicyAction,
        )

        graph_ctx: GraphQueryContext = info.context
        await graph_ctx.processors.project_resource_policy.modify_project_resource_policy.wait_for_complete(
            ModifyProjectResourcePolicyAction(name, props.to_updater(name))
        )

        return ModifyProjectResourcePolicy(
            ok=True,
            msg="",
        )


class DeleteProjectResourcePolicy(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
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
