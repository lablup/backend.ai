import pytest

from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
    SyncAgentRegistryActionResult,
)

from ..test_utils import TestScenario
from .fixtures import AGENT_DATA_FIXTURE, NONEXISTENT_AGENT_ID, TEST_AGENT_ID


@pytest.mark.parametrize(
    "scenario",
    [
        TestScenario.success(
            "Agent exists in database",
            SyncAgentRegistryAction(agent_id=TEST_AGENT_ID),
            SyncAgentRegistryActionResult(result=None, agent_data=AGENT_DATA_FIXTURE),
        ),
        TestScenario.success(
            "Agent does not exist in database",
            SyncAgentRegistryAction(agent_id=NONEXISTENT_AGENT_ID),
            SyncAgentRegistryActionResult(result=None, agent_data=None),
        ),
    ],
)
@pytest.mark.asyncio
async def test_sync_agent_registry(
    scenario: TestScenario[SyncAgentRegistryAction, SyncAgentRegistryActionResult],
    agent_processors,
    mock_agent_repository,
):
    # Setup mocks based on scenario
    if scenario.description == "Agent does not exist in database":
        mock_agent_repository.get_by_id.return_value = None

    async def execute_action(action: SyncAgentRegistryAction):
        return await agent_processors.sync_agent_registry.wait_for_complete(action)

    await scenario.test(execute_action)

    # Verify repository was called with correct agent ID
    mock_agent_repository.get_by_id.assert_called_once_with(scenario.input.agent_id)


@pytest.mark.asyncio
async def test_sync_agent_registry_entity_id(
    agent_processors,
    mock_agent_repository,
):
    """Test that entity_id is correctly extracted from result"""
    action = SyncAgentRegistryAction(agent_id=TEST_AGENT_ID)
    result = await agent_processors.sync_agent_registry.wait_for_complete(action)

    # Should return agent ID as entity ID
    assert result.entity_id() == str(TEST_AGENT_ID)


@pytest.mark.asyncio
async def test_sync_agent_registry_repository_error(
    agent_processors,
    mock_agent_repository,
):
    """Test error handling when repository fails"""
    # Setup repository to raise an error
    mock_agent_repository.get_by_id.side_effect = Exception("Database connection failed")

    action = SyncAgentRegistryAction(agent_id=TEST_AGENT_ID)

    # Should propagate the exception
    with pytest.raises(Exception, match="Database connection failed"):
        await agent_processors.sync_agent_registry.wait_for_complete(action)
