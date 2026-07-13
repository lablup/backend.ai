"""
Tests for PermissionDBSource virtual-scope-chain permission checks.

Covers resolution through the ``entity -> virtual_scope -> scope`` chain with
per-hop ``permission_cap`` clipping, parallel to the direct scope-walk check.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.entity.types import EntityRef, EntityType, ScopeType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType as PermEntityType,
)
from ai.backend.manager.data.permission.types import (
    OperationType,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as PermScopeType,
)
from ai.backend.manager.data.permission.virtual_scope import VirtualScopePermissionCheckKey
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
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ScalingGroupForDomainRow,
)

_TARGET_ENTITY_TYPE = EntityType("vfolder")


@dataclass
class VSChainFixture:
    """Identifiers for a virtual-scope chain test."""

    user_id: UserID = field(default_factory=lambda: UserID(uuid.uuid4()))
    role_id: uuid.UUID = field(default_factory=uuid.uuid4)
    virtual_scope_id: VirtualScopeID = field(default_factory=lambda: VirtualScopeID(uuid.uuid4()))
    owner_scope_id: uuid.UUID = field(default_factory=uuid.uuid4)
    bound_scope_id: uuid.UUID = field(default_factory=uuid.uuid4)
    entity_id: EntityID = field(default_factory=uuid.uuid4)


@dataclass
class VSChainSpec:
    """Declarative description of the virtual-scope chain to materialize."""

    granted: Permission
    scope_cap: Permission | None = None
    entity_cap: Permission | None = None
    attach_membership: bool = True
    role_status: RoleStatus = RoleStatus.ACTIVE


class TestCheckPermissionViaVirtualScope:
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
                VirtualScopeRow,
                ScopeBindingRow,
                EntityMembershipRow,
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
    def fixture_ids(self) -> VSChainFixture:
        return VSChainFixture()

    async def _create_user_and_role(
        self,
        db: ExtendedAsyncSAEngine,
        ids: VSChainFixture,
        role_status: RoleStatus,
    ) -> None:
        async with db.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name="test-rbac-policy",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            db_sess.add(policy)
            user = UserRow(
                uuid=ids.user_id,
                email="testuser@test.com",
                resource_policy="test-rbac-policy",
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
            )
            db_sess.add(user)
            await db_sess.flush()

            role = RoleRow(id=ids.role_id, name="test-role", status=role_status)
            db_sess.add(role)
            await db_sess.flush()

            db_sess.add(UserRoleRow(user_id=ids.user_id, role_id=ids.role_id))
            await db_sess.flush()

    async def _build_chain(
        self,
        db: ExtendedAsyncSAEngine,
        ids: VSChainFixture,
        spec: VSChainSpec,
    ) -> None:
        """Materialize: virtual scope, scope binding, entity membership, and a
        permission granting ``spec.granted`` at the bound scope."""
        async with db.begin_session() as db_sess:
            db_sess.add(
                VirtualScopeRow(
                    id=ids.virtual_scope_id,
                    scope_type=ScopeType("project"),
                    scope_id=ids.owner_scope_id,
                )
            )
            await db_sess.flush()

            db_sess.add(
                ScopeBindingRow(
                    virtual_scope_id=ids.virtual_scope_id,
                    scope_type=ScopeType("project"),
                    scope_id=ids.bound_scope_id,
                    permission_cap=spec.scope_cap,
                )
            )
            if spec.attach_membership:
                db_sess.add(
                    EntityMembershipRow(
                        virtual_scope_id=ids.virtual_scope_id,
                        entity_type=_TARGET_ENTITY_TYPE,
                        entity_id=ids.entity_id,
                        permission_cap=spec.entity_cap,
                    )
                )
            db_sess.add(
                PermissionRow(
                    role_id=ids.role_id,
                    scope_type=PermScopeType.PROJECT,
                    scope_id=str(ids.bound_scope_id),
                    entity_type=PermEntityType.VFOLDER,
                    operation=OperationType.READ,
                    permission=spec.granted,
                )
            )
            await db_sess.flush()

    @pytest.fixture
    async def chain(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: VSChainFixture,
        request: pytest.FixtureRequest,
    ) -> VSChainFixture:
        spec: VSChainSpec = request.param
        await self._create_user_and_role(db_with_rbac_tables, fixture_ids, spec.role_status)
        await self._build_chain(db_with_rbac_tables, fixture_ids, spec)
        return fixture_ids

    @pytest.mark.parametrize(
        ("chain", "permission", "expected"),
        [
            pytest.param(
                VSChainSpec(granted=Permission.READ),
                Permission.READ,
                True,
                id="permitted",
            ),
            pytest.param(
                VSChainSpec(granted=Permission.READ),
                Permission.UPDATE,
                False,
                id="denied-operation-mismatch",
            ),
            pytest.param(
                VSChainSpec(granted=Permission.READ | Permission.UPDATE | Permission.CREATE),
                Permission.CREATE,
                True,
                id="multi-level-chain-flows-through",
            ),
            pytest.param(
                VSChainSpec(
                    granted=Permission.READ | Permission.UPDATE,
                    scope_cap=Permission.READ,
                ),
                Permission.UPDATE,
                False,
                id="clip-at-scope-to-vs-hop",
            ),
            pytest.param(
                VSChainSpec(
                    granted=Permission.READ | Permission.UPDATE,
                    scope_cap=Permission.READ,
                ),
                Permission.READ,
                True,
                id="scope-cap-keeps-read",
            ),
            pytest.param(
                VSChainSpec(
                    granted=Permission.READ | Permission.UPDATE,
                    entity_cap=Permission.READ,
                ),
                Permission.UPDATE,
                False,
                id="clip-at-vs-to-entity-hop",
            ),
            pytest.param(
                VSChainSpec(
                    granted=Permission.READ | Permission.UPDATE,
                    entity_cap=Permission.READ,
                ),
                Permission.READ,
                True,
                id="entity-cap-keeps-read",
            ),
            pytest.param(
                VSChainSpec(granted=Permission.READ | Permission.UPDATE),
                Permission.UPDATE,
                True,
                id="null-cap-no-clip",
            ),
            pytest.param(
                VSChainSpec(granted=Permission.READ, attach_membership=False),
                Permission.READ,
                False,
                id="no-vs-fallback",
            ),
            pytest.param(
                VSChainSpec(granted=Permission.READ, role_status=RoleStatus.INACTIVE),
                Permission.READ,
                False,
                id="inactive-role-denied",
            ),
        ],
        indirect=["chain"],
    )
    async def test_check_permission(
        self,
        db_source: PermissionDBSource,
        chain: VSChainFixture,
        permission: Permission,
        expected: bool,
    ) -> None:
        result = await db_source.check_permission_via_virtual_scope(
            user_id=chain.user_id,
            entity=EntityRef(entity_type=_TARGET_ENTITY_TYPE, entity_id=chain.entity_id),
            permission=permission,
        )
        assert result is expected

    @pytest.mark.parametrize(
        ("chain", "expected"),
        [
            pytest.param(
                VSChainSpec(granted=Permission.READ | Permission.UPDATE),
                Permission.READ | Permission.UPDATE,
                id="both-caps-null",
            ),
            pytest.param(
                VSChainSpec(
                    granted=Permission.full(),
                    scope_cap=Permission.READ | Permission.UPDATE,
                    entity_cap=Permission.READ,
                ),
                Permission.READ,
                id="clipped-by-both-hops",
            ),
        ],
        indirect=["chain"],
    )
    async def test_resolve_effective_permission_bitmask(
        self,
        db_source: PermissionDBSource,
        chain: VSChainFixture,
        expected: Permission,
    ) -> None:
        key = VirtualScopePermissionCheckKey(
            user_id=chain.user_id,
            entity=EntityRef(entity_type=_TARGET_ENTITY_TYPE, entity_id=chain.entity_id),
        )
        resolved = await db_source.resolve_effective_permissions_via_virtual_scope([key])
        assert resolved[key] == expected

    @pytest.mark.parametrize(
        ("chain",),
        [pytest.param(VSChainSpec(granted=Permission.READ), id="bulk")],
        indirect=["chain"],
    )
    async def test_bulk_check_maps_each_key(
        self,
        db_source: PermissionDBSource,
        chain: VSChainFixture,
    ) -> None:
        reachable = VirtualScopePermissionCheckKey(
            user_id=chain.user_id,
            entity=EntityRef(entity_type=_TARGET_ENTITY_TYPE, entity_id=chain.entity_id),
        )
        unreachable = VirtualScopePermissionCheckKey(
            user_id=chain.user_id,
            entity=EntityRef(entity_type=_TARGET_ENTITY_TYPE, entity_id=uuid.uuid4()),
        )
        result = await db_source.check_bulk_permission_via_virtual_scope(
            [reachable, unreachable], Permission.READ
        )
        assert result == {reachable: True, unreachable: False}

    @pytest.mark.parametrize(
        ("chain",),
        [pytest.param(VSChainSpec(granted=Permission.READ), id="isolation")],
        indirect=["chain"],
    )
    async def test_other_user_is_isolated(
        self,
        db_source: PermissionDBSource,
        chain: VSChainFixture,
    ) -> None:
        result = await db_source.check_permission_via_virtual_scope(
            user_id=UserID(uuid.uuid4()),
            entity=EntityRef(entity_type=_TARGET_ENTITY_TYPE, entity_id=chain.entity_id),
            permission=Permission.READ,
        )
        assert result is False
