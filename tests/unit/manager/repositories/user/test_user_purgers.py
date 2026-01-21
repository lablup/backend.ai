"""
Tests for user purgers functionality.
Tests the purger pattern implementation for user-related deletions.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow, ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder.row import VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.base.purger import BatchPurger, execute_batch_purger
from ai.backend.manager.repositories.user.purgers import (
    UserErrorLogPurgerSpec,
    UserGroupAssociationPurgerSpec,
    UserKeyPairPurgerSpec,
    UserPurgerSpec,
    UserVFolderPermissionPurgerSpec,
    create_user_error_log_purger,
    create_user_group_association_purger,
    create_user_keypair_purger,
    create_user_purger,
    create_user_vfolder_permission_purger,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Force mapper initialization by importing Row classes with relationships
# This ensures all related mappers are initialized before tests run
_ = (AgentRow, KernelRow, SessionRow, ImageRow, ScalingGroupRow)


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    """Create a PasswordInfo object for testing."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestUserPurgerSpecs:
    """Tests for PurgerSpec classes - verifying build_subquery() generates correct conditions."""

    def test_user_error_log_purger_spec_build_subquery(self) -> None:
        """Test UserErrorLogPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserErrorLogPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()

        # Verify it's a SELECT statement targeting ErrorLogRow
        assert subquery is not None
        # Use str() without literal_binds to avoid UUID rendering issues
        sql_str = str(subquery)

        assert "error_logs" in sql_str
        # Check the column reference is present (bound parameter will be :user_1 etc.)
        assert '"user"' in sql_str or "error_logs.user" in sql_str.lower()

    def test_user_keypair_purger_spec_build_subquery(self) -> None:
        """Test UserKeyPairPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserKeyPairPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()
        sql_str = str(subquery)

        assert "keypairs" in sql_str
        assert "keypairs.user" in sql_str.lower() or '"user"' in sql_str

    def test_user_group_association_purger_spec_build_subquery(self) -> None:
        """Test UserGroupAssociationPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserGroupAssociationPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()
        sql_str = str(subquery)

        assert "association_groups_users" in sql_str
        assert "user_id" in sql_str.lower()

    def test_user_vfolder_permission_purger_spec_build_subquery(self) -> None:
        """Test UserVFolderPermissionPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserVFolderPermissionPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()
        sql_str = str(subquery)

        assert "vfolder_permissions" in sql_str
        assert "vfolder_permissions.user" in sql_str.lower() or '"user"' in sql_str

    def test_user_purger_spec_build_subquery(self) -> None:
        """Test UserPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()
        sql_str = str(subquery)

        assert "users" in sql_str
        assert "users.uuid" in sql_str.lower() or '"uuid"' in sql_str


class TestUserPurgerFactoryFunctions:
    """Tests for purger factory functions."""

    def test_create_user_error_log_purger(self) -> None:
        """Test create_user_error_log_purger returns correct BatchPurger."""
        user_uuid = uuid.uuid4()

        purger = create_user_error_log_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserErrorLogPurgerSpec)
        assert purger.spec.user_uuid == user_uuid

    def test_create_user_keypair_purger(self) -> None:
        """Test create_user_keypair_purger returns correct BatchPurger."""
        user_uuid = uuid.uuid4()

        purger = create_user_keypair_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserKeyPairPurgerSpec)
        assert purger.spec.user_uuid == user_uuid

    def test_create_user_group_association_purger(self) -> None:
        """Test create_user_group_association_purger returns correct BatchPurger."""
        user_uuid = uuid.uuid4()

        purger = create_user_group_association_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserGroupAssociationPurgerSpec)
        assert purger.spec.user_uuid == user_uuid

    def test_create_user_vfolder_permission_purger(self) -> None:
        """Test create_user_vfolder_permission_purger returns correct BatchPurger."""
        user_uuid = uuid.uuid4()

        purger = create_user_vfolder_permission_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserVFolderPermissionPurgerSpec)
        assert purger.spec.user_uuid == user_uuid

    def test_create_user_purger(self) -> None:
        """Test create_user_purger returns correct BatchPurger with batch_size=1."""
        user_uuid = uuid.uuid4()

        purger = create_user_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserPurgerSpec)
        assert purger.spec.user_uuid == user_uuid
        assert purger.batch_size == 1  # User purger should have batch_size=1


class TestUserPurgersIntegration:
    """Integration tests for user purgers with real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssocGroupUserRow,
                ErrorLogRow,
                VFolderRow,
                VFolderPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def sample_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a test domain."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
        return domain_name

    @pytest.fixture
    async def user_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a user resource policy."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
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
    async def keypair_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a keypair resource policy."""
        policy_name = "default"
        async with db_with_cleanup.begin_session() as session:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                total_resource_slots={},
                max_concurrent_sessions=10,
                max_session_lifetime=0,
                max_pending_session_count=5,
                max_pending_session_resource_slots={},
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=0,
            )
            session.add(policy)
        return policy_name

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
    async def sample_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        user_resource_policy: str,
    ) -> UserRow:
        """Create a test user and return the UserRow."""
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=create_test_password_info("test_password"),
                need_password_change=False,
                full_name="Test User",
                description="Test Description",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=sample_domain,
                role=UserRole.USER,
                resource_policy=user_resource_policy,
            )
            session.add(user)
            await session.flush()
            # Refresh to get the actual object back
            await session.refresh(user)
            # Expunge to detach from session so we can use it outside
            session.expunge(user)
        return user

    @pytest.mark.asyncio
    async def test_purge_user_error_logs(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
    ) -> None:
        """Test purging user's error logs."""
        user_uuid = sample_user.uuid

        # Create error logs for the user
        async with db_with_cleanup.begin_session() as session:
            for i in range(3):
                error_log = ErrorLogRow(
                    severity=ErrorLogSeverity.ERROR,
                    source="test",
                    message=f"Test error {i}",
                    context_lang="en",
                    context_env={},
                    user=user_uuid,
                )
                session.add(error_log)

        # Verify error logs exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(ErrorLogRow.__table__)
                .where(ErrorLogRow.__table__.c.user == user_uuid)
            )
            assert count == 3

        # Purge error logs
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_error_log_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 3

        # Verify error logs are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(ErrorLogRow.__table__)
                .where(ErrorLogRow.__table__.c.user == user_uuid)
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_user_keypairs(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
        keypair_resource_policy: str,
    ) -> None:
        """Test purging user's keypairs."""
        user_uuid = sample_user.uuid

        # Create keypairs for the user
        async with db_with_cleanup.begin_session() as session:
            for i in range(2):
                keypair = KeyPairRow(
                    user=user_uuid,
                    access_key=f"AKTEST{uuid.uuid4().hex[:12].upper()}",
                    secret_key=f"SK{uuid.uuid4().hex}",
                    is_active=True,
                    is_admin=False,
                    resource_policy=keypair_resource_policy,
                    rate_limit=1000,
                    num_queries=0,
                )
                session.add(keypair)

        # Verify keypairs exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(KeyPairRow)
                .where(KeyPairRow.user == user_uuid)
            )
            assert count == 2

        # Purge keypairs
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_keypair_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 2

        # Verify keypairs are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(KeyPairRow)
                .where(KeyPairRow.user == user_uuid)
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_user_group_associations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
        sample_domain: str,
        project_resource_policy: str,
    ) -> None:
        """Test purging user's group associations."""
        user_uuid = sample_user.uuid

        # Create groups and associations
        async with db_with_cleanup.begin_session() as session:
            for i in range(2):
                group = GroupRow(
                    id=uuid.uuid4(),
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    description="Test group",
                    is_active=True,
                    domain_name=sample_domain,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    integration_id=None,
                    resource_policy=project_resource_policy,
                    type=ProjectType.GENERAL,
                )
                session.add(group)
                await session.flush()

                assoc = AssocGroupUserRow(
                    user_id=user_uuid,
                    group_id=group.id,
                )
                session.add(assoc)

        # Verify associations exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(AssocGroupUserRow)
                .where(AssocGroupUserRow.user_id == user_uuid)
            )
            assert count == 2

        # Purge associations
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_group_association_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 2

        # Verify associations are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(AssocGroupUserRow)
                .where(AssocGroupUserRow.user_id == user_uuid)
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_user_vfolder_permissions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
        sample_domain: str,
    ) -> None:
        """Test purging user's vfolder permissions."""
        user_uuid = sample_user.uuid

        # Create a vfolder and permissions for the user
        async with db_with_cleanup.begin_session() as session:
            vfolder_id = uuid.uuid4()
            vfolder = VFolderRow(
                id=vfolder_id,
                host="local",
                domain_name=sample_domain,
                quota_scope_id=QuotaScopeID(QuotaScopeType.USER, user_uuid),
                name=f"test-vfolder-{uuid.uuid4().hex[:8]}",
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.READ_WRITE,
                ownership_type=VFolderOwnershipType.USER,
                user=user_uuid,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
            session.add(vfolder)
            await session.flush()

            # Create permissions (shared with another user scenario)
            for _ in range(2):
                perm = VFolderPermissionRow(
                    vfolder=vfolder_id,
                    user=user_uuid,
                    permission=VFolderMountPermission.READ_ONLY,
                )
                session.add(perm)

        # Verify permissions exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderPermissionRow)
                .where(VFolderPermissionRow.user == user_uuid)
            )
            assert count == 2

        # Purge permissions
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_vfolder_permission_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 2

        # Verify permissions are deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderPermissionRow)
                .where(VFolderPermissionRow.user == user_uuid)
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
    ) -> None:
        """Test purging the user itself."""
        user_uuid = sample_user.uuid

        # Verify user exists
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count()).select_from(UserRow).where(UserRow.uuid == user_uuid)
            )
            assert count == 1

        # Purge user
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 1

        # Verify user is deleted
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count()).select_from(UserRow).where(UserRow.uuid == user_uuid)
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_purge_nonexistent_user_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test purging data for a non-existent user returns 0 deleted count."""
        nonexistent_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
            purger = create_user_error_log_purger(nonexistent_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 0

        async with db_with_cleanup.begin_session() as session:
            purger = create_user_keypair_purger(nonexistent_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 0

        async with db_with_cleanup.begin_session() as session:
            purger = create_user_group_association_purger(nonexistent_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 0

        async with db_with_cleanup.begin_session() as session:
            purger = create_user_vfolder_permission_purger(nonexistent_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 0

        async with db_with_cleanup.begin_session() as session:
            purger = create_user_purger(nonexistent_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == 0
