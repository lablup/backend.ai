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
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE, RolePresetID
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE, SessionID
from ai.backend.common.data.entity.types import EntityID, EntityType, ScopeRef, ScopeType
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.virtual_scope import VirtualScopeID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import ResourceSlot
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
from ai.backend.manager.data.permission.virtual_scope import EntityPermissionCheckKey
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    RBACOpsProvider,
    ScopeUserMember,
)
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ResourceGroupForDomainRow,
)

_TARGET_ENTITY_TYPE = EntityType("vfolder")
# Wired, but not a member of the legacy RBAC enum the permissions table used to carry.
_UNMAPPED_ENTITY_TYPE = ROLE_PRESET_ENTITY_TYPE


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
                EntityLabelRow,
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
            domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
            domain_id = DomainID(uuid.uuid4())
            db_sess.add(
                DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot())
            )
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
                username=f"user-{ids.user_id.hex[:8]}",
                email="testuser@test.com",
                resource_policy="test-rbac-policy",
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
                domain_name=domain_name,
                domain_id=domain_id,
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
            domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
            domain_id = DomainID(uuid.uuid4())
            db_sess.add(
                DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot())
            )
            db_sess.add(
                VirtualScopeRow(
                    id=ids.virtual_scope_id,
                    scope_type=ScopeType(EntityType("project")),
                    scope_id=ids.owner_scope_id,
                )
            )
            await db_sess.flush()

            db_sess.add(
                ScopeBindingRow(
                    virtual_scope_id=ids.virtual_scope_id,
                    scope_type=ScopeType(EntityType("project")),
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
            # A multi-bit requirement (UPSERT wants CREATE | UPDATE) is a subset
            # test: holding one of its bits must not pass.
            pytest.param(
                VSChainSpec(granted=Permission.READ | Permission.CREATE),
                Permission.CREATE | Permission.UPDATE,
                False,
                id="mask-denied-with-create-only",
            ),
            pytest.param(
                VSChainSpec(granted=Permission.READ | Permission.UPDATE),
                Permission.CREATE | Permission.UPDATE,
                False,
                id="mask-denied-with-update-only",
            ),
            pytest.param(
                VSChainSpec(granted=Permission.CREATE | Permission.UPDATE),
                Permission.CREATE | Permission.UPDATE,
                True,
                id="mask-permitted-with-both-bits",
            ),
            pytest.param(
                VSChainSpec(
                    granted=Permission.CREATE | Permission.UPDATE,
                    entity_cap=Permission.CREATE,
                ),
                Permission.CREATE | Permission.UPDATE,
                False,
                id="mask-denied-when-cap-clips-one-bit",
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
        key = EntityPermissionCheckKey(
            user_id=chain.user_id,
            entity=VFolderUUID(chain.entity_id),
        )
        result = await db_source.check_single_entity_permission_via_virtual_scope(key, permission)
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
        key = EntityPermissionCheckKey(
            user_id=chain.user_id,
            entity=VFolderUUID(chain.entity_id),
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
        reachable = EntityPermissionCheckKey(
            user_id=chain.user_id,
            entity=VFolderUUID(chain.entity_id),
        )
        unreachable = EntityPermissionCheckKey(
            user_id=chain.user_id,
            entity=VFolderUUID(uuid.uuid4()),
        )
        result = await db_source.check_bulk_permission_via_virtual_scope(
            [reachable, unreachable], Permission.READ
        )
        assert result == {reachable: True, unreachable: False}

    @pytest.mark.parametrize(
        ("chain",),
        [
            pytest.param(
                VSChainSpec(granted=Permission.CREATE),
                id="bulk-mask",
            )
        ],
        indirect=["chain"],
    )
    async def test_bulk_check_requires_every_bit_of_the_mask(
        self,
        db_source: PermissionDBSource,
        chain: VSChainFixture,
    ) -> None:
        reachable = EntityPermissionCheckKey(
            user_id=chain.user_id,
            entity=VFolderUUID(chain.entity_id),
        )
        result = await db_source.check_bulk_permission_via_virtual_scope(
            [reachable], Permission.CREATE | Permission.UPDATE
        )
        assert result == {reachable: False}

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
        key = EntityPermissionCheckKey(
            user_id=UserID(uuid.uuid4()),
            entity=VFolderUUID(chain.entity_id),
        )
        result = await db_source.check_single_entity_permission_via_virtual_scope(
            key, Permission.READ
        )
        assert result is False

    async def _build_unmapped_chain(
        self,
        db: ExtendedAsyncSAEngine,
        ids: VSChainFixture,
    ) -> None:
        """The chain of :meth:`_build_chain`, over an entity type the legacy enum
        does not name."""
        async with db.begin_session() as db_sess:
            db_sess.add(
                VirtualScopeRow(
                    id=ids.virtual_scope_id,
                    scope_type=ScopeType(EntityType("project")),
                    scope_id=ids.owner_scope_id,
                )
            )
            await db_sess.flush()
            db_sess.add(
                ScopeBindingRow(
                    virtual_scope_id=ids.virtual_scope_id,
                    scope_type=ScopeType(EntityType("project")),
                    scope_id=ids.bound_scope_id,
                )
            )
            db_sess.add(
                EntityMembershipRow(
                    virtual_scope_id=ids.virtual_scope_id,
                    entity_type=_UNMAPPED_ENTITY_TYPE,
                    entity_id=ids.entity_id,
                )
            )
            db_sess.add(
                PermissionRow(
                    role_id=ids.role_id,
                    scope_type=ScopeType(EntityType("project")),
                    scope_id=str(ids.bound_scope_id),
                    entity_type=_UNMAPPED_ENTITY_TYPE,
                    operation=OperationType.READ,
                    permission=Permission.READ,
                )
            )
            await db_sess.flush()

    async def test_grant_over_unmapped_entity_type_resolves(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        fixture_ids: VSChainFixture,
    ) -> None:
        """A grant whose entity type the legacy enum does not name is authored and
        resolves through the chain, instead of being unwritable and falling closed."""
        await self._create_user_and_role(db_with_rbac_tables, fixture_ids, RoleStatus.ACTIVE)
        await self._build_unmapped_chain(db_with_rbac_tables, fixture_ids)

        key = EntityPermissionCheckKey(
            user_id=fixture_ids.user_id,
            entity=RolePresetID(fixture_ids.entity_id),
        )
        resolved = await db_source.resolve_effective_permissions_via_virtual_scope([key])
        assert resolved[key] == Permission.READ

    async def test_stored_unmapped_entity_type_reads_back(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        fixture_ids: VSChainFixture,
    ) -> None:
        """A stored entity type the legacy enum does not name survives an ORM read."""
        await self._create_user_and_role(db_with_rbac_tables, fixture_ids, RoleStatus.ACTIVE)
        async with db_with_rbac_tables.begin_session() as db_sess:
            await db_sess.execute(
                sa.text(
                    "INSERT INTO permissions"
                    " (role_id, scope_type, scope_id, entity_type, operation, permission)"
                    " VALUES"
                    " (:role_id, :scope_type, :scope_id, :entity_type, :operation, :permission)"
                ),
                {
                    "role_id": fixture_ids.role_id,
                    "scope_type": str(ScopeType(EntityType("project"))),
                    "scope_id": str(fixture_ids.bound_scope_id),
                    "entity_type": str(_UNMAPPED_ENTITY_TYPE),
                    "operation": OperationType.READ.value,
                    "permission": int(Permission.READ),
                },
            )

        async with db_with_rbac_tables.begin_readonly_session() as db_sess:
            row = (await db_sess.scalars(sa.select(PermissionRow))).one()
        assert row.entity_type == _UNMAPPED_ENTITY_TYPE


class TestUserRosterEnrollment:
    """A user joining a project is enrolled in its roster only: the project's
    permissions do not cascade onto what the user owns, they reach an owned entity
    only through that entity's own enrollment, and they are clipped by the roster
    cap on the member user itself."""

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
    def ops_provider(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> RBACOpsProvider:
        return RBACOpsProvider(db_with_rbac_tables)

    @pytest.fixture
    def ids(self) -> VSChainFixture:
        return VSChainFixture()

    async def _grant_on_project(
        self,
        db: ExtendedAsyncSAEngine,
        ids: VSChainFixture,
        project_id: uuid.UUID,
        entity_type: PermEntityType = PermEntityType.VFOLDER,
        operation: OperationType = OperationType.READ,
        permission: Permission = Permission.READ,
    ) -> None:
        """Give the user a role holding ``permission`` over ``entity_type`` on the
        project scope."""
        async with db.begin_session() as db_sess:
            domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
            domain_id = DomainID(uuid.uuid4())
            db_sess.add(
                DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot())
            )
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
                    uuid=ids.user_id,
                    username=f"user-{ids.user_id.hex[:8]}",
                    email="member@test.com",
                    resource_policy="test-rbac-policy",
                    status=UserStatus.ACTIVE,
                    need_password_change=False,
                    sudo_session_enabled=False,
                    domain_name=domain_name,
                    domain_id=domain_id,
                )
            )
            await db_sess.flush()

            db_sess.add(RoleRow(id=ids.role_id, name="project-role", status=RoleStatus.ACTIVE))
            await db_sess.flush()
            db_sess.add(UserRoleRow(user_id=ids.user_id, role_id=ids.role_id))
            db_sess.add(
                PermissionRow(
                    role_id=ids.role_id,
                    scope_type=PermScopeType.PROJECT,
                    scope_id=str(project_id),
                    entity_type=entity_type,
                    operation=operation,
                    permission=permission,
                )
            )
            await db_sess.flush()

    async def _own_vfolder_in_user_vs(
        self,
        db: ExtendedAsyncSAEngine,
        ids: VSChainFixture,
    ) -> None:
        """Enroll the user's personal vfolder in the user's own virtual scope, as the
        virtual-scope backfill does for ordinary resource entities."""
        async with db.begin_session() as db_sess:
            user_vs_id = await db_sess.scalar(
                sa.select(VirtualScopeRow.id).where(
                    VirtualScopeRow.scope_type == USER_SCOPE_TYPE,
                    VirtualScopeRow.scope_id == ids.user_id,
                )
            )
            db_sess.add(
                EntityMembershipRow(
                    virtual_scope_id=user_vs_id,
                    entity_type=_TARGET_ENTITY_TYPE,
                    entity_id=ids.entity_id,
                    permission_cap=None,
                )
            )
            await db_sess.flush()

    async def _enroll_session_in_project_vs(
        self,
        db: ExtendedAsyncSAEngine,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> None:
        """Enroll a session in the project's virtual scope, as session creation does for
        the project the session runs in."""
        async with db.begin_session() as db_sess:
            project_vs_id = await db_sess.scalar(
                sa.select(VirtualScopeRow.id).where(
                    VirtualScopeRow.scope_type == PROJECT_SCOPE_TYPE,
                    VirtualScopeRow.scope_id == project_id,
                )
            )
            db_sess.add(
                EntityMembershipRow(
                    virtual_scope_id=project_vs_id,
                    entity_type=SESSION_ENTITY_TYPE,
                    entity_id=session_id,
                    permission_cap=None,
                )
            )
            await db_sess.flush()

    async def _enroll_user_in_project(
        self,
        ops_provider: RBACOpsProvider,
        project_scope: ScopeRef,
        user_scope: ScopeRef,
        user_id: UserID,
    ) -> None:
        async with ops_provider.write_ops() as w:
            await w.ensure_scope(project_scope)
            await w.ensure_scope(user_scope)
            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=project_scope, members=[ScopeUserMember(user_id=user_id)]
                )
            )

    async def test_project_grant_does_not_reach_what_the_member_owns(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        ops_provider: RBACOpsProvider,
        ids: VSChainFixture,
    ) -> None:
        """A project-scope grant must not resolve onto a vfolder enrolled only in the
        member user's own virtual scope: no row binds that scope into the project."""
        project_scope = ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ids.owner_scope_id)
        user_scope = ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=ids.user_id)
        await self._grant_on_project(db_with_rbac_tables, ids, ids.owner_scope_id)

        await self._enroll_user_in_project(ops_provider, project_scope, user_scope, ids.user_id)
        await self._own_vfolder_in_user_vs(db_with_rbac_tables, ids)

        key = EntityPermissionCheckKey(
            user_id=ids.user_id,
            entity=VFolderUUID(ids.entity_id),
        )
        result = await db_source.check_single_entity_permission_via_virtual_scope(
            key, Permission.READ
        )
        assert result is False

    async def test_project_grant_reaches_an_entity_enrolled_in_the_project(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        ops_provider: RBACOpsProvider,
        ids: VSChainFixture,
    ) -> None:
        """The same grant does reach a session enrolled in the project's virtual scope,
        so the check above fails for the intended reason and not by accident."""
        project_scope = ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ids.owner_scope_id)
        user_scope = ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=ids.user_id)
        session_id = uuid.uuid4()
        await self._grant_on_project(
            db_with_rbac_tables,
            ids,
            ids.owner_scope_id,
            entity_type=PermEntityType.SESSION,
        )

        await self._enroll_user_in_project(ops_provider, project_scope, user_scope, ids.user_id)
        await self._enroll_session_in_project_vs(
            db_with_rbac_tables, ids.owner_scope_id, session_id
        )

        key = EntityPermissionCheckKey(
            user_id=ids.user_id,
            entity=SessionID(session_id),
        )
        result = await db_source.check_single_entity_permission_via_virtual_scope(
            key, Permission.READ
        )
        assert result is True

    async def test_roster_cap_clips_the_grant_over_the_member_user(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        ops_provider: RBACOpsProvider,
        ids: VSChainFixture,
    ) -> None:
        """A project role holding user UPDATE resolves to READ over the member user:
        the roster enrollment caps every project-to-user row to read."""
        project_scope = ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ids.owner_scope_id)
        user_scope = ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=ids.user_id)
        await self._grant_on_project(
            db_with_rbac_tables,
            ids,
            ids.owner_scope_id,
            entity_type=PermEntityType.USER,
            operation=OperationType.UPDATE,
            permission=Permission.READ | Permission.UPDATE,
        )

        await self._enroll_user_in_project(ops_provider, project_scope, user_scope, ids.user_id)

        key = EntityPermissionCheckKey(user_id=ids.user_id, entity=UserID(ids.user_id))
        resolved = await db_source.resolve_effective_permissions_via_virtual_scope([key])
        assert resolved[key] == Permission.READ
