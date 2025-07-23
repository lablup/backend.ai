from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from ai.backend.manager.services.agent.actions.get_watcher_status import (
    GetWatcherStatusAction,
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

from .fixtures import TEST_AGENT_ID, WATCHER_STATUS_RESPONSE, WATCHER_SUCCESS_RESPONSE


@pytest.mark.asyncio
async def test_get_watcher_status(agent_processors, mock_watcher_info):
    """Test get_watcher_status action"""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=WATCHER_STATUS_RESPONSE)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch("ai.backend.manager.services.agent.service.aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        action = GetWatcherStatusAction(agent_id=TEST_AGENT_ID)
        result = await agent_processors.get_watcher_status.wait_for_complete(action)

        assert result is not None
        assert result.resp == WATCHER_STATUS_RESPONSE
        assert result.agent_id == TEST_AGENT_ID

        # Verify watcher info was fetched
        mock_watcher_info.assert_called_once_with(TEST_AGENT_ID)


@pytest.mark.asyncio
async def test_start_watcher(agent_processors, mock_watcher_info):
    """Test start watcher action"""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=WATCHER_SUCCESS_RESPONSE)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch("ai.backend.manager.services.agent.service.aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        action = WatcherAgentStartAction(agent_id=TEST_AGENT_ID)
        result = await agent_processors.watcher_agent_start.wait_for_complete(action)

        assert result is not None
        assert result.resp == WATCHER_SUCCESS_RESPONSE
        assert result.agent_id == TEST_AGENT_ID

        # Verify watcher info was fetched
        mock_watcher_info.assert_called_once_with(TEST_AGENT_ID)


@pytest.mark.asyncio
async def test_restart_watcher(agent_processors, mock_watcher_info):
    """Test restart watcher action"""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=WATCHER_SUCCESS_RESPONSE)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch("ai.backend.manager.services.agent.service.aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        action = WatcherAgentRestartAction(agent_id=TEST_AGENT_ID)
        result = await agent_processors.watcher_agent_restart.wait_for_complete(action)

        assert result is not None
        assert result.resp == WATCHER_SUCCESS_RESPONSE
        assert result.agent_id == TEST_AGENT_ID

        # Verify watcher info was fetched
        mock_watcher_info.assert_called_once_with(TEST_AGENT_ID)


@pytest.mark.asyncio
async def test_stop_watcher(agent_processors, mock_watcher_info):
    """Test stop watcher action"""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value=WATCHER_SUCCESS_RESPONSE)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch("ai.backend.manager.services.agent.service.aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        action = WatcherAgentStopAction(agent_id=TEST_AGENT_ID)
        result = await agent_processors.watcher_agent_stop.wait_for_complete(action)

        assert result is not None
        assert result.resp == WATCHER_SUCCESS_RESPONSE
        assert result.agent_id == TEST_AGENT_ID

        # Verify watcher info was fetched
        mock_watcher_info.assert_called_once_with(TEST_AGENT_ID)


@pytest.mark.asyncio
async def test_watcher_connection_error(agent_processors, mock_watcher_info):
    """Test error handling when watcher communication fails"""
    # Mock connection failure
    with patch("ai.backend.manager.services.agent.service.aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        # Create a mock that will fail when called as a context manager
        mock_get = MagicMock()
        mock_get.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_session_instance.get.return_value = mock_get
        mock_session.return_value = mock_session_instance

        action = GetWatcherStatusAction(agent_id=TEST_AGENT_ID)

        # Should raise the exception
        with pytest.raises(aiohttp.ClientError, match="Connection failed"):
            await agent_processors.get_watcher_status.wait_for_complete(action)
