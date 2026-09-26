"""Tests for the predefined roles a user holds in a project scope."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm

# ORM cluster registration: these rows are reachable via relationships but are not
# otherwise imported by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.project import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.rbac import (
    PredefinedRole,
    ProjectScope,
    get_predefined_roles_in_scope,
)
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

_ORM_CLUSTER = (
    AgentRow,
    ResourceGroupForDomainRow,
)

_MEMBER_ROLES = [
    pytest.param(UserRole.SUPERADMIN, frozenset([PredefinedRole.OWNER]), id="superadmin"),
    pytest.param(
        UserRole.MONITOR,
        frozenset([PredefinedRole.ADMIN, PredefinedRole.PRIVILEGED_MEMBER]),
        id="monitor",
    ),
    pytest.param(UserRole.ADMIN, frozenset([PredefinedRole.OWNER]), id="admin"),
    pytest.param(UserRole.USER, frozenset([PredefinedRole.PRIVILEGED_MEMBER]), id="user"),
]

_NON_MEMBER_ROLES = [
    pytest.param(UserRole.SUPERADMIN, frozenset([PredefinedRole.ADMIN]), id="superadmin"),
    pytest.param(UserRole.MONITOR, frozenset([PredefinedRole.ADMIN]), id="monitor"),
    pytest.param(UserRole.ADMIN, frozenset([PredefinedRole.ADMIN]), id="admin"),
    pytest.param(UserRole.USER, frozenset(), id="user"),
]


class TestPredefinedRolesInProjectScope:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                UserRow,
                ProjectRow,
                AssocGroupUserRow,
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> DomainFixtureData:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                )
            )
        return DomainFixtureData(domain_name=DomainName(domain_name), domain_id=domain_id)

    @pytest.fixture
    async def test_project_id(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_domain: DomainFixtureData
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
        policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await sess.flush()
            sess.add(
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
                )
            )
        return project_id

    @pytest.fixture
    async def test_user_id(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_domain: DomainFixtureData
    ) -> uuid.UUID:
        user_id = uuid.uuid4()
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=user_id,
                    username=f"testuser-{user_id.hex[:8]}",
                    email=f"test-{user_id.hex[:8]}@example.com",
                    password=PasswordInfo(
                        password="dummy",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=600_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    domain_name=test_domain.domain_name,
                    role=UserRole.USER,
                    resource_policy=policy_name,
                    domain_id=test_domain.domain_id,
                )
            )
        return user_id

    async def _roles(
        self,
        db: ExtendedAsyncSAEngine,
        domain: DomainFixtureData,
        user_id: uuid.UUID,
        user_role: UserRole,
        project_id: uuid.UUID,
    ) -> frozenset[PredefinedRole]:
        ctx = ClientContext(db, domain.domain_name, user_id, user_role)
        return await get_predefined_roles_in_scope(ctx, ProjectScope(project_id))

    @pytest.mark.parametrize(("user_role", "expected"), _MEMBER_ROLES)
    async def test_graph_membership_grants_member_roles(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_project_id: uuid.UUID,
        test_user_id: uuid.UUID,
        user_role: UserRole,
        expected: frozenset[PredefinedRole],
    ) -> None:
        async with db_with_cleanup.begin_session() as sess:
            await VirtualEntitySeeder().enroll_user_in_project(sess, test_project_id, test_user_id)

        roles = await self._roles(
            db_with_cleanup, test_domain, test_user_id, user_role, test_project_id
        )

        assert roles == expected

    @pytest.mark.parametrize(("user_role", "expected"), _NON_MEMBER_ROLES)
    async def test_legacy_membership_is_ignored(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_project_id: uuid.UUID,
        test_user_id: uuid.UUID,
        user_role: UserRole,
        expected: frozenset[PredefinedRole],
    ) -> None:
        async with db_with_cleanup.begin_session() as sess:
            sess.add(AssocGroupUserRow(group_id=test_project_id, user_id=test_user_id))

        roles = await self._roles(
            db_with_cleanup, test_domain, test_user_id, user_role, test_project_id
        )

        assert roles == expected

    async def test_another_domain_project_grants_nothing_to_domain_admin(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_project_id: uuid.UUID,
        test_user_id: uuid.UUID,
    ) -> None:
        async with db_with_cleanup.begin_session() as sess:
            await VirtualEntitySeeder().enroll_user_in_project(sess, test_project_id, test_user_id)
        other_domain = DomainFixtureData(
            domain_name=DomainName("other-domain"), domain_id=DomainID(uuid.uuid4())
        )

        roles = await self._roles(
            db_with_cleanup, other_domain, test_user_id, UserRole.ADMIN, test_project_id
        )

        assert roles == frozenset()
