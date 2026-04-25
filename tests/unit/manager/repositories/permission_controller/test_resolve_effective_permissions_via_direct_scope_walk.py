"""
Tests for PermissionDBSource.resolve_effective_permissions_via_direct_scope_walk()
and the shared fan-in dedup path that also backs
PermissionDBSource.check_bulk_permission_with_scope_chain().

The shared path walks parent scopes once per unique direct parent scope
rather than once per input entity. These tests verify:
  * Output parity with the legacy ``resolve_effective_permissions`` across
    the BA-5797 scenarios (project / domain chains, self-scope, mixed
    edges, multi-domain, inactive role, multi-role union, cycle).
  * Fan-in correctness when many entities share a single direct parent.
  * Bulk-permission equivalence: the refactored
    ``check_bulk_permission_with_scope_chain`` returns the same boolean
    map as the legacy implementation for representative cases (granted /
    not-granted, scope-chain match, self-scope match, mixed).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest

from ai.backend.common.data.permission.types import (
    RBACElementType,
    RelationType,
)
from ai.backend.manager.data.permission.role import (
    BulkPermissionCheckInput,
    EffectivePermissionsInput,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.data.user.types import UserStatus
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
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables


@dataclass
class PermissionEntry:
    """A single permission to create in permission_setup fixture."""

    scope_key: str
    operation: OperationType
    entity_type: EntityType = EntityType.VFOLDER


@dataclass
class SharedPathFixture:
    """Pre-built fixture data for shared-path tests."""

    user_id: uuid.UUID
    role_id: uuid.UUID
    domain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vfolder_ids: list[str] = field(default_factory=list)
    # Extra IDs for multi-project / multi-domain tests
    domain_b_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_b_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_c_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role_b_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self) -> None:
        if not self.vfolder_ids:
            self.vfolder_ids = [str(uuid.uuid4()) for _ in range(3)]


def _normalize_permissions(
    perms: object,
    entity_ids: list[str],
) -> dict[str, set[OperationType]]:
    """Snap a permissions mapping into a plain dict keyed by every input entity id.

    The legacy resolver returns a defaultdict whose missing keys silently
    materialize empty sets, while the shared path returns a plain dict
    that omits ungranted entities. Compare them on common ground by
    explicitly filling in empty sets for ids that are not present.
    """
    assert isinstance(perms, dict)
    return {eid: set(perms.get(eid, set())) for eid in entity_ids}


class _SharedFixtures:
    """Fixtures reused by both the effective-permissions and bulk parity tests."""

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
    def fixture_ids(self) -> SharedPathFixture:
        return SharedPathFixture(
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
        )

    @pytest.fixture
    async def user_with_active_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: SharedPathFixture,
    ) -> SharedPathFixture:
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name="test-rbac-policy",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=0,
                    max_customized_image_count=0,
                )
            )
            db_sess.add(
                UserRow(
                    uuid=fixture_ids.user_id,
                    email="testuser@test.com",
                    resource_policy="test-rbac-policy",
                    status=UserStatus.ACTIVE,
                    need_password_change=False,
                    sudo_session_enabled=False,
                )
            )
            await db_sess.flush()

            db_sess.add(RoleRow(id=fixture_ids.role_id, name="test-role"))
            await db_sess.flush()

            db_sess.add(UserRoleRow(user_id=fixture_ids.user_id, role_id=fixture_ids.role_id))
            await db_sess.flush()
        return fixture_ids

    @pytest.fixture
    async def user_with_inactive_role(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: SharedPathFixture,
    ) -> SharedPathFixture:
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name="test-rbac-policy",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=0,
                    max_customized_image_count=0,
                )
            )
            db_sess.add(
                UserRow(
                    uuid=fixture_ids.user_id,
                    email="testuser@test.com",
                    resource_policy="test-rbac-policy",
                    status=UserStatus.ACTIVE,
                    need_password_change=False,
                    sudo_session_enabled=False,
                )
            )
            await db_sess.flush()

            db_sess.add(
                RoleRow(
                    id=fixture_ids.role_id,
                    name="inactive-role",
                    status=RoleStatus.INACTIVE,
                )
            )
            await db_sess.flush()

            db_sess.add(UserRoleRow(user_id=fixture_ids.user_id, role_id=fixture_ids.role_id))
            await db_sess.flush()
        return fixture_ids

    @pytest.fixture
    async def user_with_two_roles(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: SharedPathFixture,
    ) -> SharedPathFixture:
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name="test-rbac-policy",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=0,
                    max_customized_image_count=0,
                )
            )
            db_sess.add(
                UserRow(
                    uuid=fixture_ids.user_id,
                    email="testuser@test.com",
                    resource_policy="test-rbac-policy",
                    status=UserStatus.ACTIVE,
                    need_password_change=False,
                    sudo_session_enabled=False,
                )
            )
            await db_sess.flush()

            db_sess.add(RoleRow(id=fixture_ids.role_id, name="role-a"))
            db_sess.add(RoleRow(id=fixture_ids.role_b_id, name="role-b"))
            await db_sess.flush()

            db_sess.add(UserRoleRow(user_id=fixture_ids.user_id, role_id=fixture_ids.role_id))
            db_sess.add(UserRoleRow(user_id=fixture_ids.user_id, role_id=fixture_ids.role_b_id))
            await db_sess.flush()
        return fixture_ids

    @pytest.fixture
    async def all_vfolders_in_project_auto(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: SharedPathFixture,
    ) -> None:
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
        fixture_ids: SharedPathFixture,
    ) -> None:
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
        fixture_ids: SharedPathFixture,
    ) -> None:
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
        fixture_ids: SharedPathFixture,
    ) -> None:
        f = fixture_ids
        async with db_with_rbac_tables.begin_session() as db_sess:
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

    @pytest.fixture
    async def scope_chain_with_cycle(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: SharedPathFixture,
    ) -> None:
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

    @pytest.fixture
    async def permission_setup(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: SharedPathFixture,
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
                    )
                )
                await db_sess.flush()


def _make_effective_input(
    fixture: SharedPathFixture,
    entity_type: EntityType = EntityType.VFOLDER,
) -> EffectivePermissionsInput:
    return EffectivePermissionsInput(
        user_id=fixture.user_id,
        target_element_type=RBACElementType.VFOLDER,
        target_entity_ids=fixture.vfolder_ids,
        permission_entity_type=entity_type,
    )


def _make_bulk_input(
    fixture: SharedPathFixture,
    operation: OperationType,
) -> BulkPermissionCheckInput:
    return BulkPermissionCheckInput(
        user_id=fixture.user_id,
        target_element_type=RBACElementType.VFOLDER,
        target_entity_ids=fixture.vfolder_ids,
        operation=operation,
    )


class TestResolveEffectivePermissionsViaDirectScopeWalk(_SharedFixtures):
    """Effective-permissions resolver routed through the fan-in dedup path."""

    async def test_empty_input_returns_empty(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            EffectivePermissionsInput(
                user_id=fixture.user_id,
                target_element_type=RBACElementType.VFOLDER,
                target_entity_ids=[],
            )
        )
        assert result.permissions == {}

    async def test_no_permission_returns_empty_sets(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result.permissions[vfolder_id] == set()

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
        user_with_active_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result.permissions[vfolder_id] == {OperationType.READ}

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
        user_with_active_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        expected = {OperationType.READ, OperationType.UPDATE, OperationType.SOFT_DELETE}
        for vfolder_id in fixture.vfolder_ids:
            assert result.permissions[vfolder_id] == expected

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
        user_with_active_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        project_in_domain_auto: None,
        permission_setup: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result.permissions[vfolder_id] == {OperationType.UPDATE}

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
        user_with_active_role: SharedPathFixture,
        permission_setup: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        assert result.permissions[fixture.vfolder_ids[0]] == {OperationType.READ}
        assert result.permissions[fixture.vfolder_ids[1]] == set()
        assert result.permissions[fixture.vfolder_ids[2]] == set()

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                id="project-read-mixed-edges",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_mixed_edges_only_auto_gets_operations(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        mixed_vfolder_edges: None,
        permission_setup: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        assert result.permissions[fixture.vfolder_ids[0]] == {OperationType.READ}
        assert result.permissions[fixture.vfolder_ids[1]] == set()
        assert result.permissions[fixture.vfolder_ids[2]] == set()

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
        user_with_active_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        assert result.permissions[fixture.vfolder_ids[0]] == {
            OperationType.READ,
            OperationType.UPDATE,
        }
        assert result.permissions[fixture.vfolder_ids[1]] == {OperationType.READ}
        assert result.permissions[fixture.vfolder_ids[2]] == {OperationType.READ}

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.READ)],
                id="domain-read-multi",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_domain_chain_multi_project_with_foreign_vfolder(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        multi_project_two_domains: None,
        permission_setup: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        assert result.permissions[fixture.vfolder_ids[0]] == {OperationType.READ}
        assert result.permissions[fixture.vfolder_ids[1]] == {OperationType.READ}
        assert result.permissions[fixture.vfolder_ids[2]] == set()

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                id="project-read-inactive",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_inactive_role_returns_empty_sets(
        self,
        db_source: PermissionDBSource,
        user_with_inactive_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        fixture = user_with_inactive_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert result.permissions[vfolder_id] == set()

    async def test_multiple_roles_union_operations(
        self,
        db_source: PermissionDBSource,
        user_with_two_roles: SharedPathFixture,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        all_vfolders_in_project_auto: None,
    ) -> None:
        fixture = user_with_two_roles
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                PermissionRow(
                    role_id=fixture.role_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture.project_id,
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.READ,
                )
            )
            db_sess.add(
                PermissionRow(
                    role_id=fixture.role_b_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture.project_id,
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.UPDATE,
                )
            )
            await db_sess.flush()

        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        expected = {OperationType.READ, OperationType.UPDATE}
        for vfolder_id in fixture.vfolder_ids:
            assert result.permissions[vfolder_id] == expected

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.READ)],
                id="domain-read-cycle",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_scope_chain_cycle_terminates_with_permission(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        scope_chain_with_cycle: None,
        permission_setup: None,
    ) -> None:
        fixture = user_with_active_role
        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        for vfolder_id in fixture.vfolder_ids:
            assert OperationType.READ in result.permissions[vfolder_id]


class TestEffectivePermissionsParity(_SharedFixtures):
    """Output parity between the new and legacy effective-permissions resolvers."""

    async def _assert_parity(
        self,
        db_source: PermissionDBSource,
        fixture: SharedPathFixture,
    ) -> dict[str, set[OperationType]]:
        legacy = await db_source.resolve_effective_permissions(
            _make_effective_input(fixture),
        )
        new = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        legacy_norm = _normalize_permissions(legacy.permissions, fixture.vfolder_ids)
        new_norm = _normalize_permissions(new.permissions, fixture.vfolder_ids)
        assert legacy_norm == new_norm
        return new_norm

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
    async def test_parity_project_chain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        await self._assert_parity(db_source, user_with_active_role)

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
    async def test_parity_domain_chain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        project_in_domain_auto: None,
        permission_setup: None,
    ) -> None:
        await self._assert_parity(db_source, user_with_active_role)

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [
                    PermissionEntry("project", OperationType.READ),
                    PermissionEntry("vfolder_1", OperationType.UPDATE),
                ],
                id="chain-plus-self-mixed-edges",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_parity_chain_and_self_scope_mixed_edges(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        mixed_vfolder_edges: None,
        permission_setup: None,
    ) -> None:
        await self._assert_parity(db_source, user_with_active_role)

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.READ)],
                id="domain-read-multi",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_parity_multi_domain(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        multi_project_two_domains: None,
        permission_setup: None,
    ) -> None:
        await self._assert_parity(db_source, user_with_active_role)

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("vfolder_0", OperationType.READ)],
                id="self-scope-only",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_parity_self_scope_only(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        permission_setup: None,
    ) -> None:
        # No association edges at all — only the self-scope direct match
        # should grant the permission. Both paths must agree.
        await self._assert_parity(db_source, user_with_active_role)

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                id="inactive-role",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_parity_inactive_role(
        self,
        db_source: PermissionDBSource,
        user_with_inactive_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        await self._assert_parity(db_source, user_with_inactive_role)

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("domain", OperationType.READ)],
                id="cycle-with-perm",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_parity_cycle(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        scope_chain_with_cycle: None,
        permission_setup: None,
    ) -> None:
        await self._assert_parity(db_source, user_with_active_role)


class TestFanInDedup(_SharedFixtures):
    """High fan-in: many entities sharing a single direct parent scope."""

    @pytest.fixture
    async def many_vfolders_in_one_project(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: SharedPathFixture,
    ) -> SharedPathFixture:
        fixture_ids.vfolder_ids = [str(uuid.uuid4()) for _ in range(50)]
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
        return fixture_ids

    async def test_high_fan_in_effective_permissions(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        many_vfolders_in_one_project: SharedPathFixture,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """50 vfolders share one project; project-scope READ grants all of them."""
        fixture = user_with_active_role
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                PermissionRow(
                    role_id=fixture.role_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture.project_id,
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.READ,
                )
            )
            await db_sess.flush()

        result = await db_source.resolve_effective_permissions_via_direct_scope_walk(
            _make_effective_input(fixture),
        )
        assert len(fixture.vfolder_ids) == 50
        for vfolder_id in fixture.vfolder_ids:
            assert result.permissions[vfolder_id] == {OperationType.READ}

    async def test_high_fan_in_bulk_permission_check(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        many_vfolders_in_one_project: SharedPathFixture,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Bulk check on 50 vfolders sharing one project returns True for all."""
        fixture = user_with_active_role
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                PermissionRow(
                    role_id=fixture.role_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=fixture.project_id,
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.READ,
                )
            )
            await db_sess.flush()

        result = await db_source.check_bulk_permission_with_scope_chain(
            _make_bulk_input(fixture, OperationType.READ),
        )
        assert len(result) == 50
        assert all(result.values())


