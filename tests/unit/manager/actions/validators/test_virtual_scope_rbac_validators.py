"""Tests for the virtual-scope-chain RBAC action validators (BA-6876 scope).

These tests drive the validators against a real ``PermissionControllerRepository``
backed by a real Postgres connection. Permissions are seeded through the
virtual-scope chain (``virtual_scopes`` / ``scope_bindings`` /
``entity_memberships``) with a self scope_binding on the owner scope, so the
non-superadmin path exercises the virtual-scope-chain permission resolution —
not the recursive scope-walk.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Sequence
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
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.actions.action.base import BaseActionTriggerMeta
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.validator.rbac import (
    VirtualScopeBulkActionRBACValidator,
)
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.validator.rbac import (
    VirtualScopeScopeActionRBACValidator,
)
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.validator.rbac import (
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
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class _VfolderUpdateAction(BaseSingleEntityAction):
    """VFOLDER:UPDATE on a single vfolder — exercises the single-entity path."""

    vfolder_id: EntityID = field(default_factory=lambda: _VFOLDER_ID)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("vfolder")

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> EntityID:
        return self.vfolder_id


@dataclass
class _VfolderUpsertAction(BaseSingleEntityAction):
    """VFOLDER:UPSERT on a single vfolder — requires the ``CREATE | UPDATE`` mask."""

    vfolder_id: EntityID = field(default_factory=lambda: _VFOLDER_ID)

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("vfolder")

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPSERT

    @override
    def entity_id(self) -> EntityID:
        return self.vfolder_id


@dataclass
class _BulkVfolderUpdateAction(BaseBulkAction):
    """VFOLDER:UPDATE on multiple vfolders — exercises the bulk validator path."""

    ids: list[EntityID]

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("vfolder")

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return self.ids


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
        domain_id=DomainID(uuid.uuid4()),
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
                username=f"user-{suffix}",
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
    permission: Permission | None = None,
) -> None:
    """Grant *operation* on *entity_type* at the scope.

    ``permission`` overrides the granted bitmask, which the resolution actually
    reads; pass it to grant a multi-bit mask the single ``operation`` column
    cannot express.
    """
    async with db.begin_session() as db_sess:
        db_sess.add(
            PermissionRow(
                role_id=role_id,
                scope_type=scope_type,
                scope_id=str(scope_id),
                entity_type=entity_type,
                operation=operation,
                permission=permission
                if permission is not None
                else Permission.from_operation(operation),
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


async def _seed_granted_user(
    db: ExtendedAsyncSAEngine,
    *,
    owner_scope_type: str,
    owner_scope_id: uuid.UUID,
    entity_type: str,
    entity_ids: Sequence[uuid.UUID],
    perm_scope_type: PermScopeType,
    perm_entity_type: PermEntityType,
    operation: OperationType,
    permission: Permission | None = None,
    scope_cap: Permission | None = None,
    entity_cap: Permission | None = None,
) -> UserData:
    """Seed a non-superadmin user whose role grants *operation* on
    *perm_entity_type* at the owner scope, reachable via the virtual-scope chain."""
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()
    await _seed_user_with_role(db, user_id=user_id, role_id=role_id)
    await _seed_vs_chain(
        db,
        owner_scope_type=owner_scope_type,
        owner_scope_id=owner_scope_id,
        entity_type=entity_type,
        entity_ids=entity_ids,
        scope_cap=scope_cap,
        entity_cap=entity_cap,
    )
    await _grant_permission(
        db,
        role_id=role_id,
        scope_type=perm_scope_type,
        scope_id=owner_scope_id,
        entity_type=perm_entity_type,
        operation=operation,
        permission=permission,
    )
    return _make_user_data(user_id, is_superadmin=False)


@pytest.fixture
def trigger_meta() -> BaseActionTriggerMeta:
    return BaseActionTriggerMeta(action_id=uuid.uuid4(), started_at=datetime.now(UTC))


@pytest.fixture
def scope_action() -> _ProjectCreateScopeAction:
    return _ProjectCreateScopeAction(scopes=[_domain_scope(_DOMAIN_ID)])


@pytest.fixture
def partially_authorized_scope_action() -> _ProjectCreateScopeAction:
    """Targets the granted domain plus one the user has no chain to."""
    return _ProjectCreateScopeAction(
        scopes=[_domain_scope(_DOMAIN_ID), _domain_scope(_OTHER_DOMAIN_ID)],
    )


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
def scope_validator(
    repository: PermissionControllerRepository,
) -> VirtualScopeScopeActionRBACValidator:
    return VirtualScopeScopeActionRBACValidator(repository, _make_config_provider())


@pytest.fixture
def single_entity_validator(
    repository: PermissionControllerRepository,
) -> VirtualScopeSingleEntityActionRBACValidator:
    return VirtualScopeSingleEntityActionRBACValidator(repository, _make_config_provider())


@pytest.fixture
def bulk_validator(
    repository: PermissionControllerRepository,
) -> VirtualScopeBulkActionRBACValidator:
    return VirtualScopeBulkActionRBACValidator(repository, _make_config_provider())


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


@pytest.fixture
async def user_with_project_create_at_domain(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    """PROJECT:CREATE granted at the domain scope, chain uncapped."""
    return await _seed_granted_user(
        db_with_rbac_tables,
        owner_scope_type="domain",
        owner_scope_id=_DOMAIN_ID,
        entity_type="domain",
        entity_ids=[_DOMAIN_ID],
        perm_scope_type=PermScopeType.DOMAIN,
        perm_entity_type=PermEntityType.PROJECT,
        operation=OperationType.CREATE,
    )


@pytest.fixture
async def user_with_read_capped_domain_scope(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    """PROJECT:CREATE granted, but the scope_binding cap clips it to READ."""
    return await _seed_granted_user(
        db_with_rbac_tables,
        owner_scope_type="domain",
        owner_scope_id=_DOMAIN_ID,
        entity_type="domain",
        entity_ids=[_DOMAIN_ID],
        perm_scope_type=PermScopeType.DOMAIN,
        perm_entity_type=PermEntityType.PROJECT,
        operation=OperationType.CREATE,
        scope_cap=Permission.READ,
    )


@pytest.fixture
async def user_with_vfolder_update_at_project(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    """VFOLDER:UPDATE granted at the project scope, chain uncapped."""
    return await _seed_granted_user(
        db_with_rbac_tables,
        owner_scope_type="project",
        owner_scope_id=_PROJECT_ID,
        entity_type="vfolder",
        entity_ids=[_VFOLDER_ID],
        perm_scope_type=PermScopeType.PROJECT,
        perm_entity_type=PermEntityType.VFOLDER,
        operation=OperationType.UPDATE,
    )


@pytest.fixture
async def user_with_read_capped_vfolder(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    """VFOLDER:UPDATE granted, but the entity_membership cap clips it to READ."""
    return await _seed_granted_user(
        db_with_rbac_tables,
        owner_scope_type="project",
        owner_scope_id=_PROJECT_ID,
        entity_type="vfolder",
        entity_ids=[_VFOLDER_ID],
        perm_scope_type=PermScopeType.PROJECT,
        perm_entity_type=PermEntityType.VFOLDER,
        operation=OperationType.UPDATE,
        entity_cap=Permission.READ,
    )


def _vfolder_user_with(
    db: ExtendedAsyncSAEngine,
    permission: Permission,
) -> Awaitable[UserData]:
    """A user whose effective VFOLDER permission at the project scope is *permission*."""
    return _seed_granted_user(
        db,
        owner_scope_type="project",
        owner_scope_id=_PROJECT_ID,
        entity_type="vfolder",
        entity_ids=[_VFOLDER_ID],
        perm_scope_type=PermScopeType.PROJECT,
        perm_entity_type=PermEntityType.VFOLDER,
        operation=OperationType.CREATE,
        permission=permission,
    )


@pytest.fixture
async def user_with_vfolder_create_only(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    return await _vfolder_user_with(db_with_rbac_tables, Permission.CREATE)


@pytest.fixture
async def user_with_vfolder_update_only(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    return await _vfolder_user_with(db_with_rbac_tables, Permission.UPDATE)


@pytest.fixture
async def user_with_vfolder_create_and_update(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    return await _vfolder_user_with(db_with_rbac_tables, Permission.CREATE | Permission.UPDATE)


@pytest.fixture
async def user_with_all_bulk_vfolders_granted(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    """VFOLDER:UPDATE granted with both bulk target vfolders in the chain."""
    return await _seed_granted_user(
        db_with_rbac_tables,
        owner_scope_type="project",
        owner_scope_id=_PROJECT_ID,
        entity_type="vfolder",
        entity_ids=[_BULK_VF_GRANTED, _BULK_VF_DENIED],
        perm_scope_type=PermScopeType.PROJECT,
        perm_entity_type=PermEntityType.VFOLDER,
        operation=OperationType.UPDATE,
    )


@pytest.fixture
async def user_with_partial_bulk_membership(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    """VFOLDER:UPDATE granted, but only _BULK_VF_GRANTED is in the chain."""
    return await _seed_granted_user(
        db_with_rbac_tables,
        owner_scope_type="project",
        owner_scope_id=_PROJECT_ID,
        entity_type="vfolder",
        entity_ids=[_BULK_VF_GRANTED],
        perm_scope_type=PermScopeType.PROJECT,
        perm_entity_type=PermEntityType.VFOLDER,
        operation=OperationType.UPDATE,
    )


@pytest.fixture
async def user_with_read_capped_bulk_vfolder(
    db_with_rbac_tables: ExtendedAsyncSAEngine,
) -> UserData:
    """VFOLDER:UPDATE granted, but the entity_membership cap clips it to READ."""
    return await _seed_granted_user(
        db_with_rbac_tables,
        owner_scope_type="project",
        owner_scope_id=_PROJECT_ID,
        entity_type="vfolder",
        entity_ids=[_BULK_VF_GRANTED],
        perm_scope_type=PermScopeType.PROJECT,
        perm_entity_type=PermEntityType.VFOLDER,
        operation=OperationType.UPDATE,
        entity_cap=Permission.READ,
    )


class TestVirtualScopeScopeActionRBACValidator:
    async def test_superadmin_bypasses_check(
        self,
        scope_validator: VirtualScopeScopeActionRBACValidator,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
        superadmin_user: UserData,
    ) -> None:
        # No permission rows seeded; bypass must succeed regardless.
        with with_user(superadmin_user):
            await scope_validator.validate(scope_action, trigger_meta)

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
        scope_validator: VirtualScopeScopeActionRBACValidator,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
    ) -> None:
        with pytest.raises(UnreachableError):
            await scope_validator.validate(scope_action, trigger_meta)

    async def test_permission_on_subject_type_at_scope_passes(
        self,
        scope_validator: VirtualScopeScopeActionRBACValidator,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_project_create_at_domain: UserData,
    ) -> None:
        with with_user(user_with_project_create_at_domain):
            await scope_validator.validate(scope_action, trigger_meta)

    async def test_unauthorized_scope_among_targets_raises(
        self,
        scope_validator: VirtualScopeScopeActionRBACValidator,
        partially_authorized_scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_project_create_at_domain: UserData,
    ) -> None:
        # One target scope is unauthorized, so the whole action must be rejected.
        with with_user(user_with_project_create_at_domain):
            with pytest.raises(NotEnoughPermission):
                await scope_validator.validate(partially_authorized_scope_action, trigger_meta)

    async def test_scope_cap_clips_granted_permission(
        self,
        scope_validator: VirtualScopeScopeActionRBACValidator,
        scope_action: _ProjectCreateScopeAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_read_capped_domain_scope: UserData,
    ) -> None:
        with with_user(user_with_read_capped_domain_scope):
            with pytest.raises(NotEnoughPermission):
                await scope_validator.validate(scope_action, trigger_meta)


class TestVirtualScopeSingleEntityActionRBACValidator:
    async def test_permission_via_chain_passes(
        self,
        single_entity_validator: VirtualScopeSingleEntityActionRBACValidator,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_vfolder_update_at_project: UserData,
    ) -> None:
        with with_user(user_with_vfolder_update_at_project):
            await single_entity_validator.validate(single_entity_action, trigger_meta)

    async def test_without_permission_raises(
        self,
        single_entity_validator: VirtualScopeSingleEntityActionRBACValidator,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_without_permission: UserData,
    ) -> None:
        with with_user(regular_user_without_permission):
            with pytest.raises(NotEnoughPermission):
                await single_entity_validator.validate(single_entity_action, trigger_meta)

    async def test_entity_cap_clips_granted_permission(
        self,
        single_entity_validator: VirtualScopeSingleEntityActionRBACValidator,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_read_capped_vfolder: UserData,
    ) -> None:
        with with_user(user_with_read_capped_vfolder):
            with pytest.raises(NotEnoughPermission):
                await single_entity_validator.validate(single_entity_action, trigger_meta)


class TestUpsertRequiresBothCreateAndUpdate:
    """An UPSERT action demands the ``CREATE | UPDATE`` mask, and the check is a
    subset test — holding just one of the two bits must be rejected."""

    @pytest.fixture
    def upsert_action(self) -> _VfolderUpsertAction:
        return _VfolderUpsertAction()

    async def test_create_only_is_rejected(
        self,
        single_entity_validator: VirtualScopeSingleEntityActionRBACValidator,
        upsert_action: _VfolderUpsertAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_vfolder_create_only: UserData,
    ) -> None:
        with with_user(user_with_vfolder_create_only):
            with pytest.raises(NotEnoughPermission):
                await single_entity_validator.validate(upsert_action, trigger_meta)

    async def test_update_only_is_rejected(
        self,
        single_entity_validator: VirtualScopeSingleEntityActionRBACValidator,
        upsert_action: _VfolderUpsertAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_vfolder_update_only: UserData,
    ) -> None:
        with with_user(user_with_vfolder_update_only):
            with pytest.raises(NotEnoughPermission):
                await single_entity_validator.validate(upsert_action, trigger_meta)

    async def test_both_bits_pass(
        self,
        single_entity_validator: VirtualScopeSingleEntityActionRBACValidator,
        upsert_action: _VfolderUpsertAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_vfolder_create_and_update: UserData,
    ) -> None:
        with with_user(user_with_vfolder_create_and_update):
            await single_entity_validator.validate(upsert_action, trigger_meta)

    async def test_single_bit_operation_still_passes_with_one_bit(
        self,
        single_entity_validator: VirtualScopeSingleEntityActionRBACValidator,
        single_entity_action: _VfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_vfolder_update_only: UserData,
    ) -> None:
        # Regression: the subset semantics must not tighten single-bit operations.
        with with_user(user_with_vfolder_update_only):
            await single_entity_validator.validate(single_entity_action, trigger_meta)


class TestVirtualScopeBulkActionRBACValidator:
    async def test_superadmin_bypasses_check(
        self,
        bulk_validator: VirtualScopeBulkActionRBACValidator,
        bulk_vfolder_action: _BulkVfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        superadmin_user: UserData,
    ) -> None:
        # No permission rows seeded; bypass must succeed regardless.
        with with_user(superadmin_user):
            await bulk_validator.validate(bulk_vfolder_action, trigger_meta)

    async def test_all_targets_granted_passes(
        self,
        bulk_validator: VirtualScopeBulkActionRBACValidator,
        bulk_vfolder_action: _BulkVfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_all_bulk_vfolders_granted: UserData,
    ) -> None:
        with with_user(user_with_all_bulk_vfolders_granted):
            await bulk_validator.validate(bulk_vfolder_action, trigger_meta)

    async def test_any_denied_target_rejects_whole_action(
        self,
        bulk_validator: VirtualScopeBulkActionRBACValidator,
        bulk_vfolder_action: _BulkVfolderUpdateAction,
        trigger_meta: BaseActionTriggerMeta,
        user_with_partial_bulk_membership: UserData,
    ) -> None:
        # _BULK_VF_DENIED has no membership, so the whole bulk action must be rejected.
        with with_user(user_with_partial_bulk_membership):
            with pytest.raises(NotEnoughPermission):
                await bulk_validator.validate(bulk_vfolder_action, trigger_meta)

    async def test_entity_cap_clips_granted_permission(
        self,
        bulk_validator: VirtualScopeBulkActionRBACValidator,
        trigger_meta: BaseActionTriggerMeta,
        user_with_read_capped_bulk_vfolder: UserData,
    ) -> None:
        with with_user(user_with_read_capped_bulk_vfolder):
            with pytest.raises(NotEnoughPermission):
                await bulk_validator.validate(
                    _BulkVfolderUpdateAction(ids=[_BULK_VF_GRANTED]),
                    trigger_meta,
                )

    async def test_empty_targets_passes(
        self,
        bulk_validator: VirtualScopeBulkActionRBACValidator,
        trigger_meta: BaseActionTriggerMeta,
        regular_user_without_permission: UserData,
    ) -> None:
        with with_user(regular_user_without_permission):
            await bulk_validator.validate(_BulkVfolderUpdateAction(ids=[]), trigger_meta)
