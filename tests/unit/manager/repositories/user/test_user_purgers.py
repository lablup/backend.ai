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

from ai.backend.common.types import QuotaScopeID, QuotaScopeType, ResourceSlot, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.agent import AgentRow  # noqa: F401
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow, ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow  # noqa: F401
from ai.backend.manager.models.kernel import KernelRow  # noqa: F401
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow  # noqa: F401
from ai.backend.manager.models.session import SessionRow  # noqa: F401
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder.row import VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.base.purger import BatchPurger, execute_batch_purger
from ai.backend.manager.repositories.user.purgers import (
    UserBatchPurgerSpec,
    UserErrorLogBatchPurgerSpec,
    UserGroupAssociationBatchPurgerSpec,
    UserKeyPairBatchPurgerSpec,
    UserVFolderPermissionBatchPurgerSpec,
    create_user_error_log_purger,
    create_user_group_association_purger,
    create_user_keypair_purger,
    create_user_purger,
    create_user_vfolder_permission_purger,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestUserPurgerSpecs:
    """Tests for PurgerSpec classes - verifying build_subquery() generates correct conditions."""

    def test_user_error_log_batch_purger_spec_build_subquery(self) -> None:
        """Test UserErrorLogBatchPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserErrorLogBatchPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()

        # Verify it's a SELECT statement targeting ErrorLogRow
        assert subquery is not None
        # Use str() without literal_binds to avoid UUID rendering issues
        sql_str = str(subquery)

        assert "error_logs" in sql_str
        # Check the column reference is present (bound parameter will be :user_1 etc.)
        assert '"user"' in sql_str or "error_logs.user" in sql_str.lower()

    def test_user_keypair_batch_purger_spec_build_subquery(self) -> None:
        """Test UserKeyPairBatchPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserKeyPairBatchPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()
        sql_str = str(subquery)

        assert "keypairs" in sql_str
        assert "keypairs.user" in sql_str.lower() or '"user"' in sql_str

    def test_user_group_association_batch_purger_spec_build_subquery(self) -> None:
        """Test UserGroupAssociationBatchPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserGroupAssociationBatchPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()
        sql_str = str(subquery)

        assert "association_groups_users" in sql_str
        assert "user_id" in sql_str.lower()

    def test_user_vfolder_permission_batch_purger_spec_build_subquery(self) -> None:
        """Test UserVFolderPermissionBatchPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserVFolderPermissionBatchPurgerSpec(user_uuid=user_uuid)

        subquery = spec.build_subquery()
        sql_str = str(subquery)

        assert "vfolder_permissions" in sql_str
        assert "vfolder_permissions.user" in sql_str.lower() or '"user"' in sql_str

    def test_user_batch_purger_spec_build_subquery(self) -> None:
        """Test UserBatchPurgerSpec builds correct subquery."""
        user_uuid = uuid.uuid4()
        spec = UserBatchPurgerSpec(user_uuid=user_uuid)

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
        assert isinstance(purger.spec, UserErrorLogBatchPurgerSpec)
        assert purger.spec.user_uuid == user_uuid

    def test_create_user_keypair_purger(self) -> None:
        """Test create_user_keypair_purger returns correct BatchPurger."""
        user_uuid = uuid.uuid4()

        purger = create_user_keypair_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserKeyPairBatchPurgerSpec)
        assert purger.spec.user_uuid == user_uuid

    def test_create_user_group_association_purger(self) -> None:
        """Test create_user_group_association_purger returns correct BatchPurger."""
        user_uuid = uuid.uuid4()

        purger = create_user_group_association_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserGroupAssociationBatchPurgerSpec)
        assert purger.spec.user_uuid == user_uuid

    def test_create_user_vfolder_permission_purger(self) -> None:
        """Test create_user_vfolder_permission_purger returns correct BatchPurger."""
        user_uuid = uuid.uuid4()

        purger = create_user_vfolder_permission_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserVFolderPermissionBatchPurgerSpec)
        assert purger.spec.user_uuid == user_uuid

    def test_create_user_purger(self) -> None:
        """Test create_user_purger returns correct BatchPurger with batch_size=1."""
        user_uuid = uuid.uuid4()

        purger = create_user_purger(user_uuid)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, UserBatchPurgerSpec)
        assert purger.spec.user_uuid == user_uuid
        assert purger.batch_size == 1  # User purger should have batch_size=1


