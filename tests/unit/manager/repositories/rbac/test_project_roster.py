"""Tests for the project roster ops: who is enrolled and what enrolling grants."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import ScopeType
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.resource import PersonalProjectMemberAdditionError
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


def _node(entity_id: uuid.UUID, scope_type: ScopeType) -> sa.ScalarSelect[Any]:
    """The virtual entity node the id stands for."""
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == scope_type.value,
            VirtualEntityRow.entity_id == entity_id,
        )
        .scalar_subquery()
    )


class TestEnrollUsersInProject:
    """Tests for RbacRosterRepository.join_members"""

    @pytest.fixture
    def test_password_info(self) -> PasswordInfo:
        return PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                AssociationScopesEntitiesRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
                VirtualEntityRow,
                ScopeBindingRow,
                EntityLabelRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                EntityMembershipFieldRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                    dotfiles=b"",
                    integration_id=None,
                )
            )
            await session.commit()
        return DomainFixtureData(domain_name=DomainName(domain_name), domain_id=domain_id)

    @pytest.fixture
    async def other_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"other-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="Other domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                    dotfiles=b"",
                    integration_id=None,
                )
            )
            await session.commit()
        return domain_name

    @pytest.fixture
    async def user_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await session.commit()
        return policy_name

    @pytest.fixture
    async def test_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
    ) -> ProjectID:
        project_id = ProjectID(uuid.uuid4())
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            session.add(
                ProjectRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    description="Test project",
                    is_active=True,
                    domain_name=test_domain.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=policy_name,
                    type=ProjectType.GENERAL,
                )
            )
            session.add(
                VirtualEntityRow(
                    entity_type=ScopeType.PROJECT.value,
                    entity_id=project_id,
                )
            )
            await session.commit()
        return project_id

    @pytest.fixture
    async def personal_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
    ) -> ProjectID:
        project_id = ProjectID(uuid.uuid4())
        policy_name = f"personal-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            session.add(
                ProjectRow(
                    id=project_id,
                    name=f"personal-project-{project_id.hex[:8]}",
                    description="Personal project",
                    is_active=True,
                    domain_name=test_domain.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=policy_name,
                    type=ProjectType.PERSONAL,
                )
            )
            session.add(
                VirtualEntityRow(
                    entity_type=ScopeType.PROJECT.value,
                    entity_id=project_id,
                )
            )
            await session.commit()
        return project_id

    async def _create_user(
        self,
        db: ExtendedAsyncSAEngine,
        domain_name: str,
        policy_name: str,
        password_info: PasswordInfo,
    ) -> UserID:
        user_uuid = UserID(uuid.uuid4())
        async with db.begin_session() as session:
            domain_id = (
                await session.execute(sa.select(DomainRow.id).where(DomainRow.name == domain_name))
            ).scalar_one()
            session.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"user-{user_uuid.hex[:8]}",
                    email=f"user-{user_uuid.hex[:8]}@example.com",
                    password=password_info,
                    need_password_change=False,
                    full_name="Test User",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=policy_name,
                    domain_id=domain_id,
                )
            )
            await VirtualEntitySeeder().seed_user_scope(session, user_uuid)
            await session.commit()
        return user_uuid

    @pytest.fixture
    async def same_domain_user_1(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> UserID:
        return await self._create_user(
            db_with_cleanup, test_domain.domain_name, user_resource_policy, test_password_info
        )

    @pytest.fixture
    async def same_domain_user_2(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> UserID:
        return await self._create_user(
            db_with_cleanup, test_domain.domain_name, user_resource_policy, test_password_info
        )

    @pytest.fixture
    async def cross_domain_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        other_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> UserID:
        return await self._create_user(
            db_with_cleanup, other_domain, user_resource_policy, test_password_info
        )

    @pytest.fixture
    async def test_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_project: ProjectID,
    ) -> RoleID:
        role_id = RoleID(uuid.uuid4())
        async with db_with_cleanup.begin_session() as session:
            session.add(
                RoleRow(
                    id=role_id,
                    name=f"test-role-{role_id.hex[:8]}",
                    scope_type=ScopeType.PROJECT.value,
                    scope_id=test_project,
                )
            )
            await session.commit()
        return role_id

    @pytest.fixture
    def roster_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> RbacRosterRepository:
        return RbacRosterRepository(RosterOpsProvider(db_with_cleanup))

    # --- Test cases ---

    async def test_enroll_users_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
        same_domain_user_2: UserID,
    ) -> None:
        """Active users in same domain are assigned successfully."""
        result = await roster_repository.join_members(
            test_project, [same_domain_user_1, same_domain_user_2], test_role
        )

        assert len(result) == 2
        result_uuids = {u.uuid for u in result}
        assert result_uuids == {same_domain_user_1, same_domain_user_2}

        # Verify the roster edges
        async with db_with_cleanup.begin_readonly_session() as session:
            members = (
                await session.scalars(
                    sa.select(EntityMembershipRow.member_entity_id).where(
                        EntityMembershipRow.virtual_entity_id
                        == _node(test_project, ScopeType.PROJECT),
                        EntityMembershipRow.capped.is_(True),
                    )
                )
            ).all()
            assert len(members) == 2

    async def test_enroll_empty_list_returns_empty(
        self,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
    ) -> None:
        """Empty user_ids list returns empty result without DB access."""
        result = await roster_repository.join_members(test_project, [], test_role)
        assert result == []

    async def test_enroll_filters_users_already_on_the_roster(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
        same_domain_user_2: UserID,
    ) -> None:
        """Already-assigned users are excluded; only new users are returned."""
        # Pre-assign user_1
        await roster_repository.join_members(test_project, [same_domain_user_1], test_role)

        # Assign both — only user_2 should be returned
        result = await roster_repository.join_members(
            test_project, [same_domain_user_1, same_domain_user_2], test_role
        )

        assert len(result) == 1
        assert result[0].uuid == same_domain_user_2

        # Verify the roster edges
        async with db_with_cleanup.begin_readonly_session() as session:
            members = (
                await session.scalars(
                    sa.select(EntityMembershipRow.member_entity_id).where(
                        EntityMembershipRow.virtual_entity_id
                        == _node(test_project, ScopeType.PROJECT),
                        EntityMembershipRow.capped.is_(True),
                    )
                )
            ).all()
            assert len(members) == 2

    async def test_enroll_filters_cross_domain_users(
        self,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
        cross_domain_user: UserID,
    ) -> None:
        """Users from a different domain are silently excluded."""
        result = await roster_repository.join_members(
            test_project, [same_domain_user_1, cross_domain_user], test_role
        )

        assert len(result) == 1
        assert result[0].uuid == same_domain_user_1

    async def test_enroll_filters_nonexistent_users(
        self,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
    ) -> None:
        """Non-existent user UUIDs are silently excluded."""
        fake_user = UserID(uuid.uuid4())
        result = await roster_repository.join_members(test_project, [fake_user], test_role)
        assert result == []

    async def test_enroll_all_invalid_returns_empty(
        self,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        cross_domain_user: UserID,
    ) -> None:
        """When all users are invalid (wrong domain, nonexistent), return empty."""
        fake_user = UserID(uuid.uuid4())

        result = await roster_repository.join_members(
            test_project, [cross_domain_user, fake_user], test_role
        )
        assert result == []

    async def test_enroll_creates_user_role_rows(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
        same_domain_user_2: UserID,
    ) -> None:
        """Assign creates UserRoleRow records for each user with the given role."""
        await roster_repository.join_members(
            test_project, [same_domain_user_1, same_domain_user_2], test_role
        )

        async with db_with_cleanup.begin_readonly_session() as session:
            rows = (
                await session.scalars(
                    sa.select(UserRoleRow).where(UserRoleRow.role_id == test_role)
                )
            ).all()
            assert len(rows) == 2
            assert {r.user_id for r in rows} == {same_domain_user_1, same_domain_user_2}

    async def test_enroll_writes_a_read_capped_roster_edge(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
    ) -> None:
        """Enrolling puts the user on the project's list under a READ cap, and writes no
        legacy scope association."""
        await roster_repository.join_members(test_project, [same_domain_user_1], test_role)

        async with db_with_cleanup.begin_readonly_session() as session:
            membership_id = await session.scalar(
                sa.select(EntityMembershipRow.id).where(
                    EntityMembershipRow.virtual_entity_id == _node(test_project, ScopeType.PROJECT),
                    EntityMembershipRow.member_entity_id
                    == _node(same_domain_user_1, ScopeType.USER),
                    EntityMembershipRow.capped.is_(True),
                )
            )
            assert membership_id is not None
            caps = (
                await session.scalars(
                    sa.select(EntityMembershipCapRow.permission).where(
                        EntityMembershipCapRow.membership_id == membership_id
                    )
                )
            ).all()
            assert set(caps) == {Permission.READ}
            associations = (
                await session.scalars(
                    sa.select(AssociationScopesEntitiesRow).where(
                        AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                        AssociationScopesEntitiesRow.scope_id == str(test_project),
                        AssociationScopesEntitiesRow.entity_id == str(same_domain_user_1),
                    )
                )
            ).all()
            assert associations == []

    async def test_enroll_does_not_bind_project_into_user_scope(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
    ) -> None:
        """Assigned users become members of the project's virtual entity, and the project
        is not bound into theirs — project-scoped permissions must not reach the entities
        a member owns."""
        await roster_repository.join_members(test_project, [same_domain_user_1], test_role)

        async with db_with_cleanup.begin_readonly_session() as session:
            user_vs_id = await session.scalar(
                sa.select(VirtualEntityRow.id).where(
                    VirtualEntityRow.entity_type == ScopeType.USER.value,
                    VirtualEntityRow.entity_id == same_domain_user_1,
                )
            )
            project_vs_id = await session.scalar(
                sa.select(VirtualEntityRow.id).where(
                    VirtualEntityRow.entity_type == ScopeType.PROJECT.value,
                    VirtualEntityRow.entity_id == test_project,
                )
            )
            bindings_into_user_scope = (
                await session.scalars(
                    sa.select(ScopeBindingRow.scope_entity_id).where(
                        ScopeBindingRow.virtual_entity_id == user_vs_id,
                        ScopeBindingRow.scope_entity_id == project_vs_id,
                    )
                )
            ).all()
            memberships_in_project_scope = (
                await session.scalars(
                    sa.select(EntityMembershipRow.member_entity_id).where(
                        EntityMembershipRow.virtual_entity_id == project_vs_id,
                        EntityMembershipRow.member_entity_id == user_vs_id,
                    )
                )
            ).all()

        assert list(bindings_into_user_scope) == []
        assert list(memberships_in_project_scope) == [user_vs_id]

    async def test_enroll_users_in_personal_project_refused(
        self,
        roster_repository: RbacRosterRepository,
        personal_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
    ) -> None:
        """A personal project keeps its owner as its only member."""
        with pytest.raises(PersonalProjectMemberAdditionError):
            await roster_repository.join_members(personal_project, [same_domain_user_1], test_role)

    async def test_enroll_one_user_in_personal_project_refused(
        self,
        roster_repository: RbacRosterRepository,
        personal_project: ProjectID,
        same_domain_user_1: UserID,
    ) -> None:
        """The membership-only write is refused for a personal project too."""
        with pytest.raises(PersonalProjectMemberAdditionError):
            await roster_repository.join_member(personal_project, same_domain_user_1)


class TestWithdrawUsersFromProject:
    """Tests for RbacRosterRepository.leave_members"""

    @pytest.fixture
    def test_password_info(self) -> PasswordInfo:
        return PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                AssociationScopesEntitiesRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
                VirtualEntityRow,
                ScopeBindingRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                EntityMembershipFieldRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                    dotfiles=b"",
                    integration_id=None,
                )
            )
            await session.commit()
        return DomainFixtureData(domain_name=DomainName(domain_name), domain_id=domain_id)

    @pytest.fixture
    async def user_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            await session.commit()
        return policy_name

    @pytest.fixture
    async def test_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
    ) -> ProjectID:
        project_id = ProjectID(uuid.uuid4())
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            session.add(
                ProjectRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    description="Test project",
                    is_active=True,
                    domain_name=test_domain.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=policy_name,
                    type=ProjectType.GENERAL,
                )
            )
            session.add(
                VirtualEntityRow(
                    entity_type=ScopeType.PROJECT.value,
                    entity_id=project_id,
                )
            )
            await session.commit()
        return project_id

    async def _create_user(
        self,
        db: ExtendedAsyncSAEngine,
        domain_name: str,
        policy_name: str,
        password_info: PasswordInfo,
    ) -> UserID:
        user_uuid = UserID(uuid.uuid4())
        async with db.begin_session() as session:
            domain_id = (
                await session.execute(sa.select(DomainRow.id).where(DomainRow.name == domain_name))
            ).scalar_one()
            session.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"user-{user_uuid.hex[:8]}",
                    email=f"user-{user_uuid.hex[:8]}@example.com",
                    password=password_info,
                    need_password_change=False,
                    full_name="Test User",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=policy_name,
                    domain_id=domain_id,
                )
            )
            await VirtualEntitySeeder().seed_user_scope(session, user_uuid)
            await session.commit()
        return user_uuid

    @pytest.fixture
    async def same_domain_user_1(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> UserID:
        return await self._create_user(
            db_with_cleanup, test_domain.domain_name, user_resource_policy, test_password_info
        )

    @pytest.fixture
    async def same_domain_user_2(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> UserID:
        return await self._create_user(
            db_with_cleanup, test_domain.domain_name, user_resource_policy, test_password_info
        )

    @pytest.fixture
    async def test_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_project: ProjectID,
    ) -> RoleID:
        role_id = RoleID(uuid.uuid4())
        async with db_with_cleanup.begin_session() as session:
            session.add(
                RoleRow(
                    id=role_id,
                    name=f"test-role-{role_id.hex[:8]}",
                    scope_type=ScopeType.PROJECT.value,
                    scope_id=test_project,
                )
            )
            await session.commit()
        return role_id

    @pytest.fixture
    def roster_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> RbacRosterRepository:
        return RbacRosterRepository(RosterOpsProvider(db_with_cleanup))

    # --- Test cases ---

    async def test_withdraw_returns_withdrawn_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
    ) -> None:
        """Unassign reports the users it removed from the project scope."""
        project_id = test_project
        await roster_repository.join_members(project_id, [same_domain_user_1], test_role)

        result = await roster_repository.leave_members(project_id, [same_domain_user_1])
        assert len(result.members) == 1
        assert result.members[0].uuid == same_domain_user_1

    async def test_withdraw_removes_the_roster_edge(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
        test_role: RoleID,
        same_domain_user_1: UserID,
    ) -> None:
        """Withdrawing takes the user off the project's list."""
        project_id = test_project
        await roster_repository.join_members(project_id, [same_domain_user_1], test_role)

        await roster_repository.leave_members(project_id, [same_domain_user_1])

        async with db_with_cleanup.begin_readonly_session() as session:
            membership_id = await session.scalar(
                sa.select(EntityMembershipRow.id).where(
                    EntityMembershipRow.virtual_entity_id == _node(project_id, ScopeType.PROJECT),
                    EntityMembershipRow.member_entity_id
                    == _node(same_domain_user_1, ScopeType.USER),
                )
            )
            assert membership_id is None

    async def test_withdraw_nonexistent_user_reports_failure(
        self,
        roster_repository: RbacRosterRepository,
        test_project: ProjectID,
    ) -> None:
        """Non-existent user UUID is reported as failure."""
        fake_user = UserID(uuid.uuid4())
        result = await roster_repository.leave_members(test_project, [fake_user])
        assert len(result.members) == 0
        assert len(result.failures) == 1
        assert result.failures[0].user_id == fake_user
