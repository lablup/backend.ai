"""Tests for user-scope auto-sync on role assign/unassign."""

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
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
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
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables


class TestUserScopeSync:
    """Tests for auto-sync of user-scope entries on role assign/unassign."""

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

    @pytest.fixture
    async def second_project(
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
                    description="Second project",
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
    async def multi_scope_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_project: uuid.UUID,
        second_project: uuid.UUID,
    ) -> uuid.UUID:
        """A role bound to two different project scopes."""
        role_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(RoleRow(id=role_id, name=f"multi-role-{role_id.hex[:8]}"))
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(test_project),
                    entity_type=EntityType.ROLE,
                    entity_id=str(role_id),
                )
            )
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(second_project),
                    entity_type=EntityType.ROLE,
                    entity_id=str(role_id),
                )
            )
            await session.commit()
        return role_id

    @pytest.fixture
    async def role_without_scope(self, db_with_cleanup: ExtendedAsyncSAEngine) -> uuid.UUID:
        """A role with no scope binding."""
        role_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(RoleRow(id=role_id, name=f"no-scope-role-{role_id.hex[:8]}"))
            await session.commit()
        return role_id

    @pytest.fixture
    def perm_db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> PermissionDBSource:
        return PermissionDBSource(db=db_with_cleanup)

    async def _get_user_scope_entries(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
    ) -> list[tuple[ScopeType, str]]:
        async with db.begin_readonly_session() as session:
            rows = (
                await session.execute(
                    sa.select(
                        AssociationScopesEntitiesRow.scope_type,
                        AssociationScopesEntitiesRow.scope_id,
                    ).where(
                        AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                        AssociationScopesEntitiesRow.entity_id == str(user_id),
                    )
                )
            ).all()
        return [(r[0], r[1]) for r in rows]

    # --- assign sync ---

    async def test_assign_creates_user_scope_entry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        project_scoped_role: uuid.UUID,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """Assigning a project-scoped role creates a user-project scope entry."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=project_scoped_role)
        )

        entries = await self._get_user_scope_entries(db_with_cleanup, user_1)
        assert (ScopeType.PROJECT, str(test_project)) in entries

    async def test_assign_multi_scope_role_creates_all_entries(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        multi_scope_role: uuid.UUID,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
        second_project: uuid.UUID,
    ) -> None:
        """Assigning a role bound to multiple scopes creates entries for all scopes."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=multi_scope_role)
        )

        entries = await self._get_user_scope_entries(db_with_cleanup, user_1)
        assert (ScopeType.PROJECT, str(test_project)) in entries
        assert (ScopeType.PROJECT, str(second_project)) in entries

    async def test_assign_role_without_scope_creates_no_entry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_without_scope: uuid.UUID,
        user_1: uuid.UUID,
    ) -> None:
        """Assigning a role with no scope binding creates no user-scope entries."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_without_scope)
        )

        entries = await self._get_user_scope_entries(db_with_cleanup, user_1)
        assert entries == []

    async def test_assign_duplicate_scope_is_idempotent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        project_scoped_role: uuid.UUID,
        second_project_scoped_role: uuid.UUID,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """Assigning two roles to the same scope does not create duplicate user-scope entries."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=project_scoped_role)
        )
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=second_project_scoped_role)
        )

        entries = await self._get_user_scope_entries(db_with_cleanup, user_1)
        project_entries = [e for e in entries if e == (ScopeType.PROJECT, str(test_project))]
        assert len(project_entries) == 1

    # --- revoke sync ---

    async def test_revoke_only_role_removes_user_scope_entry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        project_scoped_role: uuid.UUID,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """Revoking the only role for a scope removes the user-scope entry."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=project_scoped_role)
        )
        await perm_db_source.revoke_role(
            UserRoleRevocationInput(user_id=user_1, role_id=project_scoped_role)
        )

        entries = await self._get_user_scope_entries(db_with_cleanup, user_1)
        assert (ScopeType.PROJECT, str(test_project)) not in entries

    async def test_revoke_one_of_two_roles_keeps_user_scope_entry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        project_scoped_role: uuid.UUID,
        second_project_scoped_role: uuid.UUID,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
    ) -> None:
        """Revoking one role when another covers the same scope keeps the entry."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=project_scoped_role)
        )
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=second_project_scoped_role)
        )
        await perm_db_source.revoke_role(
            UserRoleRevocationInput(user_id=user_1, role_id=project_scoped_role)
        )

        entries = await self._get_user_scope_entries(db_with_cleanup, user_1)
        assert (ScopeType.PROJECT, str(test_project)) in entries

    async def test_revoke_multi_scope_role_removes_uncovered_scopes_only(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        project_scoped_role: uuid.UUID,
        multi_scope_role: uuid.UUID,
        user_1: uuid.UUID,
        test_project: uuid.UUID,
        second_project: uuid.UUID,
    ) -> None:
        """Revoking a multi-scope role removes only scopes not covered by other roles.

        Setup: project_scoped_role covers test_project,
               multi_scope_role covers test_project + second_project.
        After revoking multi_scope_role, test_project should remain (covered by
        project_scoped_role), but second_project should be removed.
        """
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=project_scoped_role)
        )
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=multi_scope_role)
        )
        await perm_db_source.revoke_role(
            UserRoleRevocationInput(user_id=user_1, role_id=multi_scope_role)
        )

        entries = await self._get_user_scope_entries(db_with_cleanup, user_1)
        assert (ScopeType.PROJECT, str(test_project)) in entries
        assert (ScopeType.PROJECT, str(second_project)) not in entries

    async def test_revoke_role_without_scope_does_nothing(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_without_scope: uuid.UUID,
        user_1: uuid.UUID,
    ) -> None:
        """Revoking a role with no scope binding does not affect user-scope entries."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_without_scope)
        )
        await perm_db_source.revoke_role(
            UserRoleRevocationInput(user_id=user_1, role_id=role_without_scope)
        )

        entries = await self._get_user_scope_entries(db_with_cleanup, user_1)
        assert entries == []