class TestUserPurgersIntegration:
    """Integration tests for user purgers with real database."""

    @pytest.fixture
    def test_password_info(self) -> PasswordInfo:
        """Create a PasswordInfo object for testing."""
        return PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

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
                total_resource_slots=ResourceSlot(),
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
                total_resource_slots=ResourceSlot(),
                max_concurrent_sessions=10,
                max_session_lifetime=0,
                max_pending_session_count=5,
                max_pending_session_resource_slots=ResourceSlot(),
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
        test_password_info: PasswordInfo,
    ) -> UserRow:
        """Create a test user and return the UserRow."""
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=test_password_info,
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

    @pytest.fixture
    async def sample_error_logs(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
    ) -> list[ErrorLogRow]:
        """Create test error logs for the user."""
        error_logs: list[ErrorLogRow] = []
        async with db_with_cleanup.begin_session() as session:
            for i in range(3):
                error_log = ErrorLogRow(
                    severity=ErrorLogSeverity.ERROR,
                    source="test",
                    message=f"Test error {i}",
                    context_lang="en",
                    context_env={},
                    user=sample_user.uuid,
                )
                session.add(error_log)
                error_logs.append(error_log)
        return error_logs

    @pytest.fixture
    async def sample_keypairs(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
        keypair_resource_policy: str,
    ) -> list[KeyPairRow]:
        """Create test keypairs for the user."""
        keypairs: list[KeyPairRow] = []
        async with db_with_cleanup.begin_session() as session:
            for i in range(2):
                keypair = KeyPairRow(
                    user=sample_user.uuid,
                    access_key=f"AKTEST{uuid.uuid4().hex[:12].upper()}",
                    secret_key=f"SK{uuid.uuid4().hex}",
                    is_active=True,
                    is_admin=False,
                    resource_policy=keypair_resource_policy,
                    rate_limit=1000,
                    num_queries=0,
                )
                session.add(keypair)
                keypairs.append(keypair)
        return keypairs

    @pytest.fixture
    async def sample_group_associations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
        sample_domain: str,
        project_resource_policy: str,
    ) -> list[AssocGroupUserRow]:
        """Create test groups and associations for the user."""
        associations: list[AssocGroupUserRow] = []
        async with db_with_cleanup.begin_session() as session:
            for i in range(2):
                group = GroupRow(
                    id=uuid.uuid4(),
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    description="Test group",
                    is_active=True,
                    domain_name=sample_domain,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    integration_id=None,
                    resource_policy=project_resource_policy,
                    type=ProjectType.GENERAL,
                )
                session.add(group)
                await session.flush()

                assoc = AssocGroupUserRow(
                    user_id=sample_user.uuid,
                    group_id=group.id,
                )
                session.add(assoc)
                associations.append(assoc)
        return associations

    @pytest.fixture
    async def sample_vfolder_permissions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
        sample_domain: str,
    ) -> list[VFolderPermissionRow]:
        """Create test vfolder and permissions for the user."""
        permissions: list[VFolderPermissionRow] = []
        async with db_with_cleanup.begin_session() as session:
            vfolder_id = uuid.uuid4()
            vfolder = VFolderRow(
                id=vfolder_id,
                host="local",
                domain_name=sample_domain,
                quota_scope_id=QuotaScopeID(QuotaScopeType.USER, sample_user.uuid),
                name=f"test-vfolder-{uuid.uuid4().hex[:8]}",
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.READ_WRITE,
                ownership_type=VFolderOwnershipType.USER,
                user=sample_user.uuid,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
            session.add(vfolder)
            await session.flush()

            for _ in range(2):
                perm = VFolderPermissionRow(
                    vfolder=vfolder_id,
                    user=sample_user.uuid,
                    permission=VFolderMountPermission.READ_ONLY,
                )
                session.add(perm)
                permissions.append(perm)
        return permissions

    @pytest.mark.asyncio
    async def test_purge_user_error_logs(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user: UserRow,
        sample_error_logs: list[ErrorLogRow],
    ) -> None:
        """Test purging user's error logs."""
        user_uuid = sample_user.uuid

        # Verify error logs exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(ErrorLogRow.__table__)
                .where(ErrorLogRow.__table__.c.user == user_uuid)
            )
            assert count == len(sample_error_logs)

        # Purge error logs
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_error_log_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_error_logs)

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
        sample_keypairs: list[KeyPairRow],
    ) -> None:
        """Test purging user's keypairs."""
        user_uuid = sample_user.uuid

        # Verify keypairs exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(KeyPairRow)
                .where(KeyPairRow.user == user_uuid)
            )
            assert count == len(sample_keypairs)

        # Purge keypairs
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_keypair_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_keypairs)

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
        sample_group_associations: list[AssocGroupUserRow],
    ) -> None:
        """Test purging user's group associations."""
        user_uuid = sample_user.uuid

        # Verify associations exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(AssocGroupUserRow)
                .where(AssocGroupUserRow.user_id == user_uuid)
            )
            assert count == len(sample_group_associations)

        # Purge associations
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_group_association_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_group_associations)

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
        sample_vfolder_permissions: list[VFolderPermissionRow],
    ) -> None:
        """Test purging user's vfolder permissions."""
        user_uuid = sample_user.uuid

        # Verify permissions exist
        async with db_with_cleanup.begin_session() as session:
            count = await session.scalar(
                sa.select(sa.func.count())
                .select_from(VFolderPermissionRow)
                .where(VFolderPermissionRow.user == user_uuid)
            )
            assert count == len(sample_vfolder_permissions)

        # Purge permissions
        async with db_with_cleanup.begin_session() as session:
            purger = create_user_vfolder_permission_purger(user_uuid)
            result = await execute_batch_purger(session, purger)
            assert result.deleted_count == len(sample_vfolder_permissions)

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
