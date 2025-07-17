"""
Integration tests for user_resource_policy service with real database.
These tests verify that the service methods work correctly with actual database connections.
"""

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy import select

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models import UserResourcePolicyRow
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

# Mark all tests in this module
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
async def db_session(database_engine, database_fixture):
    """Database session for testing"""
    async with database_engine.begin_session() as session:
        yield session


@pytest.fixture
async def repository(db_session):
    """Real repository instance with database connection"""
    return UserResourcePolicyRepository(db_session)


@pytest.fixture
def action_monitor():
    """Action monitor for testing"""

    # Use a simple implementation that doesn't require mocking
    class TestActionMonitor(ActionMonitor):
        async def notify(self, *args, **kwargs):
            pass

    return TestActionMonitor()


@pytest.fixture
def service(repository):
    """Service instance with real repository"""
    return UserResourcePolicyService(
        user_resource_policy_repository=repository,
    )


@pytest.fixture
def processors(service, action_monitor):
    """Processors instance with real dependencies"""
    return UserResourcePolicyProcessors(
        service=service,
        action_monitors=[action_monitor],
    )


async def test_create_user_resource_policy_service(service, db_session):
    """Test create user resource policy service method"""
    # Create action
    policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
    creator = UserResourcePolicyCreator(
        name=policy_name,
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
    assert result.user_resource_policy.name == policy_name
    assert result.user_resource_policy.max_vfolder_count == 10
    assert result.user_resource_policy.max_quota_scope_size == 1000000
    assert result.user_resource_policy.max_session_count_per_model_session == 5
    assert result.user_resource_policy.max_customized_image_count == 3

    # Verify policy exists in database
    query = select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == policy_name)
    row = await db_session.scalar(query)
    assert row is not None
    assert row.name == policy_name
    assert row.max_vfolder_count == 10

    # Clean up
    await db_session.execute(
        sa.delete(UserResourcePolicyRow).where(UserResourcePolicyRow.name == policy_name)
    )
    await db_session.commit()


async def test_modify_user_resource_policy_service(service, db_session):
    """Test modify user resource policy service method"""
    # First create a policy to modify
    policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
    await db_session.execute(
        sa.insert(UserResourcePolicyRow).values(
            name=policy_name,
            max_vfolder_count=10,
            max_quota_scope_size=1000000,
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )
    )
    await db_session.commit()

    # Create action
    modifier = UserResourcePolicyModifier(
        max_vfolder_count=OptionalState.update(20),
        max_quota_scope_size=OptionalState.update(2000000),
        max_session_count_per_model_session=OptionalState.nop(),
        max_customized_image_count=OptionalState.update(5),
    )
    action = ModifyUserResourcePolicyAction(
        name=policy_name,
        modifier=modifier,
    )

    # Execute service method
    result = await service.modify_user_resource_policy(action)

    # Verify result
    assert result.user_resource_policy.name == policy_name
    assert result.user_resource_policy.max_vfolder_count == 20
    assert result.user_resource_policy.max_quota_scope_size == 2000000
    assert result.user_resource_policy.max_session_count_per_model_session == 5  # Unchanged
    assert result.user_resource_policy.max_customized_image_count == 5

    # Verify changes in database
    query = select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == policy_name)
    row = await db_session.scalar(query)
    assert row is not None
    assert row.max_vfolder_count == 20
    assert row.max_quota_scope_size == 2000000

    # Clean up
    await db_session.execute(
        sa.delete(UserResourcePolicyRow).where(UserResourcePolicyRow.name == policy_name)
    )
    await db_session.commit()


async def test_delete_user_resource_policy_service(service, db_session):
    """Test delete user resource policy service method"""
    # First create a policy to delete
    policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
    await db_session.execute(
        sa.insert(UserResourcePolicyRow).values(
            name=policy_name,
            max_vfolder_count=10,
            max_quota_scope_size=1000000,
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )
    )
    await db_session.commit()

    # Create action
    action = DeleteUserResourcePolicyAction(name=policy_name)

    # Execute service method
    result = await service.delete_user_resource_policy(action)

    # Verify result
    assert result.user_resource_policy.name == policy_name
    assert result.user_resource_policy.max_vfolder_count == 10

    # Verify policy was deleted from database
    query = select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == policy_name)
    row = await db_session.scalar(query)
    assert row is None


async def test_modify_non_existing_policy_raises_exception(service):
    """Test that modifying non-existing policy raises ObjectNotFound"""
    # Create action for non-existing policy
    modifier = UserResourcePolicyModifier(
        max_vfolder_count=OptionalState.update(20),
    )
    action = ModifyUserResourcePolicyAction(
        name="non-existing-policy",
        modifier=modifier,
    )

    # Execute and verify exception is raised
    with pytest.raises(ObjectNotFound):
        await service.modify_user_resource_policy(action)


async def test_delete_non_existing_policy_raises_exception(service):
    """Test that deleting non-existing policy raises ObjectNotFound"""
    # Create action for non-existing policy
    action = DeleteUserResourcePolicyAction(name="non-existing-policy")

    # Execute and verify exception is raised
    with pytest.raises(ObjectNotFound):
        await service.delete_user_resource_policy(action)


async def test_processors_integration(processors, db_session):
    """Test that processors work correctly with the service"""
    # Create action
    policy_name = f"processor-test-{uuid.uuid4().hex[:8]}"
    creator = UserResourcePolicyCreator(
        name=policy_name,
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
    assert result.user_resource_policy.name == policy_name
    assert result.user_resource_policy.max_vfolder_count == 15
    assert result.user_resource_policy.max_quota_scope_size == 1500000

    # Verify policy exists in database
    query = select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == policy_name)
    row = await db_session.scalar(query)
    assert row is not None

    # Clean up
    await db_session.execute(
        sa.delete(UserResourcePolicyRow).where(UserResourcePolicyRow.name == policy_name)
    )
    await db_session.commit()
