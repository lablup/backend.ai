"""RBAC authorization tests for creating an app config fragment (BEP-1052).

Drives the real ``ScopeActionRBACValidator`` (the validator wired to the fragment
``create`` processor) against a real ``PermissionControllerRepository`` and the actual
``CreateAppConfigFragmentAction``. This verifies the end-to-end contract the wiring
promises:

- a user may create a fragment in their **own** user scope,
- creating in **another** user's scope is denied,
- creating a **public** (global-scoped) fragment is superadmin-only.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    Permission,
    ScopeType,
)
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.action.base import BaseActionTriggerMeta
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.permission import NotEnoughPermission

# ORM cluster: configure_mappers() resolves string relationships against the registry
# when this isolated test registers rows; these keep the referenced mappers live.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ImageRow,
    ScalingGroupForDomainRow,
)

_DOMAIN = "default"


def _user_data(user_id: UserID, *, is_superadmin: bool) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=is_superadmin,
        is_superadmin=is_superadmin,
        role=UserRole.SUPERADMIN if is_superadmin else UserRole.USER,
        domain_name=_DOMAIN,
    )


async def _seed_user_with_role(
    db: ExtendedAsyncSAEngine,
    *,
    user_id: UserID,
    role_id: uuid.UUID,
) -> None:
    suffix = user_id.hex[:8]
    policy_name = f"policy-{suffix}"
    async with db.begin_session() as db_sess:
        db_sess.add(
            UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        db_sess.add(
            UserRow(
                uuid=user_id,
                email=f"user-{suffix}@test.com",
                resource_policy=policy_name,
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
            )
        )
        await db_sess.flush()
        db_sess.add(RoleRow(id=role_id, name=f"role-{suffix}", description="fragment authz test"))
        await db_sess.flush()
        db_sess.add(UserRoleRow(user_id=user_id, role_id=role_id))
        await db_sess.flush()


async def _grant_fragment_create(
    db: ExtendedAsyncSAEngine,
    *,
    role_id: uuid.UUID,
    scope_id: str,
) -> None:
    async with db.begin_session() as db_sess:
        db_sess.add(
            PermissionRow(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=scope_id,
                entity_type=EntityType.APP_CONFIG_FRAGMENT,
                operation=OperationType.CREATE,
                permission=Permission.from_operation(OperationType.CREATE),
            )
        )
        await db_sess.flush()


@pytest.fixture
def trigger_meta() -> BaseActionTriggerMeta:
    return BaseActionTriggerMeta(action_id=uuid.uuid4(), started_at=datetime.now(UTC))


@pytest.fixture
async def db_with_rbac_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with with_tables(
        database_connection,
        [
            DomainRow,
            UserResourcePolicyRow,
            KeyPairResourcePolicyRow,
            RoleRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            PermissionRow,
            ObjectPermissionRow,
            AssociationScopesEntitiesRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def repository(db_with_rbac_tables: ExtendedAsyncSAEngine) -> PermissionControllerRepository:
    return PermissionControllerRepository(db_with_rbac_tables)


@pytest.fixture
def scope_validator(repository: PermissionControllerRepository) -> ScopeActionRBACValidator:
    # MagicMock config_provider → enforcement_enabled is truthy, so the check runs.
    return ScopeActionRBACValidator(repository, MagicMock())


@pytest.fixture
async def owner_user(db_with_rbac_tables: ExtendedAsyncSAEngine) -> UserData:
    """A non-superadmin granted APP_CONFIG_FRAGMENT:CREATE on their own user scope."""
    user_id = UserID(uuid.uuid4())
    role_id = uuid.uuid4()
    await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
    await _grant_fragment_create(db_with_rbac_tables, role_id=role_id, scope_id=str(user_id))
    return _user_data(user_id, is_superadmin=False)


class TestScopeAuthorization:
    """user / domain fragment writes are authorized by the scope-chain RBAC check."""

    async def test_own_user_scope_is_allowed(
        self,
        scope_validator: ScopeActionRBACValidator,
        trigger_meta: BaseActionTriggerMeta,
        owner_user: UserData,
    ) -> None:
        action = CreateAppConfigFragmentAction(
            creator_spec=AppConfigFragmentCreatorSpec(
                config_name="cfg",
                scope_type=AppConfigScopeType.USER,
                scope_id=str(owner_user.user_id),
                config={},
            )
        )
        with with_user(owner_user):
            await scope_validator.validate(action, trigger_meta)

    async def test_another_user_scope_is_denied(
        self,
        scope_validator: ScopeActionRBACValidator,
        trigger_meta: BaseActionTriggerMeta,
        owner_user: UserData,
    ) -> None:
        other_user_id = UserID(uuid.uuid4())
        action = CreateAppConfigFragmentAction(
            creator_spec=AppConfigFragmentCreatorSpec(
                config_name="cfg",
                scope_type=AppConfigScopeType.USER,
                scope_id=str(other_user_id),
                config={},
            )
        )
        with with_user(owner_user):
            with pytest.raises(NotEnoughPermission):
                await scope_validator.validate(action, trigger_meta)


class TestPublicScopeAuthorization:
    """A public fragment is global-scoped: no role grants the write, so the scope-chain
    check denies everyone and only a superadmin bypasses it."""

    async def test_non_superadmin_is_denied(
        self,
        scope_validator: ScopeActionRBACValidator,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        action = CreateAppConfigFragmentAction(
            creator_spec=AppConfigFragmentCreatorSpec(
                config_name="cfg",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="",
                config={},
            )
        )
        with with_user(_user_data(UserID(uuid.uuid4()), is_superadmin=False)):
            with pytest.raises(NotEnoughPermission):
                await scope_validator.validate(action, trigger_meta)

    async def test_superadmin_is_allowed(
        self,
        scope_validator: ScopeActionRBACValidator,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        action = CreateAppConfigFragmentAction(
            creator_spec=AppConfigFragmentCreatorSpec(
                config_name="cfg",
                scope_type=AppConfigScopeType.PUBLIC,
                scope_id="",
                config={},
            )
        )
        with with_user(_user_data(UserID(uuid.uuid4()), is_superadmin=True)):
            await scope_validator.validate(action, trigger_meta)
