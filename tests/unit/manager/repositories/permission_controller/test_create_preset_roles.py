"""
Tests for RoleManager.create_preset_roles().

Verifies that scope/user creation auto-generates roles from active role presets:
a role row owned by the scope, its scope association, and a shallow snapshot of
the preset's permissions. Roles are created only for active presets whose
scope_type matches the target scope.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.status import RoleStatus

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry, so the forward-reachable rows below must be imported. Kept live by
# the _ORM_CLUSTER reference.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.network import NetworkRow
from ai.backend.manager.models.rbac_models import ObjectPermissionRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.vfolder import VFolderInvitationRow, VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager
from ai.backend.testutils.db import TableOrORM, with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


PRESET_ROLE_TABLES: Sequence[TableOrORM] = [
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    AssociationScopesEntitiesRow,
    PermissionRow,
]


_ORM_CLUSTER = (
    AgentResourceRow,
    AgentRow,
    AssocGroupUserRow,
    AssociationContainerRegistriesGroupsRow,
    AssociationScopesEntitiesRow,
    ContainerRegistryRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentPolicyRow,
    DeploymentRevisionResourceSlotRow,
    DeploymentRevisionRow,
    DomainRow,
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
    GroupRow,
    ImageAliasRow,
    ImageRow,
    KernelRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    NetworkRow,
    ObjectPermissionRow,
    ProjectResourcePolicyRow,
    ReplicaGroupRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    RoleRow,
    RoutingRow,
    RuntimeVariantRow,
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
    SessionRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)


@dataclass(frozen=True)
class SeededPreset:
    name: str
    scope_type: ScopeType
    auto_assign: bool
    permissions: tuple[tuple[EntityType, OperationType], ...]


async def _seed_preset(db: ExtendedAsyncSAEngine, preset: SeededPreset, *, deleted: bool) -> None:
    async with db.begin_session() as db_sess:
        preset_row = RolePresetRow(
            name=preset.name,
            scope_type=preset.scope_type,
            auto_assign=preset.auto_assign,
            deleted=deleted,
        )
        db_sess.add(preset_row)
        await db_sess.flush()
        db_sess.add_all([
            RolePermissionPresetRow(
                role_preset_id=preset_row.id,
                entity_type=entity_type,
                operation=operation,
            )
            for entity_type, operation in preset.permissions
        ])
        await db_sess.flush()


class TestCreatePresetRoles:
    """Tests for auto-generating roles from role presets on scope/user creation."""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, PRESET_ROLE_TABLES):
            yield database_connection

    @pytest.fixture
    def role_manager(self) -> RoleManager:
        return RoleManager()

    @pytest.fixture
    async def domain_preset(self, db_with_tables: ExtendedAsyncSAEngine) -> SeededPreset:
        preset = SeededPreset(
            name="domain-viewer",
            scope_type=ScopeType.DOMAIN,
            auto_assign=False,
            permissions=(
                (EntityType.VFOLDER, OperationType.READ),
                (EntityType.SESSION, OperationType.READ),
            ),
        )
        await _seed_preset(db_with_tables, preset, deleted=False)
        return preset

    @pytest.fixture
    async def auto_assign_user_preset(self, db_with_tables: ExtendedAsyncSAEngine) -> SeededPreset:
        preset = SeededPreset(
            name="user-default",
            scope_type=ScopeType.USER,
            auto_assign=True,
            permissions=(),
        )
        await _seed_preset(db_with_tables, preset, deleted=False)
        return preset

    @pytest.fixture
    async def project_preset(self, db_with_tables: ExtendedAsyncSAEngine) -> SeededPreset:
        preset = SeededPreset(
            name="project-only",
            scope_type=ScopeType.PROJECT,
            auto_assign=False,
            permissions=(),
        )
        await _seed_preset(db_with_tables, preset, deleted=False)
        return preset

    @pytest.fixture
    async def deleted_domain_preset(self, db_with_tables: ExtendedAsyncSAEngine) -> SeededPreset:
        preset = SeededPreset(
            name="domain-archived",
            scope_type=ScopeType.DOMAIN,
            auto_assign=False,
            permissions=(),
        )
        await _seed_preset(db_with_tables, preset, deleted=True)
        return preset

    @pytest.fixture
    async def two_domain_presets(self, db_with_tables: ExtendedAsyncSAEngine) -> list[SeededPreset]:
        presets = [
            SeededPreset(
                name="domain-admin",
                scope_type=ScopeType.DOMAIN,
                auto_assign=False,
                permissions=((EntityType.SESSION, OperationType.READ),),
            ),
            SeededPreset(
                name="domain-member",
                scope_type=ScopeType.DOMAIN,
                auto_assign=False,
                permissions=((EntityType.VFOLDER, OperationType.READ),),
            ),
        ]
        for preset in presets:
            await _seed_preset(db_with_tables, preset, deleted=False)
        return presets

    async def test_creates_role_with_permissions_for_matching_preset(
        self,
        role_manager: RoleManager,
        db_with_tables: ExtendedAsyncSAEngine,
        domain_preset: SeededPreset,
    ) -> None:
        """A matching active preset yields a role, its scope association, and permissions."""
        domain_id = str(uuid.uuid4())
        scope_id = ScopeId(scope_type=ScopeType.DOMAIN, scope_id=domain_id)

        async with db_with_tables.begin_session() as db_sess:
            created = await role_manager.create_preset_roles(db_sess, scope_id)

        assert len(created) == 1
        assert created[0].name == domain_preset.name
        assert created[0].source == RoleSource.SYSTEM
        assert created[0].status == RoleStatus.ACTIVE

        async with db_with_tables.begin_session() as db_sess:
            role_row = await db_sess.scalar(
                sa.select(RoleRow).where(RoleRow.name == domain_preset.name)
            )
            assert role_row is not None
            assert role_row.id == created[0].id

            assoc_row = await db_sess.scalar(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.entity_id == str(role_row.id)
                )
            )
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.DOMAIN
            assert assoc_row.scope_id == domain_id

            permission_rows = list(
                await db_sess.scalars(
                    sa.select(PermissionRow).where(PermissionRow.role_id == role_row.id)
                )
            )
            for row in permission_rows:
                assert row.scope_type == ScopeType.DOMAIN
                assert row.scope_id == domain_id
            assert {(row.entity_type, row.operation) for row in permission_rows} == set(
                domain_preset.permissions
            )

    async def test_auto_assign_is_inherited_from_preset(
        self,
        role_manager: RoleManager,
        db_with_tables: ExtendedAsyncSAEngine,
        auto_assign_user_preset: SeededPreset,
    ) -> None:
        """The created role's auto_assign flag mirrors the preset's."""
        scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(uuid.uuid4()))

        async with db_with_tables.begin_session() as db_sess:
            created = await role_manager.create_preset_roles(db_sess, scope_id)

        assert len(created) == 1
        assert created[0].auto_assign is True

        async with db_with_tables.begin_session() as db_sess:
            role_row = await db_sess.scalar(sa.select(RoleRow).where(RoleRow.id == created[0].id))
            assert role_row is not None
            assert role_row.auto_assign is True

    async def test_no_matching_scope_type_creates_nothing(
        self,
        role_manager: RoleManager,
        db_with_tables: ExtendedAsyncSAEngine,
        project_preset: SeededPreset,
    ) -> None:
        """Presets whose scope_type differs from the target scope are ignored."""
        scope_id = ScopeId(scope_type=ScopeType.DOMAIN, scope_id=str(uuid.uuid4()))

        async with db_with_tables.begin_session() as db_sess:
            created = await role_manager.create_preset_roles(db_sess, scope_id)

        assert created == []

        async with db_with_tables.begin_session() as db_sess:
            role_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(RoleRow))
            assert role_count == 0

    async def test_deleted_preset_is_skipped(
        self,
        role_manager: RoleManager,
        db_with_tables: ExtendedAsyncSAEngine,
        deleted_domain_preset: SeededPreset,
    ) -> None:
        """Soft-deleted presets do not provision roles."""
        scope_id = ScopeId(scope_type=ScopeType.DOMAIN, scope_id=str(uuid.uuid4()))

        async with db_with_tables.begin_session() as db_sess:
            created = await role_manager.create_preset_roles(db_sess, scope_id)

        assert created == []

        async with db_with_tables.begin_session() as db_sess:
            role_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(RoleRow))
            assert role_count == 0

    async def test_multiple_matching_presets_each_yield_a_role(
        self,
        role_manager: RoleManager,
        db_with_tables: ExtendedAsyncSAEngine,
        two_domain_presets: list[SeededPreset],
    ) -> None:
        """Every active matching preset produces its own role."""
        scope_id = ScopeId(scope_type=ScopeType.DOMAIN, scope_id=str(uuid.uuid4()))

        async with db_with_tables.begin_session() as db_sess:
            created = await role_manager.create_preset_roles(db_sess, scope_id)

        assert {role.name for role in created} == {p.name for p in two_domain_presets}

        async with db_with_tables.begin_session() as db_sess:
            role_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(RoleRow))
            assert role_count == len(two_domain_presets)