class TestBulkPermissionCheckSelfScopeViaSharedPath(_SharedFixtures):
    """Self-scope direct grants must still be honored after the refactor."""

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
    async def test_self_scope_only_grants_target_entity(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        permission_setup: None,
    ) -> None:
        """Self-scope permission on vfolder[0] only; others denied."""
        fixture = user_with_active_role
        result = await db_source.check_bulk_permission_with_scope_chain(
            _make_bulk_input(fixture, OperationType.READ),
        )
        assert result[fixture.vfolder_ids[0]]
        assert not result[fixture.vfolder_ids[1]]
        assert not result[fixture.vfolder_ids[2]]

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [
                    PermissionEntry("project", OperationType.READ),
                    PermissionEntry("vfolder_1", OperationType.READ),
                ],
                id="chain-plus-self",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_chain_and_self_scope_combined(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        mixed_vfolder_edges: None,
        permission_setup: None,
    ) -> None:
        """vfolder[0] via chain (AUTO), vfolder[1] via self-scope, vfolder[2] denied."""
        fixture = user_with_active_role
        result = await db_source.check_bulk_permission_with_scope_chain(
            _make_bulk_input(fixture, OperationType.READ),
        )
        assert result[fixture.vfolder_ids[0]]  # via chain
        assert result[fixture.vfolder_ids[1]]  # via self-scope
        assert not result[fixture.vfolder_ids[2]]

    @pytest.mark.parametrize(
        "permission_setup",
        [
            pytest.param(
                [PermissionEntry("project", OperationType.READ)],
                id="op-mismatch",
            )
        ],
        indirect=["permission_setup"],
    )
    async def test_operation_filter_excludes_other_operations(
        self,
        db_source: PermissionDBSource,
        user_with_active_role: SharedPathFixture,
        all_vfolders_in_project_auto: None,
        permission_setup: None,
    ) -> None:
        """READ permission does not satisfy an UPDATE bulk check."""
        fixture = user_with_active_role
        result = await db_source.check_bulk_permission_with_scope_chain(
            _make_bulk_input(fixture, OperationType.UPDATE),
        )
        assert not any(result.values())
