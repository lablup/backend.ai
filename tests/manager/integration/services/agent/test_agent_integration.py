import asyncio
from uuid import uuid4

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.services.agent.actions.get_watcher_status import GetWatcherStatusAction
from ai.backend.manager.services.agent.actions.recalculate_usage import RecalculateUsageAction
from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_start import (
    WatcherAgentStartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_stop import (
    WatcherAgentStopAction,
)


@pytest.mark.asyncio
async def test_sync_agent_registry_with_existing_agent(
    processors,
    create_test_agent,
    mock_agent_registry_sync,
):
    """Test sync_agent_registry when agent exists in database"""
    # Create an agent in the database
    agent_id = await create_test_agent()

    # Create and process the action
    action = SyncAgentRegistryAction(agent_id=agent_id)
    result = await processors.sync_agent_registry.wait_for_complete(action)

    # Verify the result
    assert result is not None
    assert result.agent_data is not None
    assert result.agent_data.id == agent_id
    assert result.agent_data.status == AgentStatus.ALIVE

    # Verify backward compatibility
    assert result.entity_id() == str(agent_id)

    # Verify the registry sync was called
    mock_agent_registry_sync.assert_called_once_with(agent_id)


@pytest.mark.asyncio
async def test_sync_agent_registry_with_nonexistent_agent(
    processors,
    mock_agent_registry_sync,
):
    """Test sync_agent_registry when agent doesn't exist"""
    # Use a random agent ID that doesn't exist
    nonexistent_id = AgentId(str(uuid4()))

    action = SyncAgentRegistryAction(agent_id=nonexistent_id)
    result = await processors.sync_agent_registry.wait_for_complete(action)

    # Should return None when agent doesn't exist
    assert result is not None
    assert result.agent_data is None
    assert result.entity_id() is None

    # Verify the registry sync was called
    mock_agent_registry_sync.assert_called_once_with(nonexistent_id)


@pytest.mark.asyncio
async def test_get_watcher_status(
    processors,
    mock_watcher_communication,
):
    """Test get_watcher_status action"""
    mock_session_instance, _ = mock_watcher_communication

    action = GetWatcherStatusAction(agent_id=AgentId(str(uuid4())))
    result = await processors.get_watcher_status.wait_for_complete(action)

    assert result is not None
    assert result.resp == {"success": True}


@pytest.mark.asyncio
async def test_watcher_operations(
    processors,
    mock_watcher_communication,
):
    """Test start, stop, and restart watcher operations"""
    mock_session_instance, _ = mock_watcher_communication

    # Test start watcher
    start_action = WatcherAgentStartAction(agent_id=AgentId(str(uuid4())))
    start_result = await processors.watcher_agent_start.wait_for_complete(start_action)
    assert start_result is not None
    assert start_result.resp == {"success": True}

    # Test restart watcher
    restart_action = WatcherAgentRestartAction(agent_id=AgentId(str(uuid4())))
    restart_result = await processors.watcher_agent_restart.wait_for_complete(restart_action)
    assert restart_result is not None
    assert restart_result.resp == {"success": True}

    # Test stop watcher
    stop_action = WatcherAgentStopAction(agent_id=AgentId(str(uuid4())))
    stop_result = await processors.watcher_agent_stop.wait_for_complete(stop_action)
    assert stop_result is not None
    assert stop_result.resp == {"success": True}

    # Verify all calls were made
    assert mock_session_instance.post.call_count == 3


@pytest.mark.asyncio
async def test_recalculate_usage(
    processors,
    mock_agent_recalc_usage,
):
    """Test recalculate_usage action"""
    # The action doesn't require parameters
    action = RecalculateUsageAction()
    result = await processors.recalculate_usage.wait_for_complete(action)

    # Should complete successfully
    assert result is not None

    # Verify the recalc was called
    mock_agent_recalc_usage.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_watcher_operations(
    processors,
    mock_watcher_with_delay,
):
    """Test that concurrent watcher operations are handled correctly"""
    mock_session_instance, _ = mock_watcher_with_delay

    # Execute multiple operations concurrently
    tasks = [
        processors.get_watcher_status.wait_for_complete(
            GetWatcherStatusAction(agent_id=AgentId(str(uuid4())))
        ),
        processors.watcher_agent_start.wait_for_complete(
            WatcherAgentStartAction(agent_id=AgentId(str(uuid4())))
        ),
        processors.watcher_agent_restart.wait_for_complete(
            WatcherAgentRestartAction(agent_id=AgentId(str(uuid4())))
        ),
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(r is not None and r.resp == {"success": True} for r in results)


@pytest.mark.asyncio
async def test_error_handling_in_watcher_communication(
    processors,
    mock_watcher_with_error,
):
    """Test error handling when watcher communication fails"""
    action = GetWatcherStatusAction(agent_id=AgentId(str(uuid4())))

    # Should raise the exception up to the processor
    with pytest.raises(Exception, match="Connection failed"):
        await processors.get_watcher_status.wait_for_complete(action)
