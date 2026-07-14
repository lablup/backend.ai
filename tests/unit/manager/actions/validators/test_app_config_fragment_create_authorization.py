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
from ai.backend.manager.services.app_config_fragment.validators import (
    PublicAppConfigFragmentWriteValidator,
)
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ImageRow,
    ScalingGroupForDomainRow,
)

_DOMAIN = "default"


def _create_action(scope_type: AppConfigScopeType, scope_id: str) -> CreateAppConfigFragmentAction:
    return CreateAppConfigFragmentAction(
        creator_spec=AppConfigFragmentCreatorSpec(
            config_name="cfg",
            scope_type=scope_type,
            scope_id=scope_id,
            config={},
        )
    )


def _user_data(user_id: uuid.UUID, *, is_superadmin: bool) -> UserData:
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
    user_id: uuid.UUID,
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


class _CreateValidatorChain:
    """Runs the fragment create processor's validator chain in wired order.

    Mirrors ``AppConfigFragmentProcessors``: the public guard runs first, then the generic
    scope-chain RBAC check for user / domain scopes.
    """

    def __init__(self, repository: PermissionControllerRepository) -> None:
        # MagicMock config_provider → enforcement_enabled is truthy, so both checks run.
        self._guard = PublicAppConfigFragmentWriteValidator(MagicMock())
        self._scope = ScopeActionRBACValidator(repository, MagicMock())

    async def validate(
        self, action: CreateAppConfigFragmentAction, meta: BaseActionTriggerMeta
    ) -> None:
        await self._guard.validate(action, meta)
        await self._scope.validate(action, meta)


@pytest.fixture
def validator(repository: PermissionControllerRepository) -> _CreateValidatorChain:
    return _CreateValidatorChain(repository)


@pytest.fixture
async def owner_user(db_with_rbac_tables: ExtendedAsyncSAEngine) -> UserData:
    """A non-superadmin granted APP_CONFIG_FRAGMENT:CREATE on their own user scope."""
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()
    await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
    await _grant_fragment_create(db_with_rbac_tables, role_id=role_id, scope_id=str(user_id))
    return _user_data(user_id, is_superadmin=False)


class TestCreateAuthorization:
    async def test_own_user_scope_is_allowed(
        self,
        validator: _CreateValidatorChain,
        trigger_meta: BaseActionTriggerMeta,
        owner_user: UserData,
    ) -> None:
        action = _create_action(AppConfigScopeType.USER, str(owner_user.user_id))
        with with_user(owner_user):
            await validator.validate(action, trigger_meta)

    async def test_another_user_scope_is_denied(
        self,
        validator: _CreateValidatorChain,
        trigger_meta: BaseActionTriggerMeta,
        owner_user: UserData,
    ) -> None:
        other_user_id = uuid.uuid4()
        action = _create_action(AppConfigScopeType.USER, str(other_user_id))
        with with_user(owner_user):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(action, trigger_meta)

    async def test_public_scope_is_denied_for_non_superadmin(
        self,
        validator: _CreateValidatorChain,
        trigger_meta: BaseActionTriggerMeta,
        owner_user: UserData,
    ) -> None:
        # Public fragments are global-scoped (no RBAC scope element); the empty-id target
        # resolves to no scope, so a non-superadmin — even one that owns its user scope —
        # is denied.
        action = _create_action(AppConfigScopeType.PUBLIC, "")
        with with_user(owner_user):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(action, trigger_meta)

    async def test_public_scope_is_allowed_for_superadmin(
        self,
        validator: _CreateValidatorChain,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        superadmin = _user_data(uuid.uuid4(), is_superadmin=True)
        action = _create_action(AppConfigScopeType.PUBLIC, "")
        with with_user(superadmin):
            await validator.validate(action, trigger_meta)
