"""Tests for role assignment/revocation with project remaining count in PermissionDBSource."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.role import (
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.group.db_source import GroupDBSource
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager
from ai.backend.testutils.db import with_tables


class TestRoleAssignment:
    """Tests for PermissionDBSource.revoke_role project remaining count
    and GroupDBSource.bind/unbind_user_to_project."""

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
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssociationScopesEntitiesRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
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
        return domain_name

    @pytest.fixture
    async def user_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
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
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_domain: str
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
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
                GroupRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    description="Test project",
                    is_active=True,
                    domain_name=test_domain,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=policy_name,
                    type=ProjectType.GENERAL,
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
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        async with db.begin_session() as session:
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
                )
            )
            await session.commit()
        return user_uuid

    @pytest.fixture
    async def user_1(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> uuid.UUID:
        return await self._create_user(
            db_with_cleanup, test_domain, user_resource_policy, test_password_info
        )

    @pytest.fixture
    async def project_scoped_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_project: uuid.UUID,
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(RoleRow(id=role_id, name=f"project-role-{role_id.hex[:8]}"))
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(test_project),
                    entity_type=EntityType.ROLE,
                    entity_id=str(role_id),
                )
            )
            await session.commit()
        return role_id

    @pytest.fixture
    async def second_project_scoped_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_project: uuid.UUID,
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(RoleRow(id=role_id, name=f"project-role2-{role_id.hex[:8]}"))
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(test_project),
                    entity_type=EntityType.ROLE,
                    entity_id=str(role_id),
                )
            )
            await session.commit()
        return role_id

    @pytest.fixture
    async def global_role(self, db_with_cleanup: ExtendedAsyncSAEngine) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(RoleRow(id=role_id, name=f"global-role-{role_id.hex[:8]}"))
            await session.commit()
        return role_id

    @pytest.fixture
    def perm_db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> PermissionDBSource:
        return PermissionDBSource(db=db_with_cleanup)

    @pytest.fixture
    def group_db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> GroupDBSource:
        return GroupDBSource(db=db_with_cleanup)

    # --- revoke_role remaining count ---

    async def test_revoke_project_scoped_role_returns_zero_remaining(
        self,
        perm_db_source: PermissionDBSource,
        project_scoped_role: uuid.UUID,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """Revoking the only project-scoped role returns remaining_count=0."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=project_scoped_role)
        )
        result = await perm_db_source.revoke_role(
            UserRoleRevocationInput(user_id=user_1, role_id=project_scoped_role)
        )

        assert len(result.project_remaining_roles) == 1
        assert result.project_remaining_roles[0].project_id == test_project
        assert result.project_remaining_roles[0].remaining_count == 0

    async def test_revoke_one_of_two_project_roles_returns_nonzero_remaining(
        self,
        perm_db_source: PermissionDBSource,
        project_scoped_role: uuid.UUID,
        second_project_scoped_role: uuid.UUID,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """Revoking one role when another exists returns remaining_count=1."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=project_scoped_role)
        )
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=second_project_scoped_role)
        )
        result = await perm_db_source.revoke_role(
            UserRoleRevocationInput(user_id=user_1, role_id=project_scoped_role)
        )

        assert len(result.project_remaining_roles) == 1
        assert result.project_remaining_roles[0].project_id == test_project
        assert result.project_remaining_roles[0].remaining_count == 1

    async def test_revoke_global_role_returns_empty_project_remaining(
        self,
        perm_db_source: PermissionDBSource,
        global_role: uuid.UUID,
        user_1: uuid.UUID,
    ) -> None:
        """Revoking a non-project-scoped role returns empty project_remaining."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=global_role)
        )
        result = await perm_db_source.revoke_role(
            UserRoleRevocationInput(user_id=user_1, role_id=global_role)
        )
        assert result.project_remaining_roles == []

    # --- GroupDBSource.bind/unbind_user_to_project ---

    async def test_bind_user_to_project_creates_associations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """bind_user_to_project creates the ASE row (PROJECT/USER)."""
        await group_db_source.bind_user_to_project(user_1, test_project)

        async with db_with_cleanup.begin_readonly_session() as session:
            assoc = await session.execute(
                sa.select(AssociationScopesEntitiesRow.entity_id).where(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(test_project),
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(user_1),
                )
            )
            assert len(assoc.fetchall()) == 1

    async def test_bind_user_to_project_skips_if_already_bound(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """Calling bind twice does not create duplicate rows."""
        await group_db_source.bind_user_to_project(user_1, test_project)
        await group_db_source.bind_user_to_project(user_1, test_project)

        async with db_with_cleanup.begin_readonly_session() as session:
            assoc = await session.execute(
                sa.select(AssociationScopesEntitiesRow.entity_id).where(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(test_project),
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(user_1),
                )
            )
            assert len(assoc.fetchall()) == 1

    async def test_unbind_user_from_project_removes_associations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """unbind_user_from_project removes the ASE row."""
        await group_db_source.bind_user_to_project(user_1, test_project)
        await group_db_source.unbind_user_from_project(user_1, test_project)

        async with db_with_cleanup.begin_readonly_session() as session:
            assoc = await session.execute(
                sa.select(AssociationScopesEntitiesRow.entity_id).where(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(test_project),
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                )
            )
            assert len(assoc.fetchall()) == 0

    # --- RoleManager.assign_auto_assign_roles ---

    @pytest.fixture
    def role_manager(self) -> RoleManager:
        return RoleManager()

    @pytest.fixture
    def project_scope(self, test_project: uuid.UUID) -> ScopeId:
        return ScopeId(scope_type=ScopeType.PROJECT, scope_id=str(test_project))

    async def _bind_auto_assign_role(
        self,
        db: ExtendedAsyncSAEngine,
        scope_id: ScopeId,
        *,
        auto_assign: bool = True,
        status: RoleStatus = RoleStatus.ACTIVE,
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db.begin_session() as session:
            session.add(
                RoleRow(
                    id=role_id,
                    name=f"auto-role-{role_id.hex[:8]}",
                    auto_assign=auto_assign,
                    status=status,
                )
            )
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=scope_id.scope_type,
                    scope_id=scope_id.scope_id,
                    entity_type=EntityType.ROLE,
                    entity_id=str(role_id),
                )
            )
            await session.commit()
        return role_id

    async def _user_ids_for_role(
        self, db: ExtendedAsyncSAEngine, role_id: uuid.UUID
    ) -> list[uuid.UUID]:
        async with db.begin_readonly_session() as session:
            return list(
                await session.scalars(
                    sa.select(UserRoleRow.user_id).where(UserRoleRow.role_id == role_id)
                )
            )

    @pytest.fixture
    async def joined_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> list[uuid.UUID]:
        return [
            await self._create_user(
                db_with_cleanup, test_domain, user_resource_policy, test_password_info
            )
            for _ in range(3)
        ]

    @pytest.fixture
    async def auto_assign_role(
        self, db_with_cleanup: ExtendedAsyncSAEngine, project_scope: ScopeId
    ) -> uuid.UUID:
        """An active, auto_assign role bound to the target scope."""
        return await self._bind_auto_assign_role(db_with_cleanup, project_scope)

    @pytest.fixture
    async def role_with_one_existing_member(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        auto_assign_role: uuid.UUID,
        joined_users: list[uuid.UUID],
    ) -> uuid.UUID:
        """The auto_assign role with its first joined user already mapped."""
        async with db_with_cleanup.begin_session() as session:
            session.add(UserRoleRow(user_id=joined_users[0], role_id=auto_assign_role))
            await session.commit()
        return auto_assign_role

    @pytest.fixture
    async def ineligible_roles(
        self, db_with_cleanup: ExtendedAsyncSAEngine, project_scope: ScopeId
    ) -> list[uuid.UUID]:
        """Roles that must NOT be granted: not auto_assign, inactive, or bound elsewhere."""
        not_auto_assign = await self._bind_auto_assign_role(
            db_with_cleanup, project_scope, auto_assign=False
        )
        inactive = await self._bind_auto_assign_role(
            db_with_cleanup, project_scope, status=RoleStatus.INACTIVE
        )
        other_scope = ScopeId(scope_type=ScopeType.PROJECT, scope_id=str(uuid.uuid4()))
        bound_to_other_scope = await self._bind_auto_assign_role(db_with_cleanup, other_scope)
        return [not_auto_assign, inactive, bound_to_other_scope]

    async def test_assign_auto_assign_roles_grants_to_all_users_when_none_mapped(
        self,
        role_manager: RoleManager,
        db_with_cleanup: ExtendedAsyncSAEngine,
        project_scope: ScopeId,
        auto_assign_role: uuid.UUID,
        joined_users: list[uuid.UUID],
    ) -> None:
        """Every joining user is mapped to an active auto_assign role bound to the scope."""
        async with db_with_cleanup.begin_session() as session:
            await role_manager.assign_auto_assign_roles(session, joined_users, project_scope)

        mapped_user_ids = await self._user_ids_for_role(db_with_cleanup, auto_assign_role)
        assert set(mapped_user_ids) == set(joined_users)

    async def test_assign_auto_assign_roles_skips_already_mapped_users(
        self,
        role_manager: RoleManager,
        db_with_cleanup: ExtendedAsyncSAEngine,
        project_scope: ScopeId,
        role_with_one_existing_member: uuid.UUID,
        joined_users: list[uuid.UUID],
    ) -> None:
        """A pre-mapped (user, role) pair is not re-inserted; only new users are added."""
        async with db_with_cleanup.begin_session() as session:
            await role_manager.assign_auto_assign_roles(session, joined_users, project_scope)

        mapped_user_ids = await self._user_ids_for_role(
            db_with_cleanup, role_with_one_existing_member
        )
        # Exactly one row per user: the pre-mapped user is neither duplicated nor dropped.
        assert sorted(mapped_user_ids) == sorted(joined_users)

    async def test_assign_auto_assign_roles_skips_non_eligible_roles(
        self,
        role_manager: RoleManager,
        db_with_cleanup: ExtendedAsyncSAEngine,
        project_scope: ScopeId,
        auto_assign_role: uuid.UUID,
        ineligible_roles: list[uuid.UUID],
        user_1: uuid.UUID,
    ) -> None:
        """Only active, auto_assign roles bound to the target scope are granted."""
        async with db_with_cleanup.begin_session() as session:
            await role_manager.assign_auto_assign_roles(session, [user_1], project_scope)

        async with db_with_cleanup.begin_readonly_session() as session:
            granted_role_ids = list(
                await session.scalars(
                    sa.select(UserRoleRow.role_id).where(UserRoleRow.user_id == user_1)
                )
            )
        # Only the eligible role is granted; none of the ineligible roles appear.
        assert granted_role_ids == [auto_assign_role]
