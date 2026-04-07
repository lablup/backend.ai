"""Tests for role assignment/revocation with project remaining count in PermissionDBSource."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.permission.role import (
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow, association_groups_users
from ai.backend.manager.models.group.row import AssocGroupUserRow
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
                AssocGroupUserRow,
                AssociationScopesEntitiesRow,
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
        """bind_user_to_project creates business + RBAC associations."""
        await group_db_source.bind_user_to_project(user_1, test_project)

        async with db_with_cleanup.begin_readonly_session() as session:
            assoc = await session.execute(
                sa.select(association_groups_users).where(
                    association_groups_users.c.user_id == user_1,
                    association_groups_users.c.group_id == test_project,
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
                sa.select(association_groups_users).where(
                    association_groups_users.c.user_id == user_1,
                    association_groups_users.c.group_id == test_project,
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
        """unbind_user_from_project removes business + RBAC associations."""
        await group_db_source.bind_user_to_project(user_1, test_project)
        await group_db_source.unbind_user_from_project(user_1, test_project)

        async with db_with_cleanup.begin_readonly_session() as session:
            assoc = await session.execute(
                sa.select(association_groups_users).where(
                    association_groups_users.c.group_id == test_project,
                )
            )
            assert len(assoc.fetchall()) == 0
