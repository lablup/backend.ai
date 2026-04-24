"""Tests for association_groups_users sync on role assign/revoke.

Covers the 3-table invariant (user_roles, association_scopes_entities,
association_groups_users) for:
- bulk_revoke_role
- accept_invitation for project-scoped roles
- single assign and bulk_assign_role (repository-level sync).

Single-user revoke_role is exercised at the service layer via
unbind_user_from_project and is not covered here.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.action.rbac_role_invitation import (
    AcceptRoleInvitationAction,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.permission.role import (
    BulkUserRoleRevocationInput,
    UserRoleAssignmentInput,
)
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.role_invitation.types import RoleInvitationState
from ai.backend.manager.models.agent import AgentRow
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
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.permission_controller.creators import UserRoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables


class TestAssociationGroupsUsersSync:
    """Tests for association_groups_users sync across RBAC role surfaces."""

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
                RoleInvitationRow,
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

    async def _add_project(self, db: ExtendedAsyncSAEngine, domain_name: str) -> uuid.UUID:
        project_id = uuid.uuid4()
        policy_name = f"proj-pol-{uuid.uuid4().hex[:8]}"
        async with db.begin_session() as session:
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
                    domain_name=domain_name,
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
    async def project_a(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_domain: str
    ) -> uuid.UUID:
        return await self._add_project(db_with_cleanup, test_domain)

    @pytest.fixture
    async def project_b(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_domain: str
    ) -> uuid.UUID:
        return await self._add_project(db_with_cleanup, test_domain)

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
    async def user_2(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> uuid.UUID:
        return await self._create_user(
            db_with_cleanup, test_domain, user_resource_policy, test_password_info
        )

    async def _create_project_scoped_role(
        self, db: ExtendedAsyncSAEngine, project_id: uuid.UUID
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db.begin_session() as session:
            session.add(RoleRow(id=role_id, name=f"proj-role-{role_id.hex[:8]}"))
            session.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(project_id),
                    entity_type=EntityType.ROLE,
                    entity_id=str(role_id),
                )
            )
            await session.commit()
        return role_id

    @pytest.fixture
    async def role_in_project_a(
        self, db_with_cleanup: ExtendedAsyncSAEngine, project_a: uuid.UUID
    ) -> uuid.UUID:
        return await self._create_project_scoped_role(db_with_cleanup, project_a)

    @pytest.fixture
    async def second_role_in_project_a(
        self, db_with_cleanup: ExtendedAsyncSAEngine, project_a: uuid.UUID
    ) -> uuid.UUID:
        return await self._create_project_scoped_role(db_with_cleanup, project_a)

    @pytest.fixture
    async def role_in_project_b(
        self, db_with_cleanup: ExtendedAsyncSAEngine, project_b: uuid.UUID
    ) -> uuid.UUID:
        return await self._create_project_scoped_role(db_with_cleanup, project_b)

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

    async def _project_membership_ids(
        self, db: ExtendedAsyncSAEngine, user_id: uuid.UUID
    ) -> set[uuid.UUID]:
        async with db.begin_readonly_session() as session:
            rows = (
                await session.execute(
                    sa.select(AssocGroupUserRow.group_id).where(
                        AssocGroupUserRow.user_id == user_id,
                    )
                )
            ).all()
        return {r[0] for r in rows}

    async def _user_scope_ids(self, db: ExtendedAsyncSAEngine, user_id: uuid.UUID) -> set[str]:
        async with db.begin_readonly_session() as session:
            rows = (
                await session.execute(
                    sa.select(AssociationScopesEntitiesRow.scope_id).where(
                        AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                        AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                        AssociationScopesEntitiesRow.entity_id == str(user_id),
                    )
                )
            ).all()
        return {r[0] for r in rows}

    # --- _assign_role_in_session membership sync (covers accept_invitation) ---

    async def test_assign_project_role_creates_membership_row(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        user_1: uuid.UUID,
        project_a: uuid.UUID,
    ) -> None:
        """Assigning a project-scoped role inserts association_groups_users row."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_in_project_a)
        )

        memberships = await self._project_membership_ids(db_with_cleanup, user_1)
        assert project_a in memberships

    async def test_assign_global_role_does_not_touch_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        global_role: uuid.UUID,
        user_1: uuid.UUID,
    ) -> None:
        """Assigning a non-project-scoped role creates no membership row."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=global_role)
        )

        memberships = await self._project_membership_ids(db_with_cleanup, user_1)
        assert memberships == set()

    async def test_assign_is_idempotent_with_preexisting_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        user_1: uuid.UUID,
        project_a: uuid.UUID,
    ) -> None:
        """If an association_groups_users row already exists, assign does not duplicate it."""
        async with db_with_cleanup.begin_session() as session:
            session.add(AssocGroupUserRow(user_id=user_1, group_id=project_a))
            await session.commit()

        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_in_project_a)
        )

        async with db_with_cleanup.begin_readonly_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(AssocGroupUserRow)
                .where(
                    AssocGroupUserRow.user_id == user_1,
                    AssocGroupUserRow.group_id == project_a,
                )
            )
        assert count == 1

    # --- bulk_assign_role membership sync ---

    async def test_bulk_assign_project_role_creates_membership_rows(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        user_1: uuid.UUID,
        user_2: uuid.UUID,
        project_a: uuid.UUID,
    ) -> None:
        """bulk_assign_role populates association_groups_users from role scope.

        Covers the case where the caller does not pass ``project_id`` through
        the service layer for a project-scoped role — the repository-level
        sync must still keep the business-membership table consistent.
        """
        bulk_creator = BulkCreator(
            specs=[
                UserRoleCreatorSpec(user_id=user_1, role_id=role_in_project_a),
                UserRoleCreatorSpec(user_id=user_2, role_id=role_in_project_a),
            ]
        )

        await perm_db_source.bulk_assign_role(bulk_creator)

        assert project_a in await self._project_membership_ids(db_with_cleanup, user_1)
        assert project_a in await self._project_membership_ids(db_with_cleanup, user_2)

    # --- accept_invitation (BA-5810 primary regression) ---

    async def test_accept_invitation_for_project_role_populates_all_three_tables(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        user_1: uuid.UUID,
        user_2: uuid.UUID,
        project_a: uuid.UUID,
    ) -> None:
        """Accepting a project member role invitation maintains the 3-table invariant.

        After accept: user_roles, association_scopes_entities(PROJECT, USER, AUTO),
        and association_groups_users must all contain the corresponding rows.
        """
        invitation_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            session.add(
                RoleInvitationRow(
                    id=invitation_id,
                    inviter_user_id=user_1,
                    invitee_user_id=user_2,
                    role_id=role_in_project_a,
                    state=RoleInvitationState.PENDING,
                )
            )
            await session.commit()

        await perm_db_source.accept_invitation(
            AcceptRoleInvitationAction(invitation_id=invitation_id)
        )

        # 1. user_roles row exists.
        async with db_with_cleanup.begin_readonly_session() as session:
            user_role = await session.scalar(
                sa.select(UserRoleRow).where(
                    UserRoleRow.user_id == user_2,
                    UserRoleRow.role_id == role_in_project_a,
                )
            )
        assert user_role is not None

        # 2. association_scopes_entities (PROJECT, USER) row exists for the invitee.
        user_scopes = await self._user_scope_ids(db_with_cleanup, user_2)
        assert str(project_a) in user_scopes

        # 3. association_groups_users row exists for the invitee.
        memberships = await self._project_membership_ids(db_with_cleanup, user_2)
        assert project_a in memberships

    # --- bulk_revoke_role (BA-5810 primary regression) ---

    async def test_bulk_revoke_last_project_role_removes_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        user_1: uuid.UUID,
        project_a: uuid.UUID,
    ) -> None:
        """Bulk-revoking the user's last project-scoped role removes the membership row."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_in_project_a)
        )
        assert project_a in await self._project_membership_ids(db_with_cleanup, user_1)

        result = await perm_db_source.bulk_revoke_role(
            BulkUserRoleRevocationInput(
                role_id=role_in_project_a,
                user_ids=[user_1],
            )
        )

        assert len(result.successes) == 1
        assert len(result.failures) == 0
        memberships = await self._project_membership_ids(db_with_cleanup, user_1)
        assert project_a not in memberships

    async def test_bulk_revoke_one_of_two_project_roles_keeps_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        second_role_in_project_a: uuid.UUID,
        user_1: uuid.UUID,
        project_a: uuid.UUID,
    ) -> None:
        """Bulk-revoking one role when another covers the same project keeps the membership."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_in_project_a)
        )
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=second_role_in_project_a)
        )

        await perm_db_source.bulk_revoke_role(
            BulkUserRoleRevocationInput(
                role_id=role_in_project_a,
                user_ids=[user_1],
            )
        )

        memberships = await self._project_membership_ids(db_with_cleanup, user_1)
        assert project_a in memberships

    async def test_bulk_revoke_removes_only_uncovered_projects(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        role_in_project_b: uuid.UUID,
        user_1: uuid.UUID,
        project_a: uuid.UUID,
        project_b: uuid.UUID,
    ) -> None:
        """Revoking a role in project_a keeps membership for project_b."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_in_project_a)
        )
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_in_project_b)
        )

        await perm_db_source.bulk_revoke_role(
            BulkUserRoleRevocationInput(
                role_id=role_in_project_a,
                user_ids=[user_1],
            )
        )

        memberships = await self._project_membership_ids(db_with_cleanup, user_1)
        assert project_a not in memberships
        assert project_b in memberships

    async def test_bulk_revoke_across_multiple_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        user_1: uuid.UUID,
        user_2: uuid.UUID,
        project_a: uuid.UUID,
    ) -> None:
        """Bulk revoke processes memberships independently per user."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_in_project_a)
        )
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_2, role_id=role_in_project_a)
        )

        await perm_db_source.bulk_revoke_role(
            BulkUserRoleRevocationInput(
                role_id=role_in_project_a,
                user_ids=[user_1, user_2],
            )
        )

        assert project_a not in await self._project_membership_ids(db_with_cleanup, user_1)
        assert project_a not in await self._project_membership_ids(db_with_cleanup, user_2)

    async def test_bulk_revoke_global_role_does_not_touch_memberships(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
        role_in_project_a: uuid.UUID,
        global_role: uuid.UUID,
        user_1: uuid.UUID,
        project_a: uuid.UUID,
    ) -> None:
        """Revoking a non-project-scoped role must not remove project memberships."""
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=role_in_project_a)
        )
        await perm_db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_1, role_id=global_role)
        )

        await perm_db_source.bulk_revoke_role(
            BulkUserRoleRevocationInput(role_id=global_role, user_ids=[user_1])
        )

        memberships = await self._project_membership_ids(db_with_cleanup, user_1)
        assert project_a in memberships
