"""
Mock-based unit tests for UserService.

Tests verify service layer business logic using mocked repositories.
Repository tests verify actual DB operations separately.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.user.types import (
    UserCreateResultData,
    UserData,
    UserInfoContext,
    UserRole,
    UserStatus,
)
from ai.backend.manager.errors.user import UserNotFound, UserPurgeFailure
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user.admin_repository import AdminUserRepository
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.services.user.actions.create_user import (
    CreateUserAction,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
)
from ai.backend.manager.services.user.actions.modify_user import (
    ModifyUserAction,
)
from ai.backend.manager.services.user.actions.purge_user import (
    PurgeUserAction,
)
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.types import OptionalState


class TestCreateUser:
    """Tests for UserService.create_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_admin_user_repository(self) -> MagicMock:
        return MagicMock(spec=AdminUserRepository)

    @pytest.fixture
    def service(
        self,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
    ) -> UserService:
        return UserService(
            storage_manager=MagicMock(),
            valkey_stat_client=MagicMock(),
            agent_registry=MagicMock(),
            user_repository=mock_user_repository,
            admin_user_repository=mock_admin_user_repository,
        )

    @pytest.fixture
    def sample_user_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def sample_user_data(self, sample_user_uuid: uuid.UUID) -> UserData:
        return UserData(
            id=sample_user_uuid,
            uuid=sample_user_uuid,
            username="newuser",
            email="new@example.com",
            need_password_change=False,
            full_name="Test User",
            description="Test user description",
            is_active=True,
            status=UserStatus.ACTIVE,
            status_info=None,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            domain_name="default",
            role=UserRole.USER,
            resource_policy="default",
            allowed_client_ip=None,
            totp_activated=False,
            totp_activated_at=None,
            sudo_session_enabled=False,
            main_access_key="TESTKEY1234567890",
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )

    @pytest.fixture
    def sample_keypair_data(self, sample_user_uuid: uuid.UUID) -> KeyPairData:
        return KeyPairData(
            user_id=sample_user_uuid,
            access_key=AccessKey("TESTKEY1234567890"),
            secret_key=SecretKey("test-secret-key"),
            is_active=True,
            is_admin=False,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            resource_policy_name="default",
            rate_limit=60000,
            ssh_public_key=None,
            ssh_private_key=None,
            dotfiles="",
            bootstrap_script="",
        )

    @pytest.fixture
    def sample_password_info(self) -> PasswordInfo:
        return PasswordInfo(
            password="password123",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

    @pytest.fixture
    def sample_create_result(
        self,
        sample_user_data: UserData,
        sample_keypair_data: KeyPairData,
    ) -> UserCreateResultData:
        return UserCreateResultData(user=sample_user_data, keypair=sample_keypair_data)

    async def test_create_with_valid_data_returns_user(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        sample_user_data: UserData,
        sample_create_result: UserCreateResultData,
        sample_password_info: PasswordInfo,
    ) -> None:
        """Create user with valid data should return created user."""
        mock_user_repository.create_user_validated = AsyncMock(return_value=sample_create_result)

        action = CreateUserAction(
            creator=Creator(
                spec=UserCreatorSpec(
                    email=sample_user_data.email,
                    username=sample_user_data.username,
                    password=sample_password_info,
                    need_password_change=sample_user_data.need_password_change,
                    domain_name=sample_user_data.domain_name,
                )
            ),
            group_ids=None,
        )

        result = await service.create_user(action)

        assert result.data.user.email == sample_user_data.email
        mock_user_repository.create_user_validated.assert_called_once_with(
            action.creator, action.group_ids
        )

    async def test_create_with_group_ids_passes_to_repository(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        sample_user_data: UserData,
        sample_create_result: UserCreateResultData,
        sample_password_info: PasswordInfo,
    ) -> None:
        """Create user with group_ids should pass them to repository."""
        mock_user_repository.create_user_validated = AsyncMock(return_value=sample_create_result)

        group_ids = ["group1", "group2"]
        action = CreateUserAction(
            creator=Creator(
                spec=UserCreatorSpec(
                    email=sample_user_data.email,
                    username=sample_user_data.username,
                    password=sample_password_info,
                    need_password_change=sample_user_data.need_password_change,
                    domain_name=sample_user_data.domain_name,
                )
            ),
            group_ids=group_ids,
        )

        result = await service.create_user(action)

        assert result.data is not None
        mock_user_repository.create_user_validated.assert_called_once_with(
            action.creator, group_ids
        )

    async def test_create_with_duplicate_email_raises_error(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        sample_password_info: PasswordInfo,
    ) -> None:
        """Create user with duplicate email should raise InvalidAPIParameters."""
        mock_user_repository.create_user_validated = AsyncMock(
            side_effect=InvalidAPIParameters("User with this email already exists")
        )

        action = CreateUserAction(
            creator=Creator(
                spec=UserCreatorSpec(
                    email="existing@example.com",
                    username="existinguser",
                    password=sample_password_info,
                    need_password_change=False,
                    domain_name="default",
                )
            ),
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_user(action)


class TestModifyUser:
    """Tests for UserService.modify_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_admin_user_repository(self) -> MagicMock:
        return MagicMock(spec=AdminUserRepository)

    @pytest.fixture
    def service(
        self,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
    ) -> UserService:
        return UserService(
            storage_manager=MagicMock(),
            valkey_stat_client=MagicMock(),
            agent_registry=MagicMock(),
            user_repository=mock_user_repository,
            admin_user_repository=mock_admin_user_repository,
        )

    @pytest.fixture
    def modified_user_data(self) -> UserData:
        user_uuid = uuid.uuid4()
        return UserData(
            id=user_uuid,
            uuid=user_uuid,
            username="modified_username",
            email="test@example.com",
            need_password_change=False,
            full_name="Test User",
            description="Test user description",
            is_active=True,
            status=UserStatus.ACTIVE,
            status_info=None,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            domain_name="default",
            role=UserRole.USER,
            resource_policy="default",
            allowed_client_ip=None,
            totp_activated=False,
            totp_activated_at=None,
            sudo_session_enabled=False,
            main_access_key="TESTKEY1234567890",
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )

    async def test_modify_with_valid_data_returns_updated_user(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        modified_user_data: UserData,
    ) -> None:
        """Modify user with valid data should return updated user."""
        mock_user_repository.update_user_validated = AsyncMock(return_value=modified_user_data)

        action = ModifyUserAction(
            email=modified_user_data.email,
            updater=Updater(
                spec=UserUpdaterSpec(
                    username=OptionalState.update(modified_user_data.username),
                ),
                pk_value=modified_user_data.email,
            ),
        )

        result = await service.modify_user(action)

        assert result.data is not None
        assert result.data.username == modified_user_data.username
        mock_user_repository.update_user_validated.assert_called_once_with(
            email=modified_user_data.email,
            updater=action.updater,
            requester_uuid=None,
        )

    async def test_modify_nonexistent_user_raises_error(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Modify non-existent user should raise UserNotFound."""
        mock_user_repository.update_user_validated = AsyncMock(
            side_effect=UserNotFound("User not found")
        )

        action = ModifyUserAction(
            email="nonexistent@example.com",
            updater=Updater(
                spec=UserUpdaterSpec(
                    username=OptionalState.update("new_username"),
                ),
                pk_value="nonexistent@example.com",
            ),
        )

        with pytest.raises(UserNotFound):
            await service.modify_user(action)


class TestDeleteUser:
    """Tests for UserService.delete_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_admin_user_repository(self) -> MagicMock:
        return MagicMock(spec=AdminUserRepository)

    @pytest.fixture
    def service(
        self,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
    ) -> UserService:
        return UserService(
            storage_manager=MagicMock(),
            valkey_stat_client=MagicMock(),
            agent_registry=MagicMock(),
            user_repository=mock_user_repository,
            admin_user_repository=mock_admin_user_repository,
        )

    async def test_delete_existing_user_returns_success(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Delete existing user should return success result."""
        mock_user_repository.soft_delete_user_validated = AsyncMock(return_value=None)

        action = DeleteUserAction(email="test@example.com")

        result = await service.delete_user(action)

        assert result is not None
        mock_user_repository.soft_delete_user_validated.assert_called_once_with(
            email="test@example.com",
            requester_uuid=None,
        )

    async def test_delete_nonexistent_user_raises_error(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
    ) -> None:
        """Delete non-existent user should raise UserNotFound."""
        mock_user_repository.soft_delete_user_validated = AsyncMock(
            side_effect=UserNotFound("User not found")
        )

        action = DeleteUserAction(email="nonexistent@example.com")

        with pytest.raises(UserNotFound):
            await service.delete_user(action)


class TestPurgeUser:
    """Tests for UserService.purge_user"""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_admin_user_repository(self) -> MagicMock:
        return MagicMock(spec=AdminUserRepository)

    @pytest.fixture
    def mock_agent_registry(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def service(
        self,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
        mock_agent_registry: MagicMock,
    ) -> UserService:
        return UserService(
            storage_manager=MagicMock(),
            valkey_stat_client=MagicMock(),
            agent_registry=mock_agent_registry,
            user_repository=mock_user_repository,
            admin_user_repository=mock_admin_user_repository,
        )

    @pytest.fixture
    def purge_user_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def purge_user_data(self, purge_user_uuid: uuid.UUID) -> UserData:
        return UserData(
            id=purge_user_uuid,
            uuid=purge_user_uuid,
            username="purgeuser",
            email="purge@example.com",
            need_password_change=False,
            full_name="Purge User",
            description="User to be purged",
            is_active=True,
            status=UserStatus.ACTIVE,
            status_info=None,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            domain_name="default",
            role=UserRole.USER,
            resource_policy="default",
            allowed_client_ip=None,
            totp_activated=False,
            totp_activated_at=None,
            sudo_session_enabled=False,
            main_access_key="TESTKEY1234567890",
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )

    @pytest.fixture
    def admin_user_info_ctx(self) -> UserInfoContext:
        return UserInfoContext(
            uuid=uuid.uuid4(),
            email="admin@example.com",
            main_access_key=AccessKey("ADMINKEY123456789"),
        )

    async def test_purge_user_succeeds_without_active_vfolders(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
        purge_user_data: UserData,
        admin_user_info_ctx: UserInfoContext,
    ) -> None:
        """Purge user without active vfolder mounts should succeed."""
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=purge_user_data)
        mock_admin_user_repository.check_user_vfolder_mounted_to_active_kernels_force = AsyncMock(
            return_value=False
        )
        mock_admin_user_repository.retrieve_active_sessions_force = AsyncMock(return_value=[])
        mock_admin_user_repository.delete_endpoints_force = AsyncMock(return_value=None)
        mock_admin_user_repository.delete_user_vfolders_force = AsyncMock(return_value=None)
        mock_admin_user_repository.purge_user_force = AsyncMock(return_value=None)

        action = PurgeUserAction(
            user_info_ctx=admin_user_info_ctx,
            email=purge_user_data.email,
        )

        result = await service.purge_user(action)

        assert result is not None
        mock_admin_user_repository.purge_user_force.assert_called_once_with(purge_user_data.email)

    async def test_purge_user_fails_with_active_vfolder_mounts(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
        purge_user_data: UserData,
        admin_user_info_ctx: UserInfoContext,
    ) -> None:
        """Purge user with active vfolder mounts should raise UserPurgeFailure."""
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=purge_user_data)
        mock_admin_user_repository.check_user_vfolder_mounted_to_active_kernels_force = AsyncMock(
            return_value=True
        )

        action = PurgeUserAction(
            user_info_ctx=admin_user_info_ctx,
            email=purge_user_data.email,
        )

        with pytest.raises(UserPurgeFailure):
            await service.purge_user(action)

    async def test_purge_user_with_shared_vfolders_migration(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
        purge_user_uuid: uuid.UUID,
        purge_user_data: UserData,
        admin_user_info_ctx: UserInfoContext,
    ) -> None:
        """Purge user with shared vfolders migration enabled should migrate vfolders."""
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=purge_user_data)
        mock_admin_user_repository.check_user_vfolder_mounted_to_active_kernels_force = AsyncMock(
            return_value=False
        )
        mock_admin_user_repository.migrate_shared_vfolders_force = AsyncMock(return_value=None)
        mock_admin_user_repository.retrieve_active_sessions_force = AsyncMock(return_value=[])
        mock_admin_user_repository.delete_endpoints_force = AsyncMock(return_value=None)
        mock_admin_user_repository.delete_user_vfolders_force = AsyncMock(return_value=None)
        mock_admin_user_repository.purge_user_force = AsyncMock(return_value=None)

        action = PurgeUserAction(
            user_info_ctx=admin_user_info_ctx,
            email=purge_user_data.email,
            purge_shared_vfolders=OptionalState.update(True),
        )

        result = await service.purge_user(action)

        assert result is not None
        mock_admin_user_repository.migrate_shared_vfolders_force.assert_called_once_with(
            deleted_user_uuid=purge_user_uuid,
            target_user_uuid=admin_user_info_ctx.uuid,
            target_user_email=admin_user_info_ctx.email,
        )

    async def test_purge_user_with_endpoint_delegation(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
        purge_user_uuid: uuid.UUID,
        purge_user_data: UserData,
        admin_user_info_ctx: UserInfoContext,
    ) -> None:
        """Purge user with endpoint delegation enabled should delegate endpoints."""
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=purge_user_data)
        mock_admin_user_repository.check_user_vfolder_mounted_to_active_kernels_force = AsyncMock(
            return_value=False
        )
        mock_admin_user_repository.delegate_endpoint_ownership_force = AsyncMock(return_value=None)
        mock_admin_user_repository.retrieve_active_sessions_force = AsyncMock(return_value=[])
        mock_admin_user_repository.delete_endpoints_force = AsyncMock(return_value=None)
        mock_admin_user_repository.delete_user_vfolders_force = AsyncMock(return_value=None)
        mock_admin_user_repository.purge_user_force = AsyncMock(return_value=None)

        action = PurgeUserAction(
            user_info_ctx=admin_user_info_ctx,
            email=purge_user_data.email,
            delegate_endpoint_ownership=OptionalState.update(True),
        )

        result = await service.purge_user(action)

        assert result is not None
        mock_admin_user_repository.delegate_endpoint_ownership_force.assert_called_once_with(
            user_uuid=purge_user_uuid,
            target_user_uuid=admin_user_info_ctx.uuid,
            target_main_access_key=admin_user_info_ctx.main_access_key,
        )
        # When delegating, delete_endpoints_force should be called with delete_destroyed_only=True
        mock_admin_user_repository.delete_endpoints_force.assert_called_once_with(
            user_uuid=purge_user_uuid,
            delete_destroyed_only=True,
        )

    async def test_purge_user_without_endpoint_delegation_deletes_all_endpoints(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        mock_admin_user_repository: MagicMock,
        purge_user_uuid: uuid.UUID,
        purge_user_data: UserData,
        admin_user_info_ctx: UserInfoContext,
    ) -> None:
        """Purge user without endpoint delegation should delete all endpoints."""
        mock_user_repository.get_by_email_validated = AsyncMock(return_value=purge_user_data)
        mock_admin_user_repository.check_user_vfolder_mounted_to_active_kernels_force = AsyncMock(
            return_value=False
        )
        mock_admin_user_repository.retrieve_active_sessions_force = AsyncMock(return_value=[])
        mock_admin_user_repository.delete_endpoints_force = AsyncMock(return_value=None)
        mock_admin_user_repository.delete_user_vfolders_force = AsyncMock(return_value=None)
        mock_admin_user_repository.purge_user_force = AsyncMock(return_value=None)

        action = PurgeUserAction(
            user_info_ctx=admin_user_info_ctx,
            email=purge_user_data.email,
        )

        result = await service.purge_user(action)

        assert result is not None
        mock_admin_user_repository.delete_endpoints_force.assert_called_once_with(
            user_uuid=purge_user_uuid,
            delete_destroyed_only=False,
        )

    async def test_purge_nonexistent_user_raises_error(
        self,
        service: UserService,
        mock_user_repository: MagicMock,
        admin_user_info_ctx: UserInfoContext,
    ) -> None:
        """Purge non-existent user should raise UserNotFound."""
        mock_user_repository.get_by_email_validated = AsyncMock(
            side_effect=UserNotFound("User not found")
        )

        action = PurgeUserAction(
            user_info_ctx=admin_user_info_ctx,
            email="nonexistent@example.com",
        )

        with pytest.raises(UserNotFound):
            await service.purge_user(action)
