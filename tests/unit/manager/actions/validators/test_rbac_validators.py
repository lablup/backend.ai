"""Tests for RBAC action validators, focused on the superadmin bypass (BA-5721).

These tests drive the validators against a real ``PermissionControllerRepository``
backed by a real Postgres connection. Permission rows are seeded directly into
the RBAC tables instead of mocked, so the bypass path (no DB lookup) and the
non-superadmin enforcement path (real CTE-based scope chain check) are both
exercised end to end.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RBACElementType,
    ScopeType,
)
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.action.base import BaseActionTriggerMeta
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.action.single_entity import BaseSingleEntityAction
from ai.backend.manager.actions.action.types import FieldData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.validators.rbac.legacy import (
    LegacyScopeActionRBACValidator,
    LegacySingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.domain import DomainRow
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
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables

_TARGET_DOMAIN = "default"
_TARGET_VFOLDER = "vf-1"


class _ProjectCreateAction(BaseScopeAction):
    """PROJECT:CREATE at DOMAIN('default') — matches the BA-5721 reproduction."""

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType.PROJECT

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return _TARGET_DOMAIN

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.DOMAIN,
            element_id=_TARGET_DOMAIN,
        )


class _VfolderUpdateAction(BaseSingleEntityAction):
    """VFOLDER:UPDATE on a single vfolder — exercises the single-entity path."""

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType.VFOLDER

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return _TARGET_VFOLDER

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.VFOLDER,
            element_id=_TARGET_VFOLDER,
        )

    @override
    def field_data(self) -> FieldData | None:
        return None


def _make_user_data(user_id: uuid.UUID, *, is_superadmin: bool) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=is_superadmin,
        is_superadmin=is_superadmin,
        role=UserRole.SUPERADMIN if is_superadmin else UserRole.USER,
        domain_name=_TARGET_DOMAIN,
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
        db_sess.add(
            RoleRow(
                id=role_id,
                name=f"role-{suffix}",
                description="rbac validator test role",
            )
        )
        await db_sess.flush()
        db_sess.add(UserRoleRow(user_id=user_id, role_id=role_id))
        await db_sess.flush()


async def _grant_permission(
    db: ExtendedAsyncSAEngine,
    *,
    role_id: uuid.UUID,
    scope_type: ScopeType,
    scope_id: str,
    entity_type: EntityType,
    operation: OperationType,
) -> None:
    async with db.begin_session() as db_sess:
        db_sess.add(
            PermissionRow(
                role_id=role_id,
                scope_type=scope_type,
                scope_id=scope_id,
                entity_type=entity_type,
                operation=operation,
            )
        )
        await db_sess.flush()


@pytest.fixture
def trigger_meta() -> BaseActionTriggerMeta:
    return BaseActionTriggerMeta(action_id=uuid.uuid4(), started_at=datetime.now(UTC))


@pytest.fixture
def scope_action() -> _ProjectCreateAction:
    return _ProjectCreateAction()


@pytest.fixture
def single_entity_action() -> _VfolderUpdateAction:
    return _VfolderUpdateAction()


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
def repository(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> PermissionControllerRepository:
    return PermissionControllerRepository(db_with_rbac_tables)


@pytest.fixture
def superadmin_user() -> UserData:
    # Bypass path: validator returns before any DB lookup, so no rows are seeded.
    return _make_user_data(uuid.uuid4(), is_superadmin=True)


@pytest.fixture
async def regular_user_without_permission(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    user_id = uuid.uuid4()
    await _seed_user_with_role(
        db_with_rbac_tables,
        user_id=user_id,
        role_id=uuid.uuid4(),
    )
    return _make_user_data(user_id, is_superadmin=False)


@pytest.fixture
async def regular_user_with_project_create(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()
    await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
    await _grant_permission(
        db_with_rbac_tables,
        role_id=role_id,
        scope_type=ScopeType.DOMAIN,
        scope_id=_TARGET_DOMAIN,
        entity_type=EntityType.PROJECT,
        operation=OperationType.CREATE,
    )
    return _make_user_data(user_id, is_superadmin=False)


@pytest.fixture
async def regular_user_with_vfolder_update(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()
    await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
    await _grant_permission(
        db_with_rbac_tables,
        role_id=role_id,
        scope_type=ScopeType.VFOLDER,
        scope_id=_TARGET_VFOLDER,
        entity_type=EntityType.VFOLDER,
        operation=OperationType.UPDATE,
    )
    return _make_user_data(user_id, is_superadmin=False)


class TestScopeActionRBACValidator:
    async def test_superadmin_bypasses_check(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateAction,
        trigger_meta: BaseActionTriggerMeta,
        superadmin_user: UserData,
    ) -> None:
        # No permission rows seeded; bypass must succeed regardless.
        validator = ScopeActionRBACValidator(repository)
        with with_user(superadmin_user):
            await validator.validate(scope_action, trigger_meta)

    async def test_missing_user_raises(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        validator = ScopeActionRBACValidator(repository)
        with pytest.raises(UserNotFound):
            await validator.validate(scope_action, trigger_meta)

    async def test_non_superadmin_with_permission_passes(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_with_project_create: UserData,
    ) -> None:
        validator = ScopeActionRBACValidator(repository)
        with with_user(regular_user_with_project_create):
            await validator.validate(scope_action, trigger_meta)

    async def test_non_superadmin_without_permission_raises(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_without_permission: UserData,
    ) -> None:
        validator = ScopeActionRBACValidator(repository)
        with with_user(regular_user_without_permission):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(scope_action, trigger_meta)


class TestSingleEntityActionRBACValidator:
    async def test_superadmin_bypasses_check(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        superadmin_user: UserData,
    ) -> None:
        validator = SingleEntityActionRBACValidator(repository)
        with with_user(superadmin_user):
            await validator.validate(single_entity_action, trigger_meta)

    async def test_missing_user_raises(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        validator = SingleEntityActionRBACValidator(repository)
        with pytest.raises(UserNotFound):
            await validator.validate(single_entity_action, trigger_meta)

    async def test_non_superadmin_with_permission_passes(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_with_vfolder_update: UserData,
    ) -> None:
        validator = SingleEntityActionRBACValidator(repository)
        with with_user(regular_user_with_vfolder_update):
            await validator.validate(single_entity_action, trigger_meta)

    async def test_non_superadmin_without_permission_raises(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_without_permission: UserData,
    ) -> None:
        validator = SingleEntityActionRBACValidator(repository)
        with with_user(regular_user_without_permission):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(single_entity_action, trigger_meta)


class TestLegacySingleEntityActionRBACValidator:
    async def test_superadmin_bypasses_check(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        superadmin_user: UserData,
    ) -> None:
        validator = LegacySingleEntityActionRBACValidator(repository)
        with with_user(superadmin_user):
            await validator.validate(single_entity_action, trigger_meta)

    async def test_missing_user_raises(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        validator = LegacySingleEntityActionRBACValidator(repository)
        with pytest.raises(UserNotFound):
            await validator.validate(single_entity_action, trigger_meta)

    async def test_non_superadmin_with_permission_passes(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_with_vfolder_update: UserData,
    ) -> None:
        validator = LegacySingleEntityActionRBACValidator(repository)
        with with_user(regular_user_with_vfolder_update):
            await validator.validate(single_entity_action, trigger_meta)

    async def test_non_superadmin_without_permission_does_not_raise(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_without_permission: UserData,
    ) -> None:
        validator = LegacySingleEntityActionRBACValidator(repository)
        with with_user(regular_user_without_permission):
            await validator.validate(single_entity_action, trigger_meta)


class TestLegacyScopeActionRBACValidator:
    async def test_superadmin_bypasses_check(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateAction,
        trigger_meta: BaseActionTriggerMeta,
        superadmin_user: UserData,
    ) -> None:
        validator = LegacyScopeActionRBACValidator(repository)
        with with_user(superadmin_user):
            await validator.validate(scope_action, trigger_meta)

    async def test_missing_user_raises(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        validator = LegacyScopeActionRBACValidator(repository)
        with pytest.raises(UserNotFound):
            await validator.validate(scope_action, trigger_meta)

    async def test_non_superadmin_with_permission_passes(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_with_project_create: UserData,
    ) -> None:
        validator = LegacyScopeActionRBACValidator(repository)
        with with_user(regular_user_with_project_create):
            await validator.validate(scope_action, trigger_meta)

    async def test_non_superadmin_without_permission_does_not_raise(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_without_permission: UserData,
    ) -> None:
        validator = LegacyScopeActionRBACValidator(repository)
        with with_user(regular_user_without_permission):
            await validator.validate(scope_action, trigger_meta)
