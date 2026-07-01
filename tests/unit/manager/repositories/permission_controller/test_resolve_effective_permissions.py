"""
Tests for PermissionDBSource.resolve_effective_permissions().
Covers batched scope chain traversal returning per-entity operation sets.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Mapping
from dataclasses import dataclass, field

import pytest

from ai.backend.common.data.permission.types import (
    RBACElementType,
    RelationType,
)
from ai.backend.manager.data.permission.role import PermissionResolutionKey
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    Permission,
    ScopeType,
)
from ai.backend.manager.data.user.types import UserStatus

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
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
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
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderInvitationRow, VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables

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


@dataclass
class PermissionEntry:
    """A single permission to create in permission_setup fixture."""

    scope_key: str
    operation: OperationType
    entity_type: EntityType = EntityType.VFOLDER


@dataclass
class EffectiveFixture:
    """Pre-built fixture data for effective permissions tests."""

    user_id: uuid.UUID
    role_id: uuid.UUID
    domain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vfolder_ids: list[str] = field(default_factory=list)
    # Extra IDs for multi-project / multi-domain tests
    domain_b_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_b_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_c_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Extra role for multi-role tests
    role_b_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self) -> None:
        if not self.vfolder_ids:
            self.vfolder_ids = [str(uuid.uuid4()) for _ in range(3)]


class TestResolveEffectivePermissions:
    """Tests for batched effective permissions resolution."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
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
    def db_source(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionDBSource:
        return PermissionDBSource(db_with_rbac_tables)

    @pytest.fixture
    def fixture_ids(self) -> EffectiveFixture:
        return EffectiveFixture(
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
        )

    # ── User + role fixtures ──

    @pytest.fixture
    async def user_with_active_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
    ) -> EffectiveFixture:
        """Create a user with an active role (no permissions yet)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name="test-rbac-policy",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            db_sess.add(policy)
            user = UserRow(
                uuid=fixture_ids.user_id,
                email="testuser@test.com",
                resource_policy="test-rbac-policy",
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
            )
            db_sess.add(user)
            await db_sess.flush()

            role = RoleRow(
                id=fixture_ids.role_id,
                name="test-role",
                description="Test role for effective permissions",
            )
            db_sess.add(role)
            await db_sess.flush()

            user_role = UserRoleRow(
                user_id=fixture_ids.user_id,
                role_id=fixture_ids.role_id,
            )
            db_sess.add(user_role)
            await db_sess.flush()

        return fixture_ids

    @pytest.fixture
    async def user_with_inactive_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
    ) -> EffectiveFixture:
        """Create a user with an inactive role."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name="test-rbac-policy",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            db_sess.add(policy)
            user = UserRow(
                uuid=fixture_ids.user_id,
                email="testuser@test.com",
                resource_policy="test-rbac-policy",
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
            )
            db_sess.add(user)
            await db_sess.flush()

            role = RoleRow(
                id=fixture_ids.role_id,
                name="inactive-role",
                status=RoleStatus.INACTIVE,
            )
            db_sess.add(role)
            await db_sess.flush()

            user_role = UserRoleRow(
                user_id=fixture_ids.user_id,
                role_id=fixture_ids.role_id,
            )
            db_sess.add(user_role)
            await db_sess.flush()

        return fixture_ids

    @pytest.fixture
    async def user_with_two_roles(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
    ) -> EffectiveFixture:
        """Create a user with two active roles (no permissions yet)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name="test-rbac-policy",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            db_sess.add(policy)
            user = UserRow(
                uuid=fixture_ids.user_id,
                email="testuser@test.com",
                resource_policy="test-rbac-policy",
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
            )
            db_sess.add(user)
            await db_sess.flush()

            role_a = RoleRow(
                id=fixture_ids.role_id,
                name="role-a",
            )
            role_b = RoleRow(
                id=fixture_ids.role_b_id,
                name="role-b",
            )
            db_sess.add(role_a)
            db_sess.add(role_b)
            await db_sess.flush()

            db_sess.add(UserRoleRow(user_id=fixture_ids.user_id, role_id=fixture_ids.role_id))
            db_sess.add(UserRoleRow(user_id=fixture_ids.user_id, role_id=fixture_ids.role_b_id))
            await db_sess.flush()

        return fixture_ids

    # ── Association fixtures ──

    @pytest.fixture
    async def all_vfolders_in_project_auto(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
    ) -> None:
        """All vfolders belong to the same PROJECT (auto edge)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            for vfolder_id in fixture_ids.vfolder_ids:
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.PROJECT,
                        scope_id=fixture_ids.project_id,
                        entity_type=EntityType.VFOLDER,
                        entity_id=vfolder_id,
                        relation_type=RelationType.AUTO,
                    )
                )
            await db_sess.flush()

    @pytest.fixture
    async def project_in_domain_auto(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
    ) -> None:
        """PROJECT belongs to DOMAIN (auto edge)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=fixture_ids.domain_id,
                    entity_type=EntityType.PROJECT,
                    entity_id=fixture_ids.project_id,
                    relation_type=RelationType.AUTO,
                )
            )
            await db_sess.flush()

    @pytest.fixture
    async def mixed_vfolder_edges(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
    ) -> None:
        """vfolder[0] AUTO, vfolder[1] REF, vfolder[2] no association."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture_ids.project_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=fixture_ids.vfolder_ids[0],
                    relation_type=RelationType.AUTO,
                )
            )
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture_ids.project_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=fixture_ids.vfolder_ids[1],
                    relation_type=RelationType.REF,
                )
            )
            await db_sess.flush()

    @pytest.fixture
    async def multi_project_two_domains(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
    ) -> None:
        """Two domains with separate project chains.

        domain_a ← project_a ← vfolder[0]
        domain_a ← project_b ← vfolder[1]
        domain_b ← project_c ← vfolder[2]
        """
        f = fixture_ids
        async with db_with_rbac_tables.begin_session() as db_sess:
            # domain_a ← project_a ← vfolder[0]
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=f.domain_id,
                    entity_type=EntityType.PROJECT,
                    entity_id=f.project_id,
                    relation_type=RelationType.AUTO,
                )
            )
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=f.project_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=f.vfolder_ids[0],
                    relation_type=RelationType.AUTO,
                )
            )
            # domain_a ← project_b ← vfolder[1]
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=f.domain_id,
                    entity_type=EntityType.PROJECT,
                    entity_id=f.project_b_id,
                    relation_type=RelationType.AUTO,
                )
            )
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=f.project_b_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=f.vfolder_ids[1],
                    relation_type=RelationType.AUTO,
                )
            )
            # domain_b ← project_c ← vfolder[2]
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=f.domain_b_id,
                    entity_type=EntityType.PROJECT,
                    entity_id=f.project_c_id,
                    relation_type=RelationType.AUTO,
                )
            )
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=f.project_c_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=f.vfolder_ids[2],
                    relation_type=RelationType.AUTO,
                )
            )
            await db_sess.flush()

    # ── Permission fixture ──

    @pytest.fixture
    async def permission_setup(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
        request: pytest.FixtureRequest,
    ) -> None:
        scope_map: dict[str, tuple[ScopeType, str]] = {
            "vfolder_0": (ScopeType.VFOLDER, fixture_ids.vfolder_ids[0]),
            "vfolder_1": (ScopeType.VFOLDER, fixture_ids.vfolder_ids[1]),
            "project": (ScopeType.PROJECT, fixture_ids.project_id),
            "domain": (ScopeType.DOMAIN, fixture_ids.domain_id),
        }
        for entry in request.param:
            scope_type, scope_id = scope_map[entry.scope_key]
            async with db_with_rbac_tables.begin_session() as db_sess:
                db_sess.add(
                    PermissionRow(
                        role_id=fixture_ids.role_id,
                        scope_type=scope_type,
                        scope_id=scope_id,
                        entity_type=entry.entity_type,
                        operation=entry.operation,
                        permission=Permission.from_operation(entry.operation),
                    )
                )
                await db_sess.flush()

    # ── Helpers ──

    def _make_keys(
        self,
        fixture: EffectiveFixture,
        entity_type: RBACElementType = RBACElementType.VFOLDER,
    ) -> list[PermissionResolutionKey]:
        return [
            PermissionResolutionKey(
                user_id=fixture.user_id,
                element_type=RBACElementType.VFOLDER,
                entity_id=vfolder_id,
                subject_entity_type=entity_type,
            )
            for vfolder_id in fixture.vfolder_ids
        ]

    @staticmethod
    def _ops_by_entity_id(
        result: Mapping[PermissionResolutionKey, frozenset[OperationType]],
    ) -> dict[str, frozenset[OperationType]]:
        return {key.entity_id: ops for key, ops in result.items()}

    # ── Tests: empty / no permission ──

    async def test_empty_input_returns_empty(
        self,
        db_source: PermissionDBSource,
    ) -> None:
        """Empty key sequence returns empty mapping."""
        result = await db_source.resolve_effective_permissions([])
        assert result == {}

    async def test_no_permission_returns_empty_sets(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        all_vfolders_in_project_auto: None,
    ) -> None:
        """No permissions assigned -> all entities get empty operation sets."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result[vfolder_id] == set()

    # ── Tests: scope chain ──

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                id="project-read",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_single_operation_via_project_scope(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """All vfolders in same project with READ -> all get {READ}."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        assert len(result) == 3
        for vfolder_id in fixture.vfolder_ids:
            assert result[vfolder_id] == {OperationType.READ}

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [
                    PermissionEntry("project", OperationType.READ),
                    PermissionEntry("project", OperationType.UPDATE),
                    PermissionEntry("project", OperationType.SOFT_DELETE),
                ],
                id="project-multiple-ops",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_multiple_operations_via_project_scope(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """Multiple operations at project scope propagate to all vfolders."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        expected = {OperationType.READ, OperationType.UPDATE, OperationType.SOFT_DELETE}
        for vfolder_id in fixture.vfolder_ids:
            assert result[vfolder_id] == expected

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.UPDATE)],
                id="domain-update",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_operations_via_domain_chain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        all_vfolders_in_project_auto: None,
        project_in_domain_auto: None,
        permission_setup: None,
    ) -> None:
        """Permission at DOMAIN scope propagates through chain to all vfolders."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result[vfolder_id] == {OperationType.UPDATE}

    # ── Tests: self-scope ──

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("vfolder_0", OperationType.READ)],
                id="self-scope-v0",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_self_scope_grants_individually(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        permission_setup: None,
    ) -> None:
        """Self-scope permission on vfolder[0] only; others empty."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        assert result[fixture.vfolder_ids[0]] == {OperationType.READ}
        assert result[fixture.vfolder_ids[1]] == set()
        assert result[fixture.vfolder_ids[2]] == set()

    # ── Tests: mixed edges ──

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                id="project-read",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_mixed_edges_only_auto_gets_operations(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        mixed_vfolder_edges: None,
        permission_setup: None,
    ) -> None:
        """AUTO edge -> {READ}, REF edge -> empty, no edge -> empty."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        assert result[fixture.vfolder_ids[0]] == {OperationType.READ}
        assert result[fixture.vfolder_ids[1]] == set()
        assert result[fixture.vfolder_ids[2]] == set()

    # ── Tests: chain + self-scope combined ──

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [
                    PermissionEntry("project", OperationType.READ),
                    PermissionEntry("vfolder_1", OperationType.UPDATE),
                ],
                id="chain-read-self-update",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_chain_and_self_scope_union(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        mixed_vfolder_edges: None,
        permission_setup: None,
    ) -> None:
        """vfolder[0] gets READ via chain, vfolder[1] gets UPDATE via self-scope."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        assert result[fixture.vfolder_ids[0]] == {OperationType.READ}
        assert result[fixture.vfolder_ids[1]] == {OperationType.UPDATE}
        assert result[fixture.vfolder_ids[2]] == set()

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [
                    PermissionEntry("project", OperationType.READ),
                    PermissionEntry("vfolder_0", OperationType.UPDATE),
                ],
                id="chain-plus-self-on-same-entity",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_chain_and_self_scope_merge_on_same_entity(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """vfolder[0] gets {READ, UPDATE}: READ from chain, UPDATE from self-scope."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        assert result[fixture.vfolder_ids[0]] == {
            OperationType.READ,
            OperationType.UPDATE,
        }
        assert result[fixture.vfolder_ids[1]] == {OperationType.READ}
        assert result[fixture.vfolder_ids[2]] == {OperationType.READ}

    # ── Tests: multi-domain ──

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.READ)],
                id="domain-read",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_domain_chain_multi_project_with_foreign_vfolder(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        multi_project_two_domains: None,
        permission_setup: None,
    ) -> None:
        """Domain permission grants vfolders in child projects but not in another domain."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        assert result[fixture.vfolder_ids[0]] == {OperationType.READ}
        assert result[fixture.vfolder_ids[1]] == {OperationType.READ}
        assert result[fixture.vfolder_ids[2]] == set()

    # ── Tests: inactive role ──

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                id="project-read",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_inactive_role_returns_empty_sets(
        self,
        db_source: PermissionDBSource,
        user_with_inactive_role: EffectiveFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """Inactive role does not grant any operations."""
        fixture = user_with_inactive_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result[vfolder_id] == set()

    # ── Tests: user isolation ──

    async def test_other_user_permissions_not_leaked(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        all_vfolders_in_project_auto: None,
    ) -> None:
        """Permissions for another user do not leak into target user's results."""
        fixture = user_with_active_role
        other_user_id = uuid.uuid4()
        other_role_id = uuid.uuid4()
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=other_user_id,
                    email="other@test.com",
                    resource_policy="test-rbac-policy",
                    status=UserStatus.ACTIVE,
                    need_password_change=False,
                    sudo_session_enabled=False,
                )
            )
            await db_sess.flush()
            db_sess.add(RoleRow(id=other_role_id, name="other-role"))
            await db_sess.flush()
            db_sess.add(UserRoleRow(user_id=other_user_id, role_id=other_role_id))
            db_sess.add(
                PermissionRow(
                    role_id=other_role_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture.project_id,
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.READ,
                    permission=Permission.READ,
                )
            )
            await db_sess.flush()

        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result[vfolder_id] == set()

    # ── Tests: multi-role union ──

    async def test_multiple_roles_union_operations(
        self,
        db_source: PermissionDBSource,
        user_with_two_roles: EffectiveFixture,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        all_vfolders_in_project_auto: None,
    ) -> None:
        """Operations from multiple roles are unioned together."""
        fixture = user_with_two_roles
        async with db_with_rbac_tables.begin_session() as db_sess:
            # role_a grants READ at project scope
            db_sess.add(
                PermissionRow(
                    role_id=fixture.role_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture.project_id,
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.READ,
                    permission=Permission.READ,
                )
            )
            # role_b grants UPDATE at project scope
            db_sess.add(
                PermissionRow(
                    role_id=fixture.role_b_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture.project_id,
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.UPDATE,
                    permission=Permission.UPDATE,
                )
            )
            await db_sess.flush()

        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        expected = {OperationType.READ, OperationType.UPDATE}
        for vfolder_id in fixture.vfolder_ids:
            assert result[vfolder_id] == expected

    # ── Tests: cycle detection ──

    @pytest.fixture
    async def scope_chain_with_cycle(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: EffectiveFixture,
    ) -> None:
        """Create a cycle: vfolders -> project -> domain -> project (back-edge)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            for vfolder_id in fixture_ids.vfolder_ids:
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.PROJECT,
                        scope_id=fixture_ids.project_id,
                        entity_type=EntityType.VFOLDER,
                        entity_id=vfolder_id,
                        relation_type=RelationType.AUTO,
                    )
                )
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=fixture_ids.domain_id,
                    entity_type=EntityType.PROJECT,
                    entity_id=fixture_ids.project_id,
                    relation_type=RelationType.AUTO,
                )
            )
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture_ids.project_id,
                    entity_type=EntityType.DOMAIN,
                    entity_id=fixture_ids.domain_id,
                    relation_type=RelationType.AUTO,
                )
            )
            await db_sess.flush()

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.READ)],
                id="domain-read",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_scope_chain_cycle_terminates_with_permission(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        scope_chain_with_cycle: None,
        permission_setup: None,
    ) -> None:
        """Cyclic scope chain terminates without infinite recursion; permission is found."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert OperationType.READ in result[vfolder_id]

    async def test_scope_chain_cycle_terminates_without_permission(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: EffectiveFixture,
        scope_chain_with_cycle: None,
    ) -> None:
        """Cyclic scope chain terminates without infinite recursion; no operations granted."""
        fixture = user_with_active_role
        result = self._ops_by_entity_id(
            await db_source.resolve_effective_permissions(self._make_keys(fixture)),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result[vfolder_id] == set()
