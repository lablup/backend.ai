"""
Tests for PermissionDBSource.check_bulk_permission_with_scope_chain().
Covers bulk CTE-based scope chain traversal with per-entity results.
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
from ai.backend.manager.data.permission.role import (
    BulkPermissionCheckInput,
    PermissionResolutionKey,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    Permission,
    ScopeType,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
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
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ScalingGroupForDomainRow,
)


@dataclass
class PermissionEntry:
    """A single permission to create in permission_setup fixture."""

    scope_key: str
    operation: OperationType
    entity_type: EntityType = EntityType.VFOLDER


@dataclass
class BatchFixture:
    """Pre-built fixture data for batch scope chain tests."""

    user_id: uuid.UUID
    role_id: uuid.UUID
    domain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vfolder_ids: list[str] = field(default_factory=list)
    # Extra IDs for multi-project / multi-domain tests
    domain_b_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_b_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_c_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.vfolder_ids:
            self.vfolder_ids = [str(uuid.uuid4()) for _ in range(3)]


class TestCheckBulkPermissionWithScopeChain:
    """Tests for batched CTE-based scope chain permission traversal."""

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
    def fixture_ids(self) -> BatchFixture:
        return BatchFixture(
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
        )

    # ── User + role fixtures ──

    @pytest.fixture
    async def user_with_active_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: BatchFixture,
    ) -> BatchFixture:
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
                description="Test role for batch scope chain",
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
        fixture_ids: BatchFixture,
    ) -> BatchFixture:
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

    # ── Association fixtures ──

    @pytest.fixture
    async def all_vfolders_in_project_auto(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: BatchFixture,
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
        fixture_ids: BatchFixture,
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
        fixture_ids: BatchFixture,
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
        fixture_ids: BatchFixture,
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
        fixture_ids: BatchFixture,
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

    # ── Other user fixture ──

    @pytest.fixture
    async def other_user_with_project_permission(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: BatchFixture,
    ) -> None:
        """Another user with READ permission on the same project."""
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
                    scope_id=fixture_ids.project_id,
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.READ,
                    permission=Permission.READ,
                )
            )
            await db_sess.flush()

    # ── Helpers ──

    @staticmethod
    def _make_input(
        fixture: BatchFixture,
        operation: OperationType,
    ) -> BulkPermissionCheckInput:
        keys = [
            PermissionResolutionKey(
                user_id=fixture.user_id,
                element_type=RBACElementType.VFOLDER,
                entity_id=vfolder_id,
                subject_entity_type=RBACElementType.VFOLDER,
            )
            for vfolder_id in fixture.vfolder_ids
        ]
        return BulkPermissionCheckInput(keys=keys, operation=operation)

    @staticmethod
    def _bool_by_entity_id(
        result: Mapping[PermissionResolutionKey, bool],
    ) -> dict[str, bool]:
        return {key.entity_id: value for key, value in result.items()}

    # ── Tests ──

    async def test_empty_input_returns_empty(
        self,
        db_source: PermissionDBSource,
    ) -> None:
        """Empty key sequence returns empty mapping."""
        result = await db_source.check_bulk_permission_with_scope_chain(
            BulkPermissionCheckInput(keys=[], operation=OperationType.READ)
        )
        assert result == {}

    @pytest.mark.parametrize(
        "permission_setup",
        [pytest.param([PermissionEntry("project", OperationType.READ)], id="project-read")],
        indirect=["permission_setup"],
    )
    async def test_all_granted_via_project_scope(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """All vfolders in same project with READ permission -> all True."""
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(user_with_active_role, OperationType.READ),
            ),
        )
        assert all(result.values())
        assert len(result) == 3

    @pytest.mark.parametrize(
        "permission_setup",
        [pytest.param([PermissionEntry("domain", OperationType.UPDATE)], id="domain-update")],
        indirect=["permission_setup"],
    )
    async def test_all_granted_via_domain_chain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        all_vfolders_in_project_auto: None,
        project_in_domain_auto: None,
        permission_setup: None,
    ) -> None:
        """Permission at DOMAIN scope propagates through chain to all vfolders."""
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(user_with_active_role, OperationType.UPDATE),
            ),
        )
        assert all(result.values())
        assert len(result) == 3

    async def test_no_permission_all_denied(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        all_vfolders_in_project_auto: None,
    ) -> None:
        """No permissions -> all False."""
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(user_with_active_role, OperationType.READ),
            ),
        )
        assert not any(result.values())
        assert len(result) == 3

    @pytest.mark.parametrize(
        "permission_setup",
        [pytest.param([PermissionEntry("project", OperationType.READ)], id="project-read")],
        indirect=["permission_setup"],
    )
    async def test_mixed_edges_partial_grant(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        mixed_vfolder_edges: None,
        permission_setup: None,
    ) -> None:
        """AUTO edge -> granted, REF edge -> denied, no edge -> denied."""
        fixture = user_with_active_role
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(fixture, OperationType.READ),
            ),
        )
        assert result[fixture.vfolder_ids[0]]  # AUTO
        assert not result[fixture.vfolder_ids[1]]  # REF
        assert not result[fixture.vfolder_ids[2]]  # no association

    @pytest.mark.parametrize(
        "permission_setup",
        [pytest.param([PermissionEntry("vfolder_0", OperationType.READ)], id="self-scope-v0")],
        indirect=["permission_setup"],
    )
    async def test_self_scope_grants_individually(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        permission_setup: None,
    ) -> None:
        """Self-scope permission on vfolder[0] only; others denied."""
        fixture = user_with_active_role
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(fixture, OperationType.READ),
            ),
        )
        assert result[fixture.vfolder_ids[0]]
        assert not result[fixture.vfolder_ids[1]]
        assert not result[fixture.vfolder_ids[2]]

    @pytest.mark.parametrize(
        "permission_setup",
        [pytest.param([PermissionEntry("project", OperationType.READ)], id="read-perm")],
        indirect=["permission_setup"],
    )
    async def test_operation_mismatch_all_denied(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """READ permission does not satisfy UPDATE check."""
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(user_with_active_role, OperationType.UPDATE),
            ),
        )
        assert not any(result.values())

    @pytest.mark.parametrize(
        "permission_setup",
        [pytest.param([PermissionEntry("project", OperationType.READ)], id="project-read")],
        indirect=["permission_setup"],
    )
    async def test_inactive_role_all_denied(
        self,
        db_source: PermissionDBSource,
        user_with_inactive_role: BatchFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """Inactive role does not grant any permission in batch."""
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(user_with_inactive_role, OperationType.READ),
            ),
        )
        assert not any(result.values())

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [
                    PermissionEntry("project", OperationType.READ),
                    PermissionEntry("vfolder_1", OperationType.READ),
                ],
                id="chain-plus-self-scope",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_self_scope_and_chain_combined(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        mixed_vfolder_edges: None,
        permission_setup: None,
    ) -> None:
        """vfolder[0] via chain (AUTO), vfolder[1] via self-scope, vfolder[2] denied."""
        fixture = user_with_active_role
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(fixture, OperationType.READ),
            ),
        )
        assert result[fixture.vfolder_ids[0]]  # via chain
        assert result[fixture.vfolder_ids[1]]  # via self-scope
        assert not result[fixture.vfolder_ids[2]]  # no path

    @pytest.mark.parametrize(
        "permission_setup",
        [pytest.param([PermissionEntry("domain", OperationType.READ)], id="domain-read")],
        indirect=["permission_setup"],
    )
    async def test_domain_chain_multi_project_with_foreign_vfolder(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        multi_project_two_domains: None,
        permission_setup: None,
    ) -> None:
        """Domain permission grants vfolders in child projects but not in another domain."""
        fixture = user_with_active_role
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(fixture, OperationType.READ),
            ),
        )
        assert result[fixture.vfolder_ids[0]]  # domain_a -> project_a -> vfolder[0]
        assert result[fixture.vfolder_ids[1]]  # domain_a -> project_b -> vfolder[1]
        assert not result[fixture.vfolder_ids[2]]  # domain_b -> project_c -> vfolder[2]

    async def test_other_user_not_affected(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        all_vfolders_in_project_auto: None,
        other_user_with_project_permission: None,
    ) -> None:
        """Permission for another user does not leak into batch results."""
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(user_with_active_role, OperationType.READ),
            ),
        )
        assert not any(result.values())

    # ── Cycle detection ──

    @pytest.fixture
    async def scope_chain_with_cycle(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: BatchFixture,
    ) -> None:
        """Create a cycle: vfolders -> project -> domain -> project (back-edge)."""
        async with db_with_rbac_tables.begin_session() as db_sess:
            # vfolders -> project (AUTO)
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
            # project -> domain (AUTO)
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=fixture_ids.domain_id,
                    entity_type=EntityType.PROJECT,
                    entity_id=fixture_ids.project_id,
                    relation_type=RelationType.AUTO,
                )
            )
            # domain -> project (AUTO, creates cycle)
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
        [pytest.param([PermissionEntry("domain", OperationType.READ)], id="domain-read")],
        indirect=["permission_setup"],
    )
    async def test_scope_chain_cycle_terminates_with_permission(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        scope_chain_with_cycle: None,
        permission_setup: None,
    ) -> None:
        """Cyclic scope chain terminates without infinite recursion; permission is found."""
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(user_with_active_role, OperationType.READ),
            ),
        )
        assert all(result.values())

    async def test_scope_chain_cycle_terminates_without_permission(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: BatchFixture,
        scope_chain_with_cycle: None,
    ) -> None:
        """Cyclic scope chain terminates without infinite recursion; no permission granted."""
        result = self._bool_by_entity_id(
            await db_source.check_bulk_permission_with_scope_chain(
                self._make_input(user_with_active_role, OperationType.READ),
            ),
        )
        assert not any(result.values())
