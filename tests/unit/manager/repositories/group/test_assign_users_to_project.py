"""Tests for ProjectDBSource.assign_users_to_project()"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.types import EntityType, ScopeType
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
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.project.db_source import ProjectDBSource
from ai.backend.manager.repositories.project.scope_binders import UserProjectEntityUnbinder
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


class TestAssignUsersToProject:
    """Tests for ProjectDBSource.assign_users_to_project"""

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
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(
                RoleRow(
                    id=role_id,
                    name=f"test-role-{role_id.hex[:8]}",
                )
            )
            await session.commit()
        return role_id

    @pytest.fixture
    def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectDBSource:
        return ProjectDBSource(db=db_with_cleanup, v2_ops_provider=V2DBOpsProvider(db_with_cleanup))

    # --- Test cases ---

    async def test_assign_users_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
        same_domain_user_2: UserID,
    ) -> None:
        """Active users in same domain are assigned successfully."""
        result = await group_db_source.assign_users_to_project(
            test_project, [same_domain_user_1, same_domain_user_2], test_role
        )

        assert len(result) == 2
        result_uuids = {u.uuid for u in result}
        assert result_uuids == {same_domain_user_1, same_domain_user_2}

        # Verify ASE rows created (PROJECT scope, USER entity)
        async with db_with_cleanup.begin_readonly_session() as session:
            assoc_result = await session.execute(
                sa.select(AssociationScopesEntitiesRow.entity_id).where(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(test_project),
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                )
            )
            assert len(assoc_result.fetchall()) == 2

    async def test_assign_empty_list_returns_empty(
        self,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
    ) -> None:
        """Empty user_ids list returns empty result without DB access."""
        result = await group_db_source.assign_users_to_project(test_project, [], test_role)
        assert result == []

    async def test_assign_filters_already_assigned_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
        same_domain_user_2: UserID,
    ) -> None:
        """Already-assigned users are excluded; only new users are returned."""
        # Pre-assign user_1
        await group_db_source.assign_users_to_project(test_project, [same_domain_user_1], test_role)

        # Assign both — only user_2 should be returned
        result = await group_db_source.assign_users_to_project(
            test_project, [same_domain_user_1, same_domain_user_2], test_role
        )

        assert len(result) == 1
        assert result[0].uuid == same_domain_user_2

        # Verify total 2 ASE associations
        async with db_with_cleanup.begin_readonly_session() as session:
            assoc_result = await session.execute(
                sa.select(AssociationScopesEntitiesRow.entity_id).where(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(test_project),
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                )
            )
            assert len(assoc_result.fetchall()) == 2

    async def test_assign_filters_cross_domain_users(
        self,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
        cross_domain_user: UserID,
    ) -> None:
        """Users from a different domain are silently excluded."""
        result = await group_db_source.assign_users_to_project(
            test_project, [same_domain_user_1, cross_domain_user], test_role
        )

        assert len(result) == 1
        assert result[0].uuid == same_domain_user_1

    async def test_assign_filters_nonexistent_users(
        self,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
    ) -> None:
        """Non-existent user UUIDs are silently excluded."""
        fake_user = UserID(uuid.uuid4())
        result = await group_db_source.assign_users_to_project(test_project, [fake_user], test_role)
        assert result == []

    async def test_assign_all_invalid_returns_empty(
        self,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
        cross_domain_user: UserID,
    ) -> None:
        """When all users are invalid (wrong domain, nonexistent), return empty."""
        fake_user = UserID(uuid.uuid4())

        result = await group_db_source.assign_users_to_project(
            test_project, [cross_domain_user, fake_user], test_role
        )
        assert result == []

    async def test_assign_creates_user_role_rows(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
        same_domain_user_2: UserID,
    ) -> None:
        """Assign creates UserRoleRow records for each user with the given role."""
        await group_db_source.assign_users_to_project(
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

    async def test_assign_creates_scope_entity_rows(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
    ) -> None:
        """Assign creates AssociationScopesEntitiesRow binding users to project scope."""
        await group_db_source.assign_users_to_project(test_project, [same_domain_user_1], test_role)

        async with db_with_cleanup.begin_readonly_session() as session:
            rows = (
                await session.scalars(
                    sa.select(AssociationScopesEntitiesRow).where(
                        AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                        AssociationScopesEntitiesRow.scope_id == str(test_project),
                        AssociationScopesEntitiesRow.entity_id == str(same_domain_user_1),
                    )
                )
            ).all()
            assert len(rows) == 1

    async def test_assign_does_not_bind_project_into_user_scope(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: ProjectDBSource,
        test_project: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
    ) -> None:
        """Assigned users become members of the project's virtual entity, and the project
        is not bound into theirs — project-scoped permissions must not reach the entities
        a member owns."""
        await group_db_source.assign_users_to_project(test_project, [same_domain_user_1], test_role)

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

    async def test_assign_users_to_personal_project_refused(
        self,
        group_db_source: ProjectDBSource,
        personal_project: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
    ) -> None:
        """A personal project keeps its owner as its only member."""
        with pytest.raises(PersonalProjectMemberAdditionError):
            await group_db_source.assign_users_to_project(
                personal_project, [same_domain_user_1], test_role
            )

    async def test_bind_user_to_personal_project_refused(
        self,
        group_db_source: ProjectDBSource,
        personal_project: ProjectID,
        same_domain_user_1: UserID,
    ) -> None:
        """The membership-only write is refused for a personal project too."""
        with pytest.raises(PersonalProjectMemberAdditionError):
            await group_db_source.bind_user_to_project(same_domain_user_1, personal_project)

    async def test_update_members_add_to_personal_project_refused(
        self,
        group_db_source: ProjectDBSource,
        personal_project: ProjectID,
        same_domain_user_1: UserID,
    ) -> None:
        """The legacy add path is refused for a personal project."""
        with pytest.raises(PersonalProjectMemberAdditionError):
            await group_db_source.update_members(personal_project, "add", [same_domain_user_1])


class TestUnassignUsersFromProject:
    """Tests for ProjectDBSource.unassign_users_from_project"""

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
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(
                RoleRow(
                    id=role_id,
                    name=f"test-role-{role_id.hex[:8]}",
                )
            )
            await session.commit()
        return role_id

    @pytest.fixture
    async def project_with_role_registered(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_project: ProjectID,
        test_role: uuid.UUID,
    ) -> ProjectID:
        """Register the test role in the project scope via association_scopes_entities."""
        async with db_with_cleanup.begin_session() as session:
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(test_project),
                    entity_type=EntityType.ROLE,
                    entity_id=str(test_role),
                )
            )
            await session.commit()
        return test_project

    @pytest.fixture
    def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectDBSource:
        return ProjectDBSource(db=db_with_cleanup, v2_ops_provider=V2DBOpsProvider(db_with_cleanup))

    # --- Test cases ---

    async def test_unassign_returns_unassigned_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: ProjectDBSource,
        project_with_role_registered: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
    ) -> None:
        """Unassign reports the users it removed from the project scope."""
        project_id = project_with_role_registered
        await group_db_source.assign_users_to_project(project_id, [same_domain_user_1], test_role)

        result = await group_db_source.unassign_users_from_project(
            UserProjectEntityUnbinder(user_uuids=[same_domain_user_1], project_id=project_id)
        )
        assert len(result.unassigned_users) == 1
        assert result.unassigned_users[0].uuid == same_domain_user_1

    async def test_unassign_deletes_scope_entity_rows(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: ProjectDBSource,
        project_with_role_registered: ProjectID,
        test_role: uuid.UUID,
        same_domain_user_1: UserID,
    ) -> None:
        """Unassign removes user's AssociationScopesEntitiesRow for the project scope."""
        project_id = project_with_role_registered
        await group_db_source.assign_users_to_project(project_id, [same_domain_user_1], test_role)

        await group_db_source.unassign_users_from_project(
            UserProjectEntityUnbinder(user_uuids=[same_domain_user_1], project_id=project_id)
        )

        async with db_with_cleanup.begin_readonly_session() as session:
            user_scope_rows = (
                await session.scalars(
                    sa.select(AssociationScopesEntitiesRow).where(
                        AssociationScopesEntitiesRow.scope_id == str(project_id),
                        AssociationScopesEntitiesRow.entity_id == str(same_domain_user_1),
                    )
                )
            ).all()
            assert len(user_scope_rows) == 0

    async def test_unassign_nonexistent_user_reports_failure(
        self,
        group_db_source: ProjectDBSource,
        project_with_role_registered: ProjectID,
    ) -> None:
        """Non-existent user UUID is reported as failure."""
        fake_user = UserID(uuid.uuid4())
        result = await group_db_source.unassign_users_from_project(
            UserProjectEntityUnbinder(
                user_uuids=[fake_user], project_id=project_with_role_registered
            )
        )
        assert len(result.unassigned_users) == 0
        assert len(result.failures) == 1
        assert result.failures[0].user_id == fake_user
