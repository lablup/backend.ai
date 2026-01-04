"""
Unit tests for user_resource_policy service with mocked dependencies.
These tests verify that the service methods work correctly with mocked repositories.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import UserResourcePolicyNotFound
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user_resource_policy.creators import (
    UserResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.repositories.user_resource_policy.updaters import (
    UserResourcePolicyUpdaterSpec,
)
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.processors import (
    UserResourcePolicyProcessors,
)
from ai.backend.manager.services.user_resource_policy.service import (
    UserResourcePolicyService,
)
from ai.backend.manager.types import OptionalState

# ==================== Shared Fixtures ====================


@pytest.fixture
def mock_repository() -> MagicMock:
    """Mock repository for testing"""
    return MagicMock(spec=UserResourcePolicyRepository)


@pytest.fixture
def mock_action_monitor() -> MagicMock:
    """Mock action monitor for testing"""
    return MagicMock(spec=ActionMonitor)


@pytest.fixture
def service(mock_repository: MagicMock) -> UserResourcePolicyService:
    """Service instance with mocked repository"""
    return UserResourcePolicyService(
        user_resource_policy_repository=mock_repository,
    )


@pytest.fixture
def processors(
    service: UserResourcePolicyService,
    mock_action_monitor: MagicMock,
) -> UserResourcePolicyProcessors:
    """Processors instance with mocked dependencies"""
    return UserResourcePolicyProcessors(
        service=service,
        action_monitors=[mock_action_monitor],
    )


@pytest.fixture
def sample_policy_data() -> UserResourcePolicyData:
    """Create sample user resource policy data."""
    return UserResourcePolicyData(
        name="test-policy",
        max_vfolder_count=10,
        max_quota_scope_size=1000000,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
    )


# ==================== Action Structure Tests ====================


class TestActionStructure:
    """Test action dataclass structure without triggering mapper initialization."""

    def test_create_action_structure(self) -> None:
        """Test CreateUserResourcePolicyAction structure"""
        spec = UserResourcePolicyCreatorSpec(
            name="test-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1000000,
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )

        creator = Creator(spec=spec)
        action = CreateUserResourcePolicyAction(creator=creator)

        assert action.creator == creator
        assert action.entity_id() is None
        assert action.operation_type() == "create"

    def test_modify_action_structure(self) -> None:
        """Test ModifyUserResourcePolicyAction structure"""
        spec = UserResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(20),
        )
        updater = Updater(spec=spec, pk_value="test-policy")

        action = ModifyUserResourcePolicyAction(
            name="test-policy",
            updater=updater,
        )

        assert action.name == "test-policy"
        assert action.updater == updater
        assert action.entity_id() is None
        assert action.operation_type() == "modify"

    def test_delete_action_structure(self) -> None:
        """Test DeleteUserResourcePolicyAction structure"""
        action = DeleteUserResourcePolicyAction(name="test-policy")

        assert action.name == "test-policy"
        assert action.entity_id() is None
        assert action.operation_type() == "delete"


# ==================== UpdaterSpec Tests ====================


class TestUpdaterSpec:
    """Test UpdaterSpec build_values without triggering mapper initialization."""

    def test_build_values_with_updates(self) -> None:
        """Test that UserResourcePolicyUpdaterSpec properly serializes fields to update"""
        spec = UserResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(20),
            max_quota_scope_size=OptionalState.update(2000000),
            max_session_count_per_model_session=OptionalState.nop(),
            max_customized_image_count=OptionalState.nop(),
        )

        fields = spec.build_values()

        # Check that updated fields are present
        assert fields["max_vfolder_count"] == 20
        assert fields["max_quota_scope_size"] == 2000000

        # Check that nop fields are not present
        assert "max_session_count_per_model_session" not in fields
        assert "max_customized_image_count" not in fields


# ==================== Create Service Tests ====================


class TestCreateUserResourcePolicy:
    """Test cases for UserResourcePolicyService.create_user_resource_policy"""

    async def test_success(
        self,
        service: UserResourcePolicyService,
        mock_repository: MagicMock,
        sample_policy_data: UserResourcePolicyData,
    ) -> None:
        """Test create user resource policy service method"""
        mock_repository.create = AsyncMock(return_value=sample_policy_data)

        spec = UserResourcePolicyCreatorSpec(
            name="test-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1000000,
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )
        creator = Creator(spec=spec)
        action = CreateUserResourcePolicyAction(creator=creator)

        result = await service.create_user_resource_policy(action)

        assert result.user_resource_policy == sample_policy_data
        mock_repository.create.assert_called_once()
        call_args = mock_repository.create.call_args[0][0]
        assert isinstance(call_args.spec, UserResourcePolicyCreatorSpec)
        assert call_args.spec.name == "test-policy"
        assert call_args.spec.max_vfolder_count == 10
        assert call_args.spec.max_quota_scope_size == 1000000
        assert call_args.spec.max_session_count_per_model_session == 5
        assert call_args.spec.max_customized_image_count == 3


# ==================== Modify Service Tests ====================


class TestModifyUserResourcePolicy:
    """Test cases for UserResourcePolicyService.modify_user_resource_policy"""

    async def test_success(
        self,
        service: UserResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Test modify user resource policy service method"""
        expected_data = UserResourcePolicyData(
            name="test-policy",
            max_vfolder_count=20,
            max_quota_scope_size=2000000,
            max_session_count_per_model_session=5,
            max_customized_image_count=5,
        )
        mock_repository.update = AsyncMock(return_value=expected_data)

        spec = UserResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(20),
            max_quota_scope_size=OptionalState.update(2000000),
            max_session_count_per_model_session=OptionalState.nop(),
            max_customized_image_count=OptionalState.update(5),
        )
        updater = Updater(spec=spec, pk_value="test-policy")
        action = ModifyUserResourcePolicyAction(
            name="test-policy",
            updater=updater,
        )

        result = await service.modify_user_resource_policy(action)

        assert result.user_resource_policy == expected_data
        mock_repository.update.assert_called_once()
        call_args = mock_repository.update.call_args[0]
        assert isinstance(call_args[0], Updater)
        assert isinstance(call_args[0].spec, UserResourcePolicyUpdaterSpec)

        spec_arg = call_args[0].spec
        assert spec_arg.max_vfolder_count.value() == 20
        assert spec_arg.max_quota_scope_size.value() == 2000000
        assert spec_arg.max_customized_image_count.value() == 5

        build_values = spec_arg.build_values()
        assert build_values == {
            "max_vfolder_count": 20,
            "max_quota_scope_size": 2000000,
            "max_customized_image_count": 5,
        }

    async def test_not_found(
        self,
        service: UserResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that modifying non-existing policy raises UserResourcePolicyNotFound"""
        mock_repository.update = AsyncMock(
            side_effect=UserResourcePolicyNotFound("Policy not found")
        )

        spec = UserResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(20),
        )
        updater = Updater(spec=spec, pk_value="non-existing-policy")
        action = ModifyUserResourcePolicyAction(
            name="non-existing-policy",
            updater=updater,
        )

        with pytest.raises(UserResourcePolicyNotFound):
            await service.modify_user_resource_policy(action)


# ==================== Delete Service Tests ====================


class TestDeleteUserResourcePolicy:
    """Test cases for UserResourcePolicyService.delete_user_resource_policy"""

    async def test_success(
        self,
        service: UserResourcePolicyService,
        mock_repository: MagicMock,
        sample_policy_data: UserResourcePolicyData,
    ) -> None:
        """Test delete user resource policy service method"""
        mock_repository.delete = AsyncMock(return_value=sample_policy_data)

        action = DeleteUserResourcePolicyAction(name="test-policy")

        result = await service.delete_user_resource_policy(action)

        assert result.user_resource_policy == sample_policy_data
        mock_repository.delete.assert_called_once_with("test-policy")

    async def test_not_found(
        self,
        service: UserResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that deleting non-existing policy raises UserResourcePolicyNotFound"""
        mock_repository.delete = AsyncMock(
            side_effect=UserResourcePolicyNotFound("Policy not found")
        )

        action = DeleteUserResourcePolicyAction(name="non-existing-policy")

        with pytest.raises(UserResourcePolicyNotFound):
            await service.delete_user_resource_policy(action)


# ==================== Processors Integration Tests ====================


class TestProcessorsIntegration:
    """Test that processors work correctly with the service"""

    async def test_create_via_processors(
        self,
        processors: UserResourcePolicyProcessors,
        mock_repository: MagicMock,
    ) -> None:
        """Test that processors work correctly with the service"""
        expected_data = UserResourcePolicyData(
            name="processor-test",
            max_vfolder_count=15,
            max_quota_scope_size=1500000,
            max_session_count_per_model_session=7,
            max_customized_image_count=4,
        )
        mock_repository.create = AsyncMock(return_value=expected_data)

        spec = UserResourcePolicyCreatorSpec(
            name="processor-test",
            max_vfolder_count=15,
            max_quota_scope_size=1500000,
            max_session_count_per_model_session=7,
            max_customized_image_count=4,
        )
        creator = Creator(spec=spec)
        action = CreateUserResourcePolicyAction(creator=creator)

        result = await processors.create_user_resource_policy.wait_for_complete(action)

        assert result.user_resource_policy == expected_data
        mock_repository.create.assert_called_once()
