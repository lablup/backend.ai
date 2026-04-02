"""Tests for GroupDBSource.assign_users_to_project()"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
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
from ai.backend.testutils.db import with_tables


class TestAssignUsersToProject:
    """Tests for GroupDBSource.assign_users_to_project"""

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
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
    async def other_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"other-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
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
        test_domain: str,
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
    async def same_domain_user_1(
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
    async def same_domain_user_2(
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
    async def cross_domain_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        other_domain: str,
        user_resource_policy: str,
        test_password_info: PasswordInfo,
    ) -> uuid.UUID:
        return await self._create_user(
            db_with_cleanup, other_domain, user_resource_policy, test_password_info
        )

    @pytest.fixture
    def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> GroupDBSource:
        return GroupDBSource(db=db_with_cleanup)

    # --- Test cases ---

    async def test_assign_users_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: uuid.UUID,
        same_domain_user_2: uuid.UUID,
    ) -> None:
        """Active users in same domain are assigned successfully."""
        result = await group_db_source.assign_users_to_project(
            test_project, [same_domain_user_1, same_domain_user_2]
        )

        assert len(result) == 2
        result_uuids = {u.uuid for u in result}
        assert result_uuids == {same_domain_user_1, same_domain_user_2}

        # Verify association rows created
        async with db_with_cleanup.begin_readonly_session() as session:
            assoc_result = await session.execute(
                sa.select(association_groups_users).where(
                    association_groups_users.c.group_id == test_project
                )
            )
            assert len(assoc_result.fetchall()) == 2

    async def test_assign_empty_list_returns_empty(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
    ) -> None:
        """Empty user_ids list returns empty result without DB access."""
        result = await group_db_source.assign_users_to_project(test_project, [])
        assert result == []

    async def test_assign_filters_already_assigned_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: uuid.UUID,
        same_domain_user_2: uuid.UUID,
    ) -> None:
        """Already-assigned users are excluded; only new users are returned."""
        # Pre-assign user_1
        await group_db_source.assign_users_to_project(test_project, [same_domain_user_1])

        # Assign both — only user_2 should be returned
        result = await group_db_source.assign_users_to_project(
            test_project, [same_domain_user_1, same_domain_user_2]
        )

        assert len(result) == 1
        assert result[0].uuid == same_domain_user_2

        # Verify total 2 associations
        async with db_with_cleanup.begin_readonly_session() as session:
            assoc_result = await session.execute(
                sa.select(association_groups_users).where(
                    association_groups_users.c.group_id == test_project
                )
            )
            assert len(assoc_result.fetchall()) == 2

    async def test_assign_filters_cross_domain_users(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        same_domain_user_1: uuid.UUID,
        cross_domain_user: uuid.UUID,
    ) -> None:
        """Users from a different domain are silently excluded."""
        result = await group_db_source.assign_users_to_project(
            test_project, [same_domain_user_1, cross_domain_user]
        )

        assert len(result) == 1
        assert result[0].uuid == same_domain_user_1

    async def test_assign_filters_nonexistent_users(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
    ) -> None:
        """Non-existent user UUIDs are silently excluded."""
        fake_user = uuid.uuid4()
        result = await group_db_source.assign_users_to_project(test_project, [fake_user])
        assert result == []

    async def test_assign_all_invalid_returns_empty(
        self,
        group_db_source: GroupDBSource,
        test_project: uuid.UUID,
        cross_domain_user: uuid.UUID,
    ) -> None:
        """When all users are invalid (wrong domain, nonexistent), return empty."""
        fake_user = uuid.uuid4()

        result = await group_db_source.assign_users_to_project(
            test_project, [cross_domain_user, fake_user]
        )
        assert result == []
