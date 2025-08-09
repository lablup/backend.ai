import pytest

from ai.backend.manager.services.agent.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
)


@pytest.mark.asyncio
async def test_recalculate_usage_success(agent_processors):
    """Test successful recalculate usage action"""
    action = RecalculateUsageAction()
    result = await agent_processors.recalculate_usage.wait_for_complete(action)

    # Should complete successfully
    assert result is not None
    assert isinstance(result, RecalculateUsageActionResult)


@pytest.mark.asyncio
async def test_recalculate_usage_error(agent_processors, agent_service, mocker):
    """Test recalculate usage with error"""
    # Mock the agent registry method to raise error
    mocker.patch.object(
        agent_service._agent_registry,
        "recalc_resource_usage",
        side_effect=RuntimeError("Recalculation failed"),
    )

    action = RecalculateUsageAction()

    # Should propagate the error
    with pytest.raises(RuntimeError, match="Recalculation failed"):
        await agent_processors.recalculate_usage.wait_for_complete(action)
