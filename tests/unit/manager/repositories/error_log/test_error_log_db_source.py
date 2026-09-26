"""Tests for the domain admin's view of error logs."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.project import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.error_log.db_source.db_source import ErrorLogDBSource
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


@dataclass
class AdminViewFixture:
    domain_name: str
    admin_id: uuid.UUID
    graph_member_id: uuid.UUID
    legacy_member_id: uuid.UUID


class TestErrorLogListLogsAsDomainAdmin:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                ProjectRow,
                AssocGroupUserRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
                ErrorLogRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def admin_view(self, db_with_cleanup: ExtendedAsyncSAEngine) -> AdminViewFixture:
        """One project in the domain: one user enrolled in the graph, one only in the
        legacy association table. Each has an error log."""
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"dom-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        admin_id = uuid.uuid4()
        graph_member_id = uuid.uuid4()
        legacy_member_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                )
            )
            user_policy = UserResourcePolicyRow(
                name=f"upol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            project_policy = ProjectResourcePolicyRow(
                name=f"ppol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(user_policy)
            session.add(project_policy)
            await session.flush()

            for user_id, role in [
                (admin_id, UserRole.ADMIN),
                (graph_member_id, UserRole.USER),
                (legacy_member_id, UserRole.USER),
            ]:
                session.add(
                    UserRow(
                        uuid=user_id,
                        username=f"user-{user_id.hex[:8]}",
                        email=f"{user_id.hex[:8]}@example.com",
                        password=PasswordInfo(
                            password="dummy",
                            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                            rounds=100_000,
                            salt_size=32,
                        ),
                        need_password_change=False,
                        status=UserStatus.ACTIVE,
                        status_info="active",
                        domain_name=domain_name,
                        role=role,
                        resource_policy=user_policy.name,
                        domain_id=domain_id,
                    )
                )
            session.add(
                ProjectRow(
                    id=project_id,
                    name=f"proj-{project_id.hex[:8]}",
                    description="",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=project_policy.name,
                    type=ProjectType.GENERAL,
                )
            )
            await session.flush()

            await VirtualEntitySeeder().enroll_user_in_project(session, project_id, graph_member_id)
            session.add(AssocGroupUserRow(group_id=project_id, user_id=legacy_member_id))
            for user_id in (graph_member_id, legacy_member_id):
                session.add(
                    ErrorLogRow(
                        severity="error",
                        source="manager",
                        user=user_id,
                        message=f"log of {user_id}",
                        context_lang="en",
                        context_env={},
                    )
                )

        return AdminViewFixture(
            domain_name=domain_name,
            admin_id=admin_id,
            graph_member_id=graph_member_id,
            legacy_member_id=legacy_member_id,
        )

    async def test_admin_sees_logs_of_graph_members_only(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        admin_view: AdminViewFixture,
    ) -> None:
        items, total_count = await ErrorLogDBSource(db_with_cleanup).list_logs(
            user_uuid=admin_view.admin_id,
            user_domain=admin_view.domain_name,
            is_superadmin=False,
            is_admin=True,
            page_no=1,
            page_size=10,
            mark_read=False,
        )

        assert total_count == 1
        assert [item.meta.user for item in items] == [admin_view.graph_member_id]
