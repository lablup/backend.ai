from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService

from .fixtures import AGENT_DATA_FIXTURE


@pytest.fixture
def mock_etcd():
    """Mock etcd client"""
    mock = MagicMock()
    mock.get = AsyncMock()
    mock.put = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry"""
    mock = MagicMock(spec=AgentRegistry)
    mock.recalc_agent_resource_occupancy = AsyncMock()
    mock.update_scaling_group = AsyncMock()
    return mock


@pytest.fixture
def mock_config_provider():
    """Mock config provider"""
    mock = MagicMock()
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    return mock


@pytest.fixture
def mock_agent_repository():
    """Mock agent repository"""
    mock = AsyncMock(spec=AgentRepository)
    # Default behavior: return test agent data
    mock.get_by_id = AsyncMock(return_value=AGENT_DATA_FIXTURE)
    return mock


@pytest.fixture
def agent_service(
    mock_etcd,
    mock_agent_registry,
    mock_config_provider,
    mock_agent_repository,
) -> AgentService:
    """Create AgentService with mocked dependencies"""
    return AgentService(
        etcd=mock_etcd,
        agent_registry=mock_agent_registry,
        config_provider=mock_config_provider,
        agent_repository=mock_agent_repository,
    )


@pytest.fixture
def agent_processors(agent_service) -> AgentProcessors:
    """Create AgentProcessors for testing"""
    return AgentProcessors(
        service=agent_service,
        action_monitors=[],
    )


@pytest.fixture
def mock_watcher_info(mocker, agent_service):
    """Mock the _get_watcher_info method on agent service"""
    mock = mocker.patch.object(
        agent_service,
        "_get_watcher_info",
        new_callable=AsyncMock,
    )
    # Return default watcher info
    mock.return_value = {
        "addr": yarl.URL("http://localhost:6009"),
        "token": "test-token",
    }
    return mock
