"""
Tests for UserRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, AsyncGenerator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import BinarySize
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.defs import DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.errors.user import (
    UserConflict,
    UserCreationBadRequest,
    UserModificationBadRequest,
    UserNotFound,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.types import OptionalState

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestUserRepository:
    """Test cases for UserRepository with real database operations"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans test data after each test"""
        try:
            yield database_engine
        finally:
            # Cleanup in FK-safe order
            async with database_engine.begin_session() as db_sess:
                await db_sess.execute(sa.delete(KeyPairRow))
                await db_sess.execute(sa.delete(UserRow))
                await db_sess.execute(sa.delete(UserResourcePolicyRow))
                await db_sess.execute(sa.delete(DomainRow))
                await db_sess.execute(sa.delete(KeyPairResourcePolicyRow))

    @pytest.fixture
    async def default_keypair_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create the default keypair resource policy required for user creation"""
        policy_name = DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME

        async with db_with_cleanup.begin_session() as db_sess:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                total_resource_slots={},
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=0,
                allowed_vfolder_hosts={},
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def sample_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for user repository",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def sample_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def another_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create another test resource policy for update tests"""
        policy_name = f"test-policy-2-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=20,
                max_quota_scope_size=BinarySize.finite_from_str("20GiB"),
                max_session_count_per_model_session=10,
                max_customized_image_count=5,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def another_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create another test domain for update tests"""
        domain_name = f"test-domain-2-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Another test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def sample_user_row(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain_name: str,
        sample_resource_policy_name: str,
    ) -> AsyncGenerator[UserRow, None]:
        """Create sample user row for testing"""
        user_uuid = uuid.uuid4()
        password_info = create_test_password_info("test_password")

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="Test User",
                description="Test user for repository tests",
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=sample_domain_name,
                role=UserRole.USER,
                resource_policy=sample_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()
            await db_sess.refresh(user)

        yield user

    @pytest.fixture
    async def another_user_row(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain_name: str,
        sample_resource_policy_name: str,
    ) -> AsyncGenerator[UserRow, None]:
        """Create another user row for conflict tests"""
        user_uuid = uuid.uuid4()
        password_info = create_test_password_info("test_password")

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"anotheruser-{user_uuid.hex[:8]}",
                email=f"another-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="Another Test User",
                description="Another test user for conflict tests",
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=sample_domain_name,
                role=UserRole.USER,
                resource_policy=sample_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()
            await db_sess.refresh(user)

        yield user

    @pytest.fixture
    async def user_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[UserRepository, None]:
        """Create UserRepository instance with database"""
        repo = UserRepository(db=db_with_cleanup)
        yield repo

    @pytest.fixture
    def sample_user_creator(
        self,
        sample_domain_name: str,
        sample_resource_policy_name: str,
    ) -> Creator[UserRow]:
        """Create sample user creator for creation"""
        password_info = create_test_password_info("new_password")
        unique_suffix = uuid.uuid4().hex[:8]
        spec = UserCreatorSpec(
            username=f"newuser-{unique_suffix}",
            email=f"newuser-{unique_suffix}@example.com",
            password=password_info,
            need_password_change=False,
            full_name="New User",
            description="New User Description",
            status=UserStatus.ACTIVE,
            domain_name=sample_domain_name,
            role=UserRole.USER,
            resource_policy=sample_resource_policy_name,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )
        return Creator(spec=spec)

    # ============ Get User Tests ============

    async def test_get_by_email_validated_success(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test successful user retrieval by email"""
        result = await user_repository.get_by_email_validated(sample_user_row.email)

        assert result is not None
        assert isinstance(result, UserData)
        assert result.email == sample_user_row.email
        assert result.username == sample_user_row.username
        assert result.uuid == sample_user_row.uuid
        assert result.role == sample_user_row.role

    async def test_get_by_email_validated_not_found(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Test user retrieval when user not found"""
        with pytest.raises(UserNotFound):
            await user_repository.get_by_email_validated("nonexistent@example.com")

    async def test_get_by_email_validated_access_denied(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user retrieval when access is denied"""
        # Note: Current implementation doesn't check access for get_by_email_validated
        # This test documents expected behavior if access control is added
        result = await user_repository.get_by_email_validated(sample_user_row.email)

        # Current implementation returns the user regardless of access
        assert result is not None
        assert isinstance(result, UserData)

    async def test_get_user_by_uuid_success(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test successful user retrieval by UUID"""
        result = await user_repository.get_user_by_uuid(sample_user_row.uuid)

        assert result is not None
        assert isinstance(result, UserData)
        assert result.uuid == sample_user_row.uuid
        assert result.email == sample_user_row.email

    async def test_get_user_by_uuid_not_found(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Test user retrieval by UUID when user not found"""
        with pytest.raises(UserNotFound):
            await user_repository.get_user_by_uuid(uuid.uuid4())

    # ============ Create User Tests ============

    async def test_create_user_validated_success(
        self,
        user_repository: UserRepository,
        sample_user_creator: Creator[UserRow],
        default_keypair_resource_policy: str,
    ) -> None:
        """Test successful user creation"""
        spec = sample_user_creator.spec
        assert isinstance(spec, UserCreatorSpec)
        result = await user_repository.create_user_validated(sample_user_creator, group_ids=[])

        assert result is not None
        assert result.user.email == spec.email
        assert result.user.username == spec.username
        assert result.user.role == spec.role
        assert result.user.domain_name == spec.domain_name
        assert result.keypair is not None
        assert result.keypair.access_key is not None

    async def test_create_user_validated_failure(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
        sample_domain_name: str,
        sample_resource_policy_name: str,
    ) -> None:
        """Test user creation failure scenarios"""
        password_info = create_test_password_info("new_password")

        # Test 1: Domain does not exist
        creator_bad_domain = Creator(
            spec=UserCreatorSpec(
                username=f"newuser-{uuid.uuid4().hex[:8]}",
                email=f"newuser-{uuid.uuid4().hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="New User",
                description="Test user",
                status=UserStatus.ACTIVE,
                domain_name="nonexistent-domain",
                role=UserRole.USER,
                resource_policy=sample_resource_policy_name,
                allowed_client_ip=None,
                totp_activated=False,
                sudo_session_enabled=False,
                container_uid=None,
                container_main_gid=None,
                container_gids=None,
            )
        )

        with pytest.raises(UserCreationBadRequest, match="Domain.*does not exist"):
            await user_repository.create_user_validated(creator_bad_domain, group_ids=[])

        # Test 2: User with same email already exists
        creator_dup_email = Creator(
            spec=UserCreatorSpec(
                username=f"different-username-{uuid.uuid4().hex[:8]}",
                email=sample_user_row.email,  # Same email as existing user
                password=password_info,
                need_password_change=False,
                full_name="Duplicate Email User",
                description="Test user",
                status=UserStatus.ACTIVE,
                domain_name=sample_domain_name,
                role=UserRole.USER,
                resource_policy=sample_resource_policy_name,
                allowed_client_ip=None,
                totp_activated=False,
                sudo_session_enabled=False,
                container_uid=None,
                container_main_gid=None,
                container_gids=None,
            )
        )

        with pytest.raises(UserConflict, match="User with email.*or username.*already exists"):
            await user_repository.create_user_validated(creator_dup_email, group_ids=[])

        # Test 3: User with same username already exists
        creator_dup_username = Creator(
            spec=UserCreatorSpec(
                username=sample_user_row.username,  # Same username as existing user
                email=f"different-email-{uuid.uuid4().hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="Duplicate Username User",
                description="Test user",
                status=UserStatus.ACTIVE,
                domain_name=sample_domain_name,
                role=UserRole.USER,
                resource_policy=sample_resource_policy_name,
                allowed_client_ip=None,
                totp_activated=False,
                sudo_session_enabled=False,
                container_uid=None,
                container_main_gid=None,
                container_gids=None,
            )
        )

        with pytest.raises(UserConflict, match="User with email.*or username.*already exists"):
            await user_repository.create_user_validated(creator_dup_username, group_ids=[])

    # ============ Update User Tests ============

    async def test_update_user_validated_success(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test successful user update"""
        updater_spec = UserUpdaterSpec(
            full_name=OptionalState.update("Updated Name"),
            description=OptionalState.update("Updated Description"),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_row.email)

        result = await user_repository.update_user_validated(
            email=sample_user_row.email,
            updater=updater,
            requester_uuid=None,
        )

        assert result is not None
        assert isinstance(result, UserData)
        assert result.full_name == "Updated Name"
        assert result.description == "Updated Description"

    async def test_update_user_validated_not_found(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Test user update when user not found"""
        updater_spec = UserUpdaterSpec(
            full_name=OptionalState.update("Updated Name"),
        )
        updater = Updater(spec=updater_spec, pk_value="nonexistent@example.com")

        with pytest.raises(UserNotFound):
            await user_repository.update_user_validated(
                email="nonexistent@example.com",
                updater=updater,
                requester_uuid=None,
            )

    async def test_update_user_validated_access_denied(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user update when access is denied"""
        # Note: Current implementation doesn't validate access in update_user_validated
        # Access control is expected to be handled at a higher level
        pass

    async def test_update_user_validated_username_conflict(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
        another_user_row: UserRow,
    ) -> None:
        """Test user update fails when username is already taken by another user"""
        # Try to update sample_user's username to another_user's username
        updater_spec = UserUpdaterSpec(
            username=OptionalState.update(another_user_row.username),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_row.email)

        with pytest.raises(
            UserModificationBadRequest, match="Username.*is already taken by another user"
        ):
            await user_repository.update_user_validated(
                email=sample_user_row.email,
                updater=updater,
                requester_uuid=None,
            )

    async def test_update_user_validated_domain_not_found(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user update fails when domain does not exist"""
        updater_spec = UserUpdaterSpec(
            domain_name=OptionalState.update("nonexistent-domain"),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_row.email)

        with pytest.raises(UserModificationBadRequest, match="Domain.*does not exist"):
            await user_repository.update_user_validated(
                email=sample_user_row.email,
                updater=updater,
                requester_uuid=None,
            )

    async def test_update_user_validated_resource_policy_not_found(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user update fails when resource policy does not exist"""
        updater_spec = UserUpdaterSpec(
            resource_policy=OptionalState.update("nonexistent-policy"),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_row.email)

        with pytest.raises(UserModificationBadRequest, match="Resource policy.*does not exist"):
            await user_repository.update_user_validated(
                email=sample_user_row.email,
                updater=updater,
                requester_uuid=None,
            )

    async def test_update_user_validated_same_username_no_conflict(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user update succeeds when updating to the same username"""
        # Update with the same username should not cause conflict
        updater_spec = UserUpdaterSpec(
            username=OptionalState.update(sample_user_row.username),
            full_name=OptionalState.update("Updated Name"),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_row.email)

        result = await user_repository.update_user_validated(
            email=sample_user_row.email,
            updater=updater,
            requester_uuid=None,
        )

        assert result is not None
        assert result.username == sample_user_row.username
        assert result.full_name == "Updated Name"

    async def test_update_user_validated_domain_change_success(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
        another_domain_name: str,
    ) -> None:
        """Test user update succeeds when changing to valid domain"""
        updater_spec = UserUpdaterSpec(
            domain_name=OptionalState.update(another_domain_name),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_row.email)

        result = await user_repository.update_user_validated(
            email=sample_user_row.email,
            updater=updater,
            requester_uuid=None,
        )

        assert result is not None
        assert result.domain_name == another_domain_name

    async def test_update_user_validated_resource_policy_change_success(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
        another_resource_policy_name: str,
    ) -> None:
        """Test user update succeeds when changing to valid resource policy"""
        updater_spec = UserUpdaterSpec(
            resource_policy=OptionalState.update(another_resource_policy_name),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_row.email)

        result = await user_repository.update_user_validated(
            email=sample_user_row.email,
            updater=updater,
            requester_uuid=None,
        )

        assert result is not None
        assert result.resource_policy == another_resource_policy_name

    async def test_update_user_validated_status_change(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user status update"""
        updater_spec = UserUpdaterSpec(
            status=OptionalState.update(UserStatus.INACTIVE),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_row.email)

        result = await user_repository.update_user_validated(
            email=sample_user_row.email,
            updater=updater,
            requester_uuid=None,
        )

        assert result is not None
        assert result.status == UserStatus.INACTIVE.value

    # ============ Soft Delete User Tests ============

    async def test_soft_delete_user_validated_success(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test successful user soft deletion"""
        await user_repository.soft_delete_user_validated(
            email=sample_user_row.email,
            requester_uuid=None,
        )

        # Verify user status is changed to DELETED
        result = await user_repository.get_by_email_validated(sample_user_row.email)
        assert result.status == UserStatus.DELETED.value

    # ============ Statistics and Validation Tests ============

    async def test_get_user_time_binned_monthly_stats(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user monthly statistics retrieval"""
        # Mock valkey client since we don't have a real one in tests
        mock_valkey_client = MagicMock(spec=ValkeyStatClient)

        # The method should return empty list when no stats available
        result = await user_repository.get_user_time_binned_monthly_stats(
            user_uuid=sample_user_row.uuid,
            valkey_stat_client=mock_valkey_client,
        )

        # Result should be a list (possibly empty)
        assert isinstance(result, list)

    def test_validate_user_access_owner(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user access validation for owner"""
        # Test owner access
        result = user_repository._validate_user_access(sample_user_row, sample_user_row.uuid)
        assert result is True

    def test_validate_user_access_admin(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user access validation for admin"""
        # Test admin access (None requester_uuid means admin)
        result = user_repository._validate_user_access(sample_user_row, None)
        assert result is True

    def test_validate_user_access_other_user(
        self,
        user_repository: UserRepository,
        sample_user_row: UserRow,
    ) -> None:
        """Test user access validation for other user"""
        # Test other user access
        other_user_uuid = uuid.uuid4()
        result = user_repository._validate_user_access(sample_user_row, other_user_uuid)
        # Current implementation allows all access
        assert result is True

    def test_user_data_conversion(
        self,
        sample_user_row: UserRow,
    ) -> None:
        """Test UserData conversion from UserRow"""
        user_data = UserData.from_row(sample_user_row)

        assert user_data.uuid == sample_user_row.uuid
        assert user_data.username == sample_user_row.username
        assert user_data.email == sample_user_row.email
        assert user_data.full_name == sample_user_row.full_name
        assert user_data.role == sample_user_row.role
        assert user_data.status == sample_user_row.status.value
        assert user_data.domain_name == sample_user_row.domain_name
