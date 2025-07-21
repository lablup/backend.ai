import pytest

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.user_resource_policy.processors import UserResourcePolicyProcessors
from ai.backend.manager.services.user_resource_policy.service import UserResourcePolicyService


@pytest.fixture
def processors(
    database_fixture,
    database_engine,
) -> UserResourcePolicyProcessors:
    """Create UserResourcePolicyProcessors instance with real dependencies for integration testing"""
    repository = UserResourcePolicyRepository(database_engine)

    service = UserResourcePolicyService(
        user_resource_policy_repository=repository,
    )

    # Use a simple implementation that doesn't require mocking
    class TestActionMonitor(ActionMonitor):
        async def notify(self, *args, **kwargs):
            pass

    return UserResourcePolicyProcessors(
        service=service,
        action_monitors=[TestActionMonitor()],
    )
