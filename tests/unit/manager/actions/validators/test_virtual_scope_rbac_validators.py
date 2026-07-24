"""Tests for the virtual-scope-chain RBAC action validators (BA-6876 scope).

These tests drive the validators against a real ``PermissionControllerRepository``
backed by a real Postgres connection. Permissions are seeded through the
virtual-scope chain (``virtual_scopes`` / ``scope_bindings`` /
``entity_memberships``) with a self scope_binding on the owner scope, so the
non-superadmin path exercises ``check_permission_via_virtual_scope`` — not the
recursive scope-walk.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import override
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.common.data.permission.types import (
    EntityType as PermEntityType,
)
from ai.backend.common.data.permission.types import (
    OperationType,
    Permission,
)
from ai.backend.common.data.permission.types import (
    ScopeType as PermScopeType,
)
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.exception import UnreachableError
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.actions.action.base import BaseActionTriggerMeta
from ai.backend.manager.actions.bulk.base import BaseBulkAction
from ai.backend.manager.actions.bulk.validator.rbac import (
    VirtualScopeBulkActionRBACValidator,
)
from ai.backend.manager.actions.scope.base import BaseScopeAction
from ai.backend.manager.actions.scope.validator.rbac import (
    VirtualScopeScopeActionRBACValidator,
)
from ai.backend.manager.actions.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.single_entity.validator.rbac import (
    VirtualScopeSingleEntityActionRBACValidator,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.agent import AgentRow

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
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
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ImageRow,
    ScalingGroupForDomainRow,
)

_DOMAIN_ID: ScopeID = uuid.uuid4()
_OTHER_DOMAIN_ID: ScopeID = uuid.uuid4()
_PROJECT_ID: ScopeID = uuid.uuid4()
_VFOLDER_ID: EntityID = uuid.uuid4()
_BULK_VF_GRANTED: EntityID = uuid.uuid4()
_BULK_VF_DENIED: EntityID = uuid.uuid4()


class _ProjectCreateScopeAction(BaseScopeAction):
    """PROJECT:CREATE at domain scopes — subject type differs from the scope type."""

    _scopes: Sequence[ScopeRef]

    def __init__(self, scopes: Sequence[ScopeRef]) -> None:
        self._scopes = scopes

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return self._scopes

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("project")

    @classmethod
    @override
    def required_permission(cls) -> Permission:
        return Permission.CREATE


@dataclass
class _VfolderUpdateAction(BaseSingleEntityAction):
    """VFOLDER:UPDATE on a single vfolder — exercises the single-entity path."""

    vfolder_id: EntityID = field(default_factory=lambda: _VFOLDER_ID)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("vfolder")

    @override
    def entity_id(self) -> EntityID:
        return self.vfolder_id

    @classmethod
    @override
    def required_permission(cls) -> Permission:
        return Permission.UPDATE


@dataclass
class _BulkVfolderUpdateAction(BaseBulkAction):
    """VFOLDER:UPDATE on multiple vfolders — exercises the bulk validator path."""

    ids: list[EntityID]

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("vfolder")

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return self.ids

    @classmethod
    @override
    def required_permission(cls) -> Permission:
        return Permission.UPDATE


def _domain_scope(scope_id: ScopeID) -> ScopeRef:
    return ScopeRef(scope_type=ScopeType("domain"), scope_id=scope_id)


def _make_user_data(user_id: uuid.UUID, *, is_superadmin: bool) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=is_superadmin,
        is_superadmin=is_superadmin,
        role=UserRole.SUPERADMIN if is_superadmin else UserRole.USER,
        domain_name="default",
    )


def _make_config_provider(*, enforcement_enabled: bool = True) -> MagicMock:
    config_provider = MagicMock()
    config_provider.config.manager.rbac.enforcement_enabled = enforcement_enabled
    return config_provider


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
                description="virtual-scope validator test role",
            )
        )
        await db_sess.flush()
        db_sess.add(UserRoleRow(user_id=user_id, role_id=role_id))
        await db_sess.flush()


async def _grant_permission(
    db: ExtendedAsyncSAEngine,
    *,
    role_id: uuid.UUID,
    scope_type: PermScopeType,
    scope_id: uuid.UUID,
    entity_type: PermEntityType,
    operation: OperationType,
) -> None:
    async with db.begin_session() as db_sess:
        db_sess.add(
            PermissionRow(
                role_id=role_id,
                scope_type=scope_type,
                scope_id=str(scope_id),
                entity_type=entity_type,
                operation=operation,
                permission=Permission.from_operation(operation),
            )
        )
        await db_sess.flush()


async def _seed_vs_chain(
    db: ExtendedAsyncSAEngine,
    *,
    owner_scope_type: str,
    owner_scope_id: uuid.UUID,
    entity_type: str,
    entity_ids: Sequence[uuid.UUID],
    scope_cap: Permission | None = None,
    entity_cap: Permission | None = None,
) -> None:
    """Materialize the owner's virtual scope with a self scope_binding and one
    entity membership per id: ``owner scope -> VS(owner) -> entities``."""
    vs_id = VirtualScopeID(uuid.uuid4())
    async with db.begin_session() as db_sess:
        db_sess.add(
            VirtualScopeRow(
                id=vs_id,
                scope_type=ScopeType(owner_scope_type),
                scope_id=owner_scope_id,
            )
        )
        await db_sess.flush()
        db_sess.add(
            ScopeBindingRow(
                virtual_scope_id=vs_id,
                scope_type=ScopeType(owner_scope_type),
                scope_id=owner_scope_id,
                permission_cap=scope_cap,
            )
        )
        for entity_id in entity_ids:
            db_sess.add(
                EntityMembershipRow(
                    virtual_scope_id=vs_id,
                    entity_type=EntityType(entity_type),
                    entity_id=entity_id,
                    permission_cap=entity_cap,
                )
            )
        await db_sess.flush()


@pytest.fixture
def trigger_meta() -> BaseActionTriggerMeta:
    return BaseActionTriggerMeta(action_id=uuid.uuid4(), started_at=datetime.now(UTC))


@pytest.fixture
def scope_action() -> _ProjectCreateScopeAction:
    return _ProjectCreateScopeAction(scopes=[_domain_scope(_DOMAIN_ID)])


@pytest.fixture
def single_entity_action() -> _VfolderUpdateAction:
    return _VfolderUpdateAction()


@pytest.fixture
def bulk_vfolder_action() -> _BulkVfolderUpdateAction:
    return _BulkVfolderUpdateAction(ids=[_BULK_VF_GRANTED, _BULK_VF_DENIED])


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
            VirtualScopeRow,
            ScopeBindingRow,
            EntityMembershipRow,
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
    await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=uuid.uuid4())
    return _make_user_data(user_id, is_superadmin=False)


class TestVirtualScopeScopeActionRBACValidator:
    async def test_superadmin_bypasses_check(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
        superadmin_user: UserData,
    ) -> None:
        # No permission rows seeded; bypass must succeed regardless.
        validator = VirtualScopeScopeActionRBACValidator(repository, _make_config_provider())
        with with_user(superadmin_user):
            await validator.validate(scope_action, trigger_meta)

    async def test_enforcement_disabled_skips_check(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        # Short-circuits before the user-context lookup, so no user is set.
        validator = VirtualScopeScopeActionRBACValidator(
            repository, _make_config_provider(enforcement_enabled=False)
        )
        await validator.validate(scope_action, trigger_meta)

    async def test_missing_user_raises(
        self,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        validator = VirtualScopeScopeActionRBACValidator(repository, _make_config_provider())
        with pytest.raises(UnreachableError):
            await validator.validate(scope_action, trigger_meta)

    async def test_permission_on_subject_type_at_scope_passes(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
        await _seed_vs_chain(
            db_with_rbac_tables,
            owner_scope_type="domain",
            owner_scope_id=_DOMAIN_ID,
            entity_type="domain",
            entity_ids=[_DOMAIN_ID],
        )
        await _grant_permission(
            db_with_rbac_tables,
            role_id=role_id,
            scope_type=PermScopeType.DOMAIN,
            scope_id=_DOMAIN_ID,
            entity_type=PermEntityType.PROJECT,
            operation=OperationType.CREATE,
        )

        validator = VirtualScopeScopeActionRBACValidator(repository, _make_config_provider())
        with with_user(_make_user_data(user_id, is_superadmin=False)):
            await validator.validate(scope_action, trigger_meta)

    async def test_unauthorized_scope_among_targets_raises(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        repository: PermissionControllerRepository,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        # Permission chain exists only for _DOMAIN_ID; the other target scope
        # is unauthorized, so the whole action must be rejected.
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
        await _seed_vs_chain(
            db_with_rbac_tables,
            owner_scope_type="domain",
            owner_scope_id=_DOMAIN_ID,
            entity_type="domain",
            entity_ids=[_DOMAIN_ID],
        )
        await _grant_permission(
            db_with_rbac_tables,
            role_id=role_id,
            scope_type=PermScopeType.DOMAIN,
            scope_id=_DOMAIN_ID,
            entity_type=PermEntityType.PROJECT,
            operation=OperationType.CREATE,
        )
        action = _ProjectCreateScopeAction(
            scopes=[_domain_scope(_DOMAIN_ID), _domain_scope(_OTHER_DOMAIN_ID)],
        )

        validator = VirtualScopeScopeActionRBACValidator(repository, _make_config_provider())
        with with_user(_make_user_data(user_id, is_superadmin=False)):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(action, trigger_meta)

    async def test_scope_cap_clips_granted_permission(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        repository: PermissionControllerRepository,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
        await _seed_vs_chain(
            db_with_rbac_tables,
            owner_scope_type="domain",
            owner_scope_id=_DOMAIN_ID,
            entity_type="domain",
            entity_ids=[_DOMAIN_ID],
            scope_cap=Permission.READ,
        )
        await _grant_permission(
            db_with_rbac_tables,
            role_id=role_id,
            scope_type=PermScopeType.DOMAIN,
            scope_id=_DOMAIN_ID,
            entity_type=PermEntityType.PROJECT,
            operation=OperationType.CREATE,
        )

        validator = VirtualScopeScopeActionRBACValidator(repository, _make_config_provider())
        with with_user(_make_user_data(user_id, is_superadmin=False)):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(scope_action, trigger_meta)


class TestVirtualScopeSingleEntityActionRBACValidator:
    async def test_permission_via_chain_passes(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
        await _seed_vs_chain(
            db_with_rbac_tables,
            owner_scope_type="project",
            owner_scope_id=_PROJECT_ID,
            entity_type="vfolder",
            entity_ids=[_VFOLDER_ID],
        )
        await _grant_permission(
            db_with_rbac_tables,
            role_id=role_id,
            scope_type=PermScopeType.PROJECT,
            scope_id=_PROJECT_ID,
            entity_type=PermEntityType.VFOLDER,
            operation=OperationType.UPDATE,
        )

        validator = VirtualScopeSingleEntityActionRBACValidator(repository, _make_config_provider())
        with with_user(_make_user_data(user_id, is_superadmin=False)):
            await validator.validate(single_entity_action, trigger_meta)

    async def test_without_permission_raises(
        self,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_without_permission: UserData,
    ) -> None:
        validator = VirtualScopeSingleEntityActionRBACValidator(repository, _make_config_provider())
        with with_user(regular_user_without_permission):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(single_entity_action, trigger_meta)

    async def test_entity_cap_clips_granted_permission(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        repository: PermissionControllerRepository,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
        await _seed_vs_chain(
            db_with_rbac_tables,
            owner_scope_type="project",
            owner_scope_id=_PROJECT_ID,
            entity_type="vfolder",
            entity_ids=[_VFOLDER_ID],
            entity_cap=Permission.READ,
        )
        await _grant_permission(
            db_with_rbac_tables,
            role_id=role_id,
            scope_type=PermScopeType.PROJECT,
            scope_id=_PROJECT_ID,
            entity_type=PermEntityType.VFOLDER,
            operation=OperationType.UPDATE,
        )

        validator = VirtualScopeSingleEntityActionRBACValidator(repository, _make_config_provider())
        with with_user(_make_user_data(user_id, is_superadmin=False)):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(single_entity_action, trigger_meta)


class TestVirtualScopeBulkActionRBACValidator:
    async def test_superadmin_bypasses_check(
        self,
        repository: PermissionControllerRepository,
        bulk_vfolder_action: _BulkVfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        superadmin_user: UserData,
    ) -> None:
        # No permission rows seeded; bypass must succeed regardless.
        validator = VirtualScopeBulkActionRBACValidator(repository, _make_config_provider())
        with with_user(superadmin_user):
            await validator.validate(bulk_vfolder_action, trigger_meta)

    async def test_all_targets_granted_passes(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        repository: PermissionControllerRepository,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
        await _seed_vs_chain(
            db_with_rbac_tables,
            owner_scope_type="project",
            owner_scope_id=_PROJECT_ID,
            entity_type="vfolder",
            entity_ids=[_BULK_VF_GRANTED, _BULK_VF_DENIED],
        )
        await _grant_permission(
            db_with_rbac_tables,
            role_id=role_id,
            scope_type=PermScopeType.PROJECT,
            scope_id=_PROJECT_ID,
            entity_type=PermEntityType.VFOLDER,
            operation=OperationType.UPDATE,
        )

        validator = VirtualScopeBulkActionRBACValidator(repository, _make_config_provider())
        with with_user(_make_user_data(user_id, is_superadmin=False)):
            await validator.validate(
                _BulkVfolderUpdateAction(ids=[_BULK_VF_GRANTED, _BULK_VF_DENIED]),
                trigger_meta,
            )

    async def test_any_denied_target_rejects_whole_action(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        repository: PermissionControllerRepository,
        bulk_vfolder_action: _BulkVfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        # Only _BULK_VF_GRANTED is attached to the project's VS; the other id
        # has no membership, so the whole bulk action must be rejected.
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
        await _seed_vs_chain(
            db_with_rbac_tables,
            owner_scope_type="project",
            owner_scope_id=_PROJECT_ID,
            entity_type="vfolder",
            entity_ids=[_BULK_VF_GRANTED],
        )
        await _grant_permission(
            db_with_rbac_tables,
            role_id=role_id,
            scope_type=PermScopeType.PROJECT,
            scope_id=_PROJECT_ID,
            entity_type=PermEntityType.VFOLDER,
            operation=OperationType.UPDATE,
        )

        validator = VirtualScopeBulkActionRBACValidator(repository, _make_config_provider())
        with with_user(_make_user_data(user_id, is_superadmin=False)):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(bulk_vfolder_action, trigger_meta)

    async def test_entity_cap_clips_granted_permission(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        repository: PermissionControllerRepository,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        await _seed_user_with_role(db_with_rbac_tables, user_id=user_id, role_id=role_id)
        await _seed_vs_chain(
            db_with_rbac_tables,
            owner_scope_type="project",
            owner_scope_id=_PROJECT_ID,
            entity_type="vfolder",
            entity_ids=[_BULK_VF_GRANTED],
            entity_cap=Permission.READ,
        )
        await _grant_permission(
            db_with_rbac_tables,
            role_id=role_id,
            scope_type=PermScopeType.PROJECT,
            scope_id=_PROJECT_ID,
            entity_type=PermEntityType.VFOLDER,
            operation=OperationType.UPDATE,
        )

        validator = VirtualScopeBulkActionRBACValidator(repository, _make_config_provider())
        with with_user(_make_user_data(user_id, is_superadmin=False)):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(
                    _BulkVfolderUpdateAction(ids=[_BULK_VF_GRANTED]),
                    trigger_meta,
                )

    async def test_empty_targets_passes(
        self,
        repository: PermissionControllerRepository,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_without_permission: UserData,
    ) -> None:
        validator = VirtualScopeBulkActionRBACValidator(repository, _make_config_provider())
        with with_user(regular_user_without_permission):
            await validator.validate(_BulkVfolderUpdateAction(ids=[]), trigger_meta)
