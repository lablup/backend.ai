"""
Tests for AuthRepository functionality.
"""

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import UserNotFound
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.auth.types import UserData
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.errors.auth import GroupMembershipNotFoundError
from ai.backend.manager.models import (
    DomainRow,
    GroupRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
    UserRow,
    association_groups_users,
)
from ai.backend.manager.models.group import AssocGroupUserRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.testutils.db import with_tables


@dataclass
class UserTestData(UserData):
    """Extended UserData with test-specific fields"""

    access_key: str
    ssh_public_key: str
    ssh_private_key: str


@dataclass
class DomainTestData:
    """Test data for domain fixture"""

    name: str


@dataclass
class ResourcePolicyTestData:
    """Test data for resource policy fixtures"""

    name: str


class TestAuthRepository:
    """Test cases for AuthRepository with real database"""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AssocGroupUserRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def auth_repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> AuthRepository:
        return AuthRepository(db=db_with_cleanup)

    @pytest.fixture
    async def default_domain(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[DomainTestData, None]:
        """Create default domain"""
        domain_name = f"domain-{uuid.uuid4()}"
        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Default domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()
        yield DomainTestData(name=domain_name)

    @pytest.fixture
    async def user_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ResourcePolicyTestData, None]:
        """Create user resource policy"""
        policy_name = f"test-user-policy-{uuid.uuid4()}"
        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(policy)
            await db_sess.commit()
        yield ResourcePolicyTestData(name=policy_name)

    @pytest.fixture
    async def keypair_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ResourcePolicyTestData, None]:
        """Create keypair resource policy"""
        policy_name = f"test-keypair-policy-{uuid.uuid4()}"
        async with db_with_cleanup.begin_session() as db_sess:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=2,
                max_containers_per_session=10,
                idle_timeout=3600,
            )
            db_sess.add(policy)
            await db_sess.commit()
        yield ResourcePolicyTestData(name=policy_name)

    @pytest.fixture
    async def sample_user_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        default_domain: DomainTestData,
        user_resource_policy: ResourcePolicyTestData,
        keypair_resource_policy: ResourcePolicyTestData,
    ) -> AsyncGenerator[UserTestData, None]:
        """Create a sample user for testing"""
        user_uuid = uuid.uuid4()
        email = f"test-{uuid.uuid4()}@example.com"
        access_key = f"AKIATEST{uuid.uuid4().hex[:10]}"
        ssh_public_key = f"ssh-rsa AAAAB3NzaC1yc2ETEST{uuid.uuid4().hex[:16]}..."
        ssh_private_key = f"-----BEGIN RSA PRIVATE KEY-----\nTEST{uuid.uuid4().hex[:32]}\n-----END RSA PRIVATE KEY-----"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create test user with hashed password
            password_info = PasswordInfo(
                password="test_password",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=100_000,
                salt_size=32,
            )
            user = UserRow(
                uuid=user_uuid,
                username=email,
                email=email,
                password=password_info,
                domain_name=default_domain.name,
                role=UserRole.USER,
                resource_policy=user_resource_policy.name,
            )
            db_sess.add(user)
            await db_sess.flush()

            # Create test keypair with SSH keys
            keypair = KeyPairRow(
                access_key=access_key,
                secret_key="test_secret_key",
                user_id=email,
                user=user_uuid,
                is_active=True,
                resource_policy=keypair_resource_policy.name,
                ssh_public_key=ssh_public_key,
                ssh_private_key=ssh_private_key,
            )
            db_sess.add(keypair)
            await db_sess.flush()
            await db_sess.refresh(user)

            user_data = UserTestData(
                uuid=user.uuid,
                username=user.username,
                email=user.email,
                password=user.password,
                need_password_change=user.need_password_change,
                full_name=user.full_name or "",
                description=user.description or "",
                is_active=user.status == UserStatus.ACTIVE,
                status=user.status,
                status_info=user.status_info,
                created_at=user.created_at,
                modified_at=user.modified_at,
                password_changed_at=user.password_changed_at,
                domain_name=user.domain_name,
                role=user.role,
                integration_id=user.integration_id,
                resource_policy=user.resource_policy,
                sudo_session_enabled=user.sudo_session_enabled,
                access_key=access_key,
                ssh_public_key=ssh_public_key,
                ssh_private_key=ssh_private_key,
            )
        yield user_data

    @pytest.fixture
    async def project_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ResourcePolicyTestData, None]:
        """Create project resource policy"""
        policy_name = f"test-group-policy-{uuid.uuid4()}"
        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(policy)
            await db_sess.commit()
        yield ResourcePolicyTestData(name=policy_name)

    @pytest.fixture
    async def sample_group_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_user_data: UserTestData,
        project_resource_policy: ResourcePolicyTestData,
    ) -> AsyncGenerator[GroupData, None]:
        """Create a sample group with user membership for testing"""
        group_id = uuid.uuid4()
        group_name = f"test-group-{uuid.uuid4()}"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create test group
            group = GroupRow(
                id=group_id,
                name=group_name,
                description="Test Group",
                is_active=True,
                domain_name=sample_user_data.domain_name,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy=project_resource_policy.name,
            )
            db_sess.add(group)
            await db_sess.flush()

            # Add user to group
            await db_sess.execute(
                association_groups_users.insert().values(
                    user_id=sample_user_data.uuid,
                    group_id=group_id,
                )
            )
            await db_sess.flush()
            await db_sess.refresh(group)

            group_data = GroupData(
                id=group.id,
                name=group.name,
                description=group.description,
                is_active=group.is_active,
                created_at=group.created_at,
                modified_at=group.modified_at,
                integration_id=group.integration_id,
                domain_name=group.domain_name,
                total_resource_slots=group.total_resource_slots,
                allowed_vfolder_hosts=group.allowed_vfolder_hosts,
                dotfiles=group.dotfiles,
                resource_policy=group.resource_policy,
                type=group.type,
                container_registry=group.container_registry,
            )
        yield group_data

    @pytest.mark.asyncio
    async def test_get_group_membership_success(
        self,
        auth_repository: AuthRepository,
        sample_user_data: UserTestData,
        sample_group_data: GroupData,
    ) -> None:
        """Test successful group membership retrieval"""
        result = await auth_repository.get_group_membership(
            sample_group_data.id, sample_user_data.uuid
        )

        assert result is not None
        assert result.group_id == sample_group_data.id
        assert result.user_id == sample_user_data.uuid

    @pytest.mark.asyncio
    async def test_get_group_membership_not_found(
        self, auth_repository: AuthRepository, sample_user_data: UserTestData
    ) -> None:
        """Test group membership retrieval when not found"""
        non_existent_group_id = UUID("99999999-9999-9999-9999-999999999999")

        with pytest.raises(GroupMembershipNotFoundError):
            await auth_repository.get_group_membership(non_existent_group_id, sample_user_data.uuid)

    @pytest.mark.asyncio
    async def test_check_email_exists(
        self, auth_repository: AuthRepository, sample_user_data: UserTestData
    ) -> None:
        """Test email existence check when email exists"""
        result = await auth_repository.check_email_exists(sample_user_data.email)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_email_not_exists(self, auth_repository: AuthRepository) -> None:
        """Test email existence check when email doesn't exist"""
        result = await auth_repository.check_email_exists("nonexistent@example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_user_full_name(
        self,
        auth_repository: AuthRepository,
        sample_user_data: UserTestData,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test updating user full name"""
        update_name = "Updated Full Name"
        await auth_repository.update_user_full_name(
            sample_user_data.email, sample_user_data.domain_name, update_name
        )

        # Verify full name was updated
        async with db_with_cleanup.begin_session() as db_sess:
            user = await db_sess.scalar(
                sa.select(UserRow).where(UserRow.uuid == sample_user_data.uuid)
            )
            assert user is not None
            assert user.full_name == update_name

    @pytest.mark.asyncio
    async def test_update_user_full_name_not_found(
        self, auth_repository: AuthRepository, default_domain: DomainTestData
    ) -> None:
        """Test updating user full name when user doesn't exist"""
        with pytest.raises(UserNotFound):
            await auth_repository.update_user_full_name(
                "nonexistent@example.com", default_domain.name, "Some Name"
            )

    @pytest.mark.asyncio
    async def test_update_user_password(
        self,
        auth_repository: AuthRepository,
        sample_user_data: UserTestData,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test updating user password"""
        update_password_info = PasswordInfo(
            password="new_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

        await auth_repository.update_user_password(sample_user_data.email, update_password_info)

        # Verify password was updated
        async with db_with_cleanup.begin_session() as db_sess:
            user = await db_sess.scalar(
                sa.select(UserRow).where(UserRow.uuid == sample_user_data.uuid)
            )
            assert user is not None
            assert user.password != sample_user_data.password  # Password should have changed

    @pytest.mark.asyncio
    async def test_update_user_password_by_uuid(
        self,
        auth_repository: AuthRepository,
        sample_user_data: UserTestData,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test updating user password by UUID"""
        password_info = PasswordInfo(
            password="new_password_uuid",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )

        await auth_repository.update_user_password_by_uuid(sample_user_data.uuid, password_info)

        # Verify password was updated
        async with db_with_cleanup.begin_session() as db_sess:
            user = await db_sess.scalar(
                sa.select(UserRow).where(UserRow.uuid == sample_user_data.uuid)
            )
            assert user is not None
            assert user.password != sample_user_data.password

    @pytest.mark.asyncio
    async def test_deactivate_user_and_keypairs(
        self,
        auth_repository: AuthRepository,
        sample_user_data: UserTestData,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test deactivating user and keypairs"""
        await auth_repository.deactivate_user_and_keypairs(sample_user_data.email)

        # Verify user was deactivated
        async with db_with_cleanup.begin_session() as db_sess:
            user = await db_sess.scalar(
                sa.select(UserRow).where(UserRow.uuid == sample_user_data.uuid)
            )
            assert user is not None
            assert user.status == UserStatus.INACTIVE

            # Verify keypair was deactivated
            keypair = await db_sess.scalar(
                sa.select(KeyPairRow).where(KeyPairRow.access_key == sample_user_data.access_key)
            )
            assert keypair is not None
            assert keypair.is_active is False

    @pytest.mark.asyncio
    async def test_get_ssh_public_key(
        self,
        auth_repository: AuthRepository,
        sample_user_data: UserTestData,
    ) -> None:
        """Test retrieving SSH public key"""
        result = await auth_repository.get_ssh_public_key(sample_user_data.access_key)

        assert result == sample_user_data.ssh_public_key

    @pytest.mark.asyncio
    async def test_update_ssh_keypair(
        self,
        auth_repository: AuthRepository,
        sample_user_data: UserTestData,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test updating SSH keypair"""
        update_public_key = "ssh-rsa AAAAB3NzaC1yc2EUPDATED..."
        update_private_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nUPDATED...\n-----END RSA PRIVATE KEY-----"
        )

        await auth_repository.update_ssh_keypair(
            sample_user_data.access_key,
            update_public_key,
            update_private_key,
        )

        # Verify SSH keypair was updated
        async with db_with_cleanup.begin_session() as db_sess:
            keypair = await db_sess.scalar(
                sa.select(KeyPairRow).where(KeyPairRow.access_key == sample_user_data.access_key)
            )
            assert keypair is not None
            assert keypair.ssh_public_key == update_public_key
            assert keypair.ssh_private_key == update_private_key

    @pytest.mark.asyncio
    async def test_get_user_row_by_uuid(
        self, auth_repository: AuthRepository, sample_user_data: UserTestData
    ) -> None:
        """Test getting user row by UUID"""
        result = await auth_repository.get_user_row_by_uuid(sample_user_data.uuid)

        assert result is not None
        assert isinstance(result, UserRow)
        assert result.uuid == sample_user_data.uuid
        assert result.email == sample_user_data.email

    @pytest.mark.asyncio
    async def test_get_user_row_by_uuid_not_found(self, auth_repository: AuthRepository) -> None:
        """Test getting user row by UUID when user doesn't exist"""
        non_existent_uuid = UUID("99999999-9999-9999-9999-999999999999")

        with pytest.raises(UserNotFound):
            await auth_repository.get_user_row_by_uuid(non_existent_uuid)

    @pytest.mark.asyncio
    async def test_get_current_time(self, auth_repository: AuthRepository) -> None:
        """Test getting current time from database"""
        result = await auth_repository.get_current_time()

        assert isinstance(result, datetime)
        # Verify it's reasonably close to current time (within 1 second)
        now_utc = datetime.now(timezone.utc)
        time_diff = abs((now_utc - result).total_seconds())
        assert time_diff < 1.0
