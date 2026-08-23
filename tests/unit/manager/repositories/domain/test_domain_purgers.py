"""
Tests for domain purgers functionality.
Tests the purger pattern implementation for domain-related deletions.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.errors.resource import DomainHasGroups, DomainHasUsers
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.domain.purgers import DomainKernelPurger, DomainPurger
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.session import SessionRow, SessionStatus, SessionTypes
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory, DomainFixtureData

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestDomainPurgersIntegration:
    """Integration tests for domain purgers with real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                RoleRow,
                PermissionRow,
                VirtualScopeRow,
                EntityMembershipRow,
                ScopeBindingRow,
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ResourceGroupRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                SessionRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_domain(
        self,
        domain_factory: DomainFactory,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        """Create a test domain."""
        return await domain_factory(db_with_cleanup)

    @pytest.fixture
    async def project_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a project resource policy."""
        policy_name = f"project-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(policy)
        return policy_name

    @pytest.fixture
    async def user_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a user resource policy."""
        policy_name = f"user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(policy)
        return policy_name

    @pytest.fixture
    async def sample_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        user_resource_policy: str,
    ) -> UserRow:
        """Create a test user."""
        user_uuid = uuid.uuid4()
        password_info = PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="Test User",
                description="Test user for integration tests",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=sample_domain.domain_name,
                role=UserRole.USER,
                resource_policy=user_resource_policy,
                domain_id=sample_domain.domain_id,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    @pytest.fixture
    async def sample_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        project_resource_policy: str,
    ) -> ProjectRow:
        """Create a test group."""
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            group = ProjectRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group for integration tests",
                is_active=True,
                domain_name=sample_domain.domain_name,
                total_resource_slots=ResourceSlot({}),
                allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                dotfiles=b"\x90",
                resource_policy=project_resource_policy,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.flush()
            await session.refresh(group)
            return group

    @pytest.fixture
    async def sample_sessions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_group: ProjectRow,
        sample_domain: DomainFixtureData,
        sample_user: UserRow,
    ) -> list[SessionRow]:
        """Create test sessions belonging to the domain."""
        sessions: list[SessionRow] = []
        sgroup_name = f"default-{uuid.uuid4().hex[:8]}"
        sgroup_id = ResourceGroupID(uuid.uuid4())
        async with db_with_cleanup.begin_session() as session:
            sgroup = ResourceGroupRow(
                name=sgroup_name,
                id=sgroup_id,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
            )
            session.add(sgroup)
            await session.flush()
            for i in range(3):
                sess = SessionRow(
                    name=f"test-session-{i}-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode="single-node",
                    cluster_size=1,
                    domain_name=sample_domain.domain_name,
                    domain_id=sample_domain.domain_id,
                    group_id=sample_group.id,
                    scaling_group_name=sgroup_name,
                    resource_group_id=sgroup_id,
                    user_uuid=sample_user.uuid,
                    status=SessionStatus.TERMINATED,
                    status_info="",
                    target_sgroup_names=[],
                    vfolder_mounts=[],
                    environ={},
                )
                session.add(sess)
                sessions.append(sess)
            await session.flush()
            for sess in sessions:
                await session.refresh(sess)
        return sessions

    @pytest.fixture
    async def sample_kernels(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_sessions: list[SessionRow],
        sample_domain: DomainFixtureData,
        sample_group: ProjectRow,
        sample_user: UserRow,
    ) -> list[KernelRow]:
        """Create test kernels belonging to sessions in the domain."""
        kernels: list[KernelRow] = []
        async with db_with_cleanup.begin_session() as session:
            for sess in sample_sessions:
                kernel = KernelRow(
                    session_id=sess.id,
                    domain_name=sample_domain.domain_name,
                    group_id=sample_group.id,
                    user_uuid=sample_user.uuid,
                    scaling_group=sess.scaling_group_name,
                    resource_group_id=sess.resource_group_id,
                    occupied_shares={},
                    vfolder_mounts=[],
                    status=KernelStatus.TERMINATED,
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                )
                session.add(kernel)
                kernels.append(kernel)
            await session.flush()
            for kernel in kernels:
                await session.refresh(kernel)
        return kernels

    async def test_purge_domain_kernels(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        sample_kernels: list[KernelRow],
    ) -> None:
        """Test purging kernels belonging to a domain."""
        domain_name = sample_domain.domain_name

        # Purge kernels
        async with V2DBOpsProvider(db_with_cleanup).write_ops() as w:
            purged = await w.batch_purge_in_global(DomainKernelPurger(name=domain_name))
            assert len(purged) == len(sample_kernels)

        # Verify kernels are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(KernelRow)
                .where(KernelRow.domain_name == domain_name)
            )
            assert count == 0

    async def test_purge_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
    ) -> None:
        """Test purging the domain itself."""
        domain_name = sample_domain.domain_name

        # Purge domain
        async with V2DBOpsProvider(db_with_cleanup).write_ops() as w:
            purged = await w.purge_entity(
                DomainPurger(domain_id=sample_domain.domain_id, name=domain_name)
            )
            assert purged is not None

        # Verify domain is deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(DomainRow)
                .where(DomainRow.name == domain_name)
            )
            assert count == 0

    async def test_purge_domain_spec_succeeds_without_conflicts(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
    ) -> None:
        """DomainPurger deletes a domain with no bound users or groups."""
        domain_name = sample_domain.domain_name

        async with V2DBOpsProvider(db_with_cleanup).write_ops() as w:
            purged = await w.purge_entity(
                DomainPurger(domain_id=sample_domain.domain_id, name=domain_name)
            )
            assert purged is not None
            assert purged.name == domain_name

        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(DomainRow)
                .where(DomainRow.name == domain_name)
            )
            assert count == 0

    async def test_purge_domain_spec_blocked_by_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        sample_user: UserRow,
    ) -> None:
        """DomainPurger raises DomainHasUsers while users remain bound."""
        domain_name = sample_domain.domain_name

        async with V2DBOpsProvider(db_with_cleanup).write_ops() as w:
            with pytest.raises(DomainHasUsers):
                await w.purge_entity(
                    DomainPurger(domain_id=sample_domain.domain_id, name=domain_name)
                )

        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(DomainRow)
                .where(DomainRow.name == domain_name)
            )
            assert count == 1

    async def test_purge_domain_spec_blocked_by_groups(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        sample_group: ProjectRow,
    ) -> None:
        """DomainPurger raises DomainHasGroups while groups remain bound."""
        domain_name = sample_domain.domain_name

        async with V2DBOpsProvider(db_with_cleanup).write_ops() as w:
            with pytest.raises(DomainHasGroups):
                await w.purge_entity(
                    DomainPurger(domain_id=sample_domain.domain_id, name=domain_name)
                )

        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(DomainRow)
                .where(DomainRow.name == domain_name)
            )
            assert count == 1
