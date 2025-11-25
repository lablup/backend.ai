"""
Unit tests for user_resource_policy service with mocked dependencies.
These tests verify that the service methods work correctly with mocked repositories.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import UserResourcePolicyNotFound
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
    UserResourcePolicyModifier,
)
from ai.backend.manager.services.user_resource_policy.processors import UserResourcePolicyProcessors
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService
from ai.backend.manager.services.user_resource_policy.types import (
    UserResourcePolicyCreator,
)
from ai.backend.manager.types import OptionalState


@pytest.fixture
def mock_repository():
    """Mock repository for testing"""
    mock_repo = AsyncMock(spec=UserResourcePolicyRepository)
    return mock_repo


@pytest.fixture
def mock_action_monitor():
    """Mock action monitor for testing"""
    return MagicMock(spec=ActionMonitor)


@pytest.fixture
def service(mock_repository):
    """Service instance with mocked repository"""
    return UserResourcePolicyService(
        user_resource_policy_repository=mock_repository,
    )


@pytest.fixture
def processors(service, mock_action_monitor):
    """Processors instance with mocked dependencies"""
    return UserResourcePolicyProcessors(
        service=service,
        action_monitors=[mock_action_monitor],
    )


def test_user_resource_policy_creator_fields_to_store():
    """Test that UserResourcePolicyCreator properly serializes fields to store"""
    creator = UserResourcePolicyCreator(
        name="test-policy",
        max_vfolder_count=10,
        max_quota_scope_size=1000000,
        max_session_count_per_model_session=5,
        max_vfolder_size=500000,  # This should be excluded
        max_customized_image_count=3,
    )

    fields = creator.fields_to_store()

    # Check that all expected fields are present
    assert fields["name"] == "test-policy"
    assert fields["max_vfolder_count"] == 10
    assert fields["max_quota_scope_size"] == 1000000
    assert fields["max_session_count_per_model_session"] == 5
    assert fields["max_customized_image_count"] == 3

    # Check that deprecated field is not included
    assert "max_vfolder_size" not in fields


def test_user_resource_policy_creator_fields_to_store_with_none_values():
    """Test that UserResourcePolicyCreator handles None values correctly"""
    creator = UserResourcePolicyCreator(
        name="minimal-policy",
        max_vfolder_count=None,
        max_quota_scope_size=None,
        max_session_count_per_model_session=None,
        max_vfolder_size=None,
        max_customized_image_count=None,
    )

    fields = creator.fields_to_store()

    # Check that all expected fields are present, even if None
    assert fields["name"] == "minimal-policy"
    assert fields["max_vfolder_count"] is None
    assert fields["max_quota_scope_size"] is None
    assert fields["max_session_count_per_model_session"] is None
    assert fields["max_customized_image_count"] is None

    # Check that deprecated field is not included
    assert "max_vfolder_size" not in fields


def test_user_resource_policy_modifier_fields_to_update():
    """Test that UserResourcePolicyModifier properly serializes fields to update"""
    modifier = UserResourcePolicyModifier(
        max_vfolder_count=OptionalState.update(20),
        max_quota_scope_size=OptionalState.update(2000000),
        max_session_count_per_model_session=OptionalState.update(None),
        max_customized_image_count=OptionalState.nop(),
    )

    fields = modifier.fields_to_update()

    # Check that updated fields are present
    assert fields["max_vfolder_count"] == 20
    assert fields["max_quota_scope_size"] == 2000000

    # Check that fields set to None are present with None value
    assert fields["max_session_count_per_model_session"] is None

    # Check that nop fields are not present
    assert "max_customized_image_count" not in fields


def test_create_user_resource_policy_action():
    """Test CreateUserResourcePolicyAction structure"""
    creator = UserResourcePolicyCreator(
        name="test-policy",
        max_vfolder_count=10,
        max_quota_scope_size=1000000,
        max_session_count_per_model_session=5,
        max_vfolder_size=500000,
        max_customized_image_count=3,
    )

    action = CreateUserResourcePolicyAction(creator=creator)

    assert action.creator == creator
    assert action.entity_id() is None
    assert action.operation_type() == "create"


def test_modify_user_resource_policy_action():
    """Test ModifyUserResourcePolicyAction structure"""
    modifier = UserResourcePolicyModifier(
        max_vfolder_count=OptionalState.update(20),
    )

    action = ModifyUserResourcePolicyAction(
        name="test-policy",
        modifier=modifier,
    )

    assert action.name == "test-policy"
    assert action.modifier == modifier
    assert action.entity_id() is None
    assert action.operation_type() == "modify"


def test_delete_user_resource_policy_action():
    """Test DeleteUserResourcePolicyAction structure"""
    action = DeleteUserResourcePolicyAction(name="test-policy")

    assert action.name == "test-policy"
    assert action.entity_id() is None
    assert action.operation_type() == "delete"


@pytest.mark.asyncio
async def test_create_user_resource_policy_service(service, mock_repository):
    """Test create user resource policy service method"""
    # Setup mock return value
    expected_data = UserResourcePolicyData(
        name="test-policy",
        max_vfolder_count=10,
        max_quota_scope_size=1000000,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
    )
    mock_repository.create.return_value = expected_data

    # Create action
    creator = UserResourcePolicyCreator(
        name="test-policy",
        max_vfolder_count=10,
        max_quota_scope_size=1000000,
        max_session_count_per_model_session=5,
        max_vfolder_size=500000,  # This should be filtered out
        max_customized_image_count=3,
    )
    action = CreateUserResourcePolicyAction(creator=creator)

    # Execute service method
    result = await service.create_user_resource_policy(action)

    # Verify result
    assert result.user_resource_policy == expected_data

    # Verify repository was called with correct creator object
    mock_repository.create.assert_called_once()
    call_args = mock_repository.create.call_args[0][0]
    assert isinstance(call_args, UserResourcePolicyCreator)
    assert call_args.name == "test-policy"
    assert call_args.max_vfolder_count == 10
    assert call_args.max_quota_scope_size == 1000000
    assert call_args.max_session_count_per_model_session == 5
    assert call_args.max_customized_image_count == 3
    # Verify deprecated field is not included in fields_to_store
    fields_to_store = call_args.fields_to_store()
    assert "max_vfolder_size" not in fields_to_store


@pytest.mark.asyncio
async def test_modify_user_resource_policy_service(service, mock_repository):
    """Test modify user resource policy service method"""
    # Setup mock return value
    expected_data = UserResourcePolicyData(
        name="test-policy",
        max_vfolder_count=20,
        max_quota_scope_size=2000000,
        max_session_count_per_model_session=5,  # Unchanged
        max_customized_image_count=5,
    )
    mock_repository.update.return_value = expected_data

    # Create action
    modifier = UserResourcePolicyModifier(
        max_vfolder_count=OptionalState.update(20),
        max_quota_scope_size=OptionalState.update(2000000),
        max_session_count_per_model_session=OptionalState.nop(),
        max_customized_image_count=OptionalState.update(5),
    )
    action = ModifyUserResourcePolicyAction(
        name="test-policy",
        modifier=modifier,
    )

    # Execute service method
    result = await service.modify_user_resource_policy(action)

    # Verify result
    assert result.user_resource_policy == expected_data

    # Verify repository was called with correct modifier object
    mock_repository.update.assert_called_once()
    call_args = mock_repository.update.call_args[0]
    assert call_args[0] == "test-policy"
    assert isinstance(call_args[1], UserResourcePolicyModifier)

    # Verify modifier contains correct fields
    modifier_arg = call_args[1]
    assert modifier_arg.max_vfolder_count.value() == 20
    assert modifier_arg.max_quota_scope_size.value() == 2000000
    assert modifier_arg.max_customized_image_count.value() == 5

    # Verify fields_to_update only contains updated fields
    fields_to_update = modifier_arg.fields_to_update()
    assert fields_to_update == {
        "max_vfolder_count": 20,
        "max_quota_scope_size": 2000000,
        "max_customized_image_count": 5,
    }


@pytest.mark.asyncio
async def test_delete_user_resource_policy_service(service, mock_repository):
    """Test delete user resource policy service method"""
    # Setup mock return value
    expected_data = UserResourcePolicyData(
        name="test-policy",
        max_vfolder_count=10,
        max_quota_scope_size=1000000,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
    )
    mock_repository.delete.return_value = expected_data

    # Create action
    action = DeleteUserResourcePolicyAction(name="test-policy")

    # Execute service method
    result = await service.delete_user_resource_policy(action)

    # Verify result
    assert result.user_resource_policy == expected_data

    # Verify repository was called correctly
    mock_repository.delete.assert_called_once_with("test-policy")


@pytest.mark.asyncio
async def test_modify_non_existing_policy_raises_exception(service, mock_repository):
    """Test that modifying non-existing policy raises UserResourcePolicyNotFound"""
    # Setup mock to raise exception
    mock_repository.update.side_effect = UserResourcePolicyNotFound("Policy not found")

    # Create action
    modifier = UserResourcePolicyModifier(
        max_vfolder_count=OptionalState.update(20),
    )
    action = ModifyUserResourcePolicyAction(
        name="non-existing-policy",
        modifier=modifier,
    )

    # Execute and verify exception is raised
    with pytest.raises(UserResourcePolicyNotFound):
        await service.modify_user_resource_policy(action)


@pytest.mark.asyncio
async def test_delete_non_existing_policy_raises_exception(service, mock_repository):
    """Test that deleting non-existing policy raises UserResourcePolicyNotFound"""
    # Setup mock to raise exception
    mock_repository.delete.side_effect = UserResourcePolicyNotFound("Policy not found")

    # Create action
    action = DeleteUserResourcePolicyAction(name="non-existing-policy")

    # Execute and verify exception is raised
    with pytest.raises(UserResourcePolicyNotFound):
        await service.delete_user_resource_policy(action)


@pytest.mark.asyncio
async def test_processors_integration(processors, mock_repository):
    """Test that processors work correctly with the service"""
    # Setup mock return value
    expected_data = UserResourcePolicyData(
        name="processor-test",
        max_vfolder_count=15,
        max_quota_scope_size=1500000,
        max_session_count_per_model_session=7,
        max_customized_image_count=4,
    )
    mock_repository.create.return_value = expected_data

    # Create action
    creator = UserResourcePolicyCreator(
        name="processor-test",
        max_vfolder_count=15,
        max_quota_scope_size=1500000,
        max_session_count_per_model_session=7,
        max_vfolder_size=750000,
        max_customized_image_count=4,
    )
    action = CreateUserResourcePolicyAction(creator=creator)

    # Execute through processors
    result = await processors.create_user_resource_policy.wait_for_complete(action)

    # Verify result
    assert result.user_resource_policy == expected_data

    # Verify repository was called
    mock_repository.create.assert_called_once()
