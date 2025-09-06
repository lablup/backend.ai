"""
Tests for AuthRepository functionality.
Tests the repository layer with mocked database operations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.auth.types import GroupMembershipData, UserData
from ai.backend.manager.errors.auth import (
    GroupMembershipNotFoundError,
    UserCreationError,
)
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.auth.repository import AuthRepository


@pytest.fixture
def mock_db_engine():
    """Create mocked database engine."""
    return MagicMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def mock_db_conn(mock_db_engine):
    """Create mocked database connection with transaction support."""
    mock_conn = AsyncMock()
    mock_db_engine.begin.return_value.__aenter__.return_value = mock_conn
    return mock_conn


@pytest.fixture
def mock_db_session(mock_db_engine):
    """Create mocked database session."""
    mock_session = AsyncMock()
    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    return mock_session


@pytest.fixture
def mock_db_readonly_conn(mock_db_engine):
    """Create mocked readonly database connection."""
    mock_conn = AsyncMock()
    mock_db_engine.begin_readonly.return_value.__aenter__.return_value = mock_conn
    return mock_conn


class TestAuthRepository:
    """Test cases for AuthRepository"""

    @pytest.fixture
    def auth_repository(self, mock_db_engine):
        """Create AuthRepository instance with mocked database"""
        return AuthRepository(db=mock_db_engine)

    @pytest.fixture
    def sample_user_row(self):
        """Create sample user row for testing"""
        return MagicMock(
            uuid=UUID("12345678-1234-5678-1234-567812345678"),
            username="testuser",
            email="test@example.com",
            password="hashed_password",
            need_password_change=False,
            full_name="Test User",
            description="Test Description",
            status=UserStatus.ACTIVE,
            status_info="admin-requested",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            domain_name="default",
            role=UserRole.USER,
            resource_policy="default",
        )

    @pytest.mark.asyncio
    async def test_get_user_by_email_validated_success(
        self, auth_repository, mock_db_conn, sample_user_row, mocker
    ):
        """Test successful user retrieval by email"""
        mocker.patch.object(auth_repository, "_get_user_by_email", return_value=sample_user_row)

        result = await auth_repository.get_user_by_email_validated("test@example.com", "default")

        assert result is not None
        assert isinstance(result, UserData)
        assert result.uuid == sample_user_row.uuid
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email_validated_not_found(
        self, auth_repository, mock_db_conn, mocker
    ):
        """Test user retrieval by email when user not found"""
        mocker.patch.object(auth_repository, "_get_user_by_email", return_value=None)

        result = await auth_repository.get_user_by_email_validated(
            "nonexistent@example.com", "default"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_group_membership_validated_success(
        self, auth_repository, mock_db_conn, mocker
    ):
        """Test successful group membership retrieval"""
        group_id = UUID("87654321-4321-8765-4321-876543218765")
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        membership_data = GroupMembershipData(group_id=group_id, user_id=user_id)
        mocker.patch.object(auth_repository, "_get_group_membership", return_value=membership_data)

        result = await auth_repository.get_group_membership_validated(group_id, user_id)

        assert result == membership_data
        assert result.group_id == group_id
        assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_group_membership_validated_not_found(
        self, auth_repository, mock_db_conn, mocker
    ):
        """Test group membership retrieval when not found"""
        group_id = UUID("87654321-4321-8765-4321-876543218765")
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        mocker.patch.object(auth_repository, "_get_group_membership", return_value=None)

        with pytest.raises(GroupMembershipNotFoundError) as exc_info:
            await auth_repository.get_group_membership_validated(group_id, user_id)

        assert "No such project or you are not the member of it" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_email_exists_true(self, auth_repository, mock_db_conn):
        """Test email existence check when email exists"""
        # Mock query result
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(email="existing@example.com")
        mock_db_conn.execute.return_value = mock_result

        result = await auth_repository.check_email_exists("existing@example.com")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_email_exists_false(self, auth_repository, mock_db_conn):
        """Test email existence check when email doesn't exist"""
        # Mock query result
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db_conn.execute.return_value = mock_result

        result = await auth_repository.check_email_exists("nonexistent@example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_create_user_with_keypair_success(self, auth_repository, mock_db_conn):
        """Test successful user creation with keypair"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "hashed_password",
            "domain_name": "default",
            "full_name": "New User",
            "status": UserStatus.ACTIVE,
            "role": UserRole.USER,
        }
        keypair_data = {
            "user_id": "newuser@example.com",
            "access_key": "AKIANEWUSER123",
            "secret_key": "secretkey123",
            "is_active": True,
            "resource_policy": "default",
        }

        # Mock successful inserts
        mock_user_result = MagicMock()
        mock_user_result.rowcount = 1

        mock_user_row = MagicMock()
        mock_user_row.uuid = UUID("99999999-9999-9999-9999-999999999999")
        mock_user_row.email = "newuser@example.com"

        mock_group_row = MagicMock()
        mock_group_row.id = UUID("11111111-1111-1111-1111-111111111111")

        mock_db_conn.execute.side_effect = [
            mock_user_result,  # user insert
            MagicMock(first=MagicMock(return_value=mock_user_row)),  # user query
            MagicMock(),  # keypair insert
            MagicMock(first=MagicMock(return_value=mock_group_row)),  # group query
            MagicMock(),  # group association insert
        ]

        result = await auth_repository.create_user_with_keypair(
            user_data=user_data,
            keypair_data=keypair_data,
            group_name="default",
            domain_name="default",
        )

        assert result is not None
        assert result.uuid == mock_user_row.uuid
        assert result.email == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_create_user_with_keypair_failure(self, auth_repository, mock_db_conn):
        """Test user creation failure"""
        user_data = {"email": "fail@example.com"}
        keypair_data = {}

        # Mock failed insert
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db_conn.execute.return_value = mock_result

        with pytest.raises(UserCreationError):
            await auth_repository.create_user_with_keypair(
                user_data=user_data,
                keypair_data=keypair_data,
                group_name="default",
                domain_name="default",
            )

    @pytest.mark.asyncio
    async def test_update_user_full_name_validated(self, auth_repository, mock_db_conn):
        """Test updating user full name"""
        # Mock successful query and update
        mock_user_row = MagicMock(email="user@example.com")
        mock_db_conn.execute.side_effect = [
            MagicMock(first=MagicMock(return_value=mock_user_row)),  # select query
            MagicMock(),  # update query
        ]

        result = await auth_repository.update_user_full_name_validated(
            "user@example.com", "default", "New Full Name"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_password_validated(self, auth_repository, mock_db_conn):
        """Test updating user password"""
        password_info = PasswordInfo(
            password="new_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )
        await auth_repository.update_user_password_validated("user@example.com", password_info)

        # Verify execute was called (for update query)
        mock_db_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_user_and_keypairs_validated(self, auth_repository, mock_db_conn):
        """Test deactivating user and keypairs"""
        await auth_repository.deactivate_user_and_keypairs_validated("deactivate@example.com")

        # Verify two updates were executed (user and keypairs)
        assert mock_db_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_ssh_public_key_validated(self, auth_repository, mock_db_conn):
        """Test retrieving SSH public key"""
        # Mock query result
        mock_db_conn.scalar = AsyncMock(return_value="ssh-rsa AAAAB3NzaC1yc2E...")

        result = await auth_repository.get_ssh_public_key_validated("AKIA123456")

        assert result == "ssh-rsa AAAAB3NzaC1yc2E..."

    @pytest.mark.asyncio
    async def test_update_ssh_keypair_validated(self, auth_repository, mock_db_conn):
        """Test updating SSH keypair"""
        await auth_repository.update_ssh_keypair_validated(
            "AKIA123456",
            "ssh-rsa AAAAB3NzaC1yc2E...",
            "-----BEGIN RSA PRIVATE KEY-----\n...",
        )

        # Verify update was executed
        mock_db_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_credential_without_migration(
        self, auth_repository, mock_db_engine, mocker
    ):
        """Test credential validation without migration"""
        mock_check = mocker.patch(
            "ai.backend.manager.repositories.auth.repository.check_credential",
            return_value={
                "uuid": UUID("12345678-1234-5678-1234-567812345678"),
                "email": "user@example.com",
                "role": UserRole.USER,
                "status": UserStatus.ACTIVE,
            },
        )

        result = await auth_repository.check_credential_without_migration(
            "default", "user@example.com", "password"
        )

        assert result is not None
        assert result["email"] == "user@example.com"
        mock_check.assert_called_once_with(
            db=mock_db_engine,
            domain="default",
            email="user@example.com",
            password="password",
        )

    @pytest.mark.asyncio
    async def test_get_user_row_by_uuid_validated(self, auth_repository, mock_db_session, mocker):
        """Test getting user row by UUID"""
        user_uuid = UUID("12345678-1234-5678-1234-567812345678")

        mock_user_row = MagicMock(spec=UserRow)
        mocker.patch(
            "ai.backend.manager.models.user.UserRow.query_user_by_uuid",
            return_value=mock_user_row,
        )

        result = await auth_repository.get_user_row_by_uuid_validated(user_uuid)

        assert result == mock_user_row

    @pytest.mark.asyncio
    async def test_get_current_time_validated(self, auth_repository, mock_db_readonly_conn):
        """Test getting current time from database"""
        current_time = datetime.now()
        mock_db_readonly_conn.scalar = AsyncMock(return_value=current_time)

        result = await auth_repository.get_current_time_validated()

        assert result == current_time
