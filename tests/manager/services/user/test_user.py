"""
Simple tests for User Service functionality based on test scenarios.
Tests the core user service actions to verify compatibility with test scenarios.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserInfoContext
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user.admin_repository import AdminUserRepository
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.services.user.actions.admin_month_stats import AdminMonthStatsAction
from ai.backend.manager.services.user.actions.create_user import CreateUserAction
from ai.backend.manager.services.user.actions.delete_user import DeleteUserAction
from ai.backend.manager.services.user.actions.modify_user import ModifyUserAction
from ai.backend.manager.services.user.actions.purge_user import PurgeUserAction
from ai.backend.manager.services.user.actions.user_month_stats import UserMonthStatsAction
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.types import OptionalState


class TestUserServiceCompatibility:
    """Test compatibility of user service with test scenarios."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for testing."""
        storage_manager = MagicMock(spec=StorageSessionManager)
        valkey_client = MagicMock(spec=ValkeyStatClient)
        agent_registry = MagicMock()
        user_repository = MagicMock(spec=UserRepository)
        admin_user_repository = MagicMock(spec=AdminUserRepository)
        action_monitor = MagicMock(spec=ActionMonitor)

        return {
            "storage_manager": storage_manager,
            "valkey_client": valkey_client,
            "agent_registry": agent_registry,
            "user_repository": user_repository,
            "admin_user_repository": admin_user_repository,
            "action_monitor": action_monitor,
        }

    @pytest.fixture
    def user_service(self, mock_dependencies):
        """Create UserService instance with mocked dependencies."""
        return UserService(
            storage_manager=mock_dependencies["storage_manager"],
            valkey_stat_client=mock_dependencies["valkey_client"],
            agent_registry=mock_dependencies["agent_registry"],
            user_repository=mock_dependencies["user_repository"],
            admin_user_repository=mock_dependencies["admin_user_repository"],
        )

    @pytest.fixture
    def user_processors(self, user_service, mock_dependencies):
        """Create UserProcessors instance."""
        return UserProcessors(
            user_service=user_service,
            action_monitors=[mock_dependencies["action_monitor"]],
        )

    @pytest.mark.asyncio
    async def test_create_user_action_structure(self, user_service, mock_dependencies):
        """Test that CreateUserAction has the expected structure from test scenarios."""
        # Mock successful user creation
        mock_user_data = MagicMock()
        mock_user_data.email = "test@example.com"
        mock_user_data.username = "testuser"
        mock_user_data.role = UserRole.USER
        mock_user_data.status = UserStatus.ACTIVE

        mock_dependencies["user_repository"].create_user_validated = AsyncMock(
            return_value=mock_user_data
        )
        password_info = PasswordInfo(
            password="SecurePass123!",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )
        # Test 1.1: Normal user creation
        action = CreateUserAction(
            creator=Creator(
                spec=UserCreatorSpec(
                    email="test@example.com",
                    password=password_info,
                    username="testuser",
                    full_name="Test User",
                    role=UserRole.USER,
                    domain_name="default",
                    need_password_change=False,
                    resource_policy="default-user-policy",
                    status=UserStatus.ACTIVE,
                )
            ),
        )

        await user_service.create_user(action)
        mock_dependencies["user_repository"].create_user_validated.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_with_container_config(self, user_service, mock_dependencies):
        """Test 1.5: Container UID/GID configuration support."""
        mock_user_data = MagicMock()
        mock_dependencies["user_repository"].create_user_validated = AsyncMock(
            return_value=mock_user_data
        )
        password_info = PasswordInfo(
            password="ContainerPass123!",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )
        action = CreateUserAction(
            creator=Creator(
                spec=UserCreatorSpec(
                    email="container@example.com",
                    password=password_info,
                    username="containeruser",
                    need_password_change=False,
                    domain_name="default",
                    container_uid=2000,
                    container_main_gid=2000,
                    container_gids=[2000, 2001],
                )
            ),
        )

        await user_service.create_user(action)

        # Verify container settings were passed to repository
        call_args = mock_dependencies["user_repository"].create_user_validated.call_args
        user_data = call_args[0][0]
        assert user_data.spec.container_uid == 2000
        assert user_data.spec.container_main_gid == 2000
        assert user_data.spec.container_gids == [2000, 2001]

    @pytest.mark.asyncio
    async def test_modify_user_action_structure(self, user_service, mock_dependencies):
        """Test that ModifyUserAction supports the expected modifications."""
        mock_user_data = MagicMock()
        mock_user_data.full_name = "Updated Name"
        mock_user_data.role = UserRole.ADMIN

        mock_dependencies["user_repository"].update_user_validated = AsyncMock(
            return_value=mock_user_data
        )

        # Test 2.1: Basic information modification
        action = ModifyUserAction(
            email="user@example.com",
            updater=Updater(
                spec=UserUpdaterSpec(
                    full_name=OptionalState.update("Updated Name"),
                    description=OptionalState.update("Senior Developer"),
                ),
                pk_value="user@example.com",
            ),
        )

        await user_service.modify_user(action)
        mock_dependencies["user_repository"].update_user_validated.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_action_structure(self, user_service, mock_dependencies):
        """Test that DeleteUserAction works as expected."""
        mock_dependencies["user_repository"].soft_delete_user_validated = AsyncMock()

        action = DeleteUserAction(email="user@example.com")
        await user_service.delete_user(action)

        mock_dependencies["user_repository"].soft_delete_user_validated.assert_called_once_with(
            email="user@example.com",
            requester_uuid=None,
        )

    @pytest.mark.asyncio
    async def test_purge_user_action_structure(self, user_service, mock_dependencies):
        """Test that PurgeUserAction handles the expected scenarios."""
        # Mock user data
        mock_user_data = MagicMock()
        mock_user_data.uuid = "test-uuid"
        mock_dependencies["admin_user_repository"].get_by_email_force = AsyncMock(
            return_value=mock_user_data
        )

        # Mock other required methods
        mock_dependencies[
            "admin_user_repository"
        ].check_user_vfolder_mounted_to_active_kernels_force = AsyncMock(return_value=False)
        mock_dependencies["admin_user_repository"].retrieve_active_sessions_force = AsyncMock(
            return_value=[]
        )
        mock_dependencies["admin_user_repository"].delete_endpoints_force = AsyncMock()
        mock_dependencies["admin_user_repository"].delete_user_vfolders_force = AsyncMock()
        mock_dependencies["admin_user_repository"].purge_user_force = AsyncMock()

        action = PurgeUserAction(
            email="user@example.com",
            user_info_ctx=UserInfoContext(
                uuid="test-uuid",
                email="user@example.com",
                main_access_key="test-key",
            ),
        )

        await user_service.purge_user(action)
        mock_dependencies["admin_user_repository"].purge_user_force.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_month_stats_action_structure(self, user_service, mock_dependencies):
        """Test that UserMonthStatsAction works as expected."""
        mock_stats = {"cpu_time": 3600, "memory_usage": 2048}
        mock_dependencies["user_repository"].get_user_time_binned_monthly_stats = AsyncMock(
            return_value=mock_stats
        )

        # Use a valid UUID format instead of "test-user-id"
        import uuid

        test_user_uuid = str(uuid.uuid4())
        action = UserMonthStatsAction(user_id=test_user_uuid)

        result = await user_service.user_month_stats(action)

        assert result.stats == mock_stats
        mock_dependencies["user_repository"].get_user_time_binned_monthly_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_month_stats_action_structure(self, user_service, mock_dependencies):
        """Test that AdminMonthStatsAction works as expected."""
        mock_stats = {"total_users": 100, "total_cpu_time": 360000}
        mock_dependencies[
            "admin_user_repository"
        ].get_admin_time_binned_monthly_stats_force = AsyncMock(return_value=mock_stats)

        action = AdminMonthStatsAction()

        result = await user_service.admin_month_stats(action)

        assert result.stats == mock_stats
        mock_dependencies[
            "admin_user_repository"
        ].get_admin_time_binned_monthly_stats_force.assert_called_once()

    def test_user_creator_fields(self):
        """Test that UserCreator has all expected fields from test scenarios."""
        # Test that UserCreator can be created with all scenario fields
        password_info = PasswordInfo(
            password="password123",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=100_000,
            salt_size=32,
        )
        creator = Creator(
            spec=UserCreatorSpec(
                email="test@example.com",
                password=password_info,
                username="testuser",
                full_name="Test User",
                description="Test Description",
                need_password_change=False,
                domain_name="default",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                allowed_client_ip=["192.168.1.0/24"],
                totp_activated=False,
                resource_policy="default-policy",
                sudo_session_enabled=False,
                # group_ids is not part of UserCreatorSpec
                container_uid=2000,
                container_main_gid=2000,
                container_gids=[2000, 2001],
            )
        )

        assert creator.spec.email == "test@example.com"
        assert creator.spec.container_uid == 2000
        assert creator.spec.container_main_gid == 2000
        assert creator.spec.container_gids == [2000, 2001]
        assert creator.spec.allowed_client_ip == ["192.168.1.0/24"]
        assert creator.spec.resource_policy == "default-policy"
        assert creator.spec.sudo_session_enabled is False

    def test_user_updater_spec_fields(self):
        """Test that UserUpdaterSpec supports expected modification fields."""
        spec = UserUpdaterSpec(
            full_name=OptionalState.update("Updated Name"),
            description=OptionalState.update("Updated Description"),
            role=OptionalState.update(UserRole.ADMIN),
            status=OptionalState.update(UserStatus.INACTIVE),
            totp_activated=OptionalState.update(True),
            need_password_change=OptionalState.update(True),
            sudo_session_enabled=OptionalState.update(True),
        )

        # Test that all fields are properly set
        assert spec.full_name.optional_value() == "Updated Name"
        assert spec.description.optional_value() == "Updated Description"
        assert spec.role.optional_value() == UserRole.ADMIN
        assert spec.status.optional_value() == UserStatus.INACTIVE
        assert spec.totp_activated.optional_value() is True
        assert spec.need_password_change.optional_value() is True
        assert spec.sudo_session_enabled.optional_value() is True
