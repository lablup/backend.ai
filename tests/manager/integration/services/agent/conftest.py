import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import yarl

from ai.backend.common.auth import PublicKey
from ai.backend.common.types import AgentId, BinarySize, ResourceSlot
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService


@pytest.fixture
def mock_http_session():
    """Mock HTTP session for agent watcher communication"""
    mock_resp = MagicMock()
    mock_resp.json = AsyncMock(return_value={"success": True})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session_instance = MagicMock()
    mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_instance.__aexit__ = AsyncMock(return_value=None)
    mock_session_instance.get = MagicMock(return_value=mock_resp)
    mock_session_instance.post = MagicMock(return_value=mock_resp)
    mock_session_instance.close = AsyncMock()

    return mock_session_instance, mock_resp


@pytest.fixture
def mock_watcher_info():
    """Mock watcher info for agent service"""
    return {
        "addr": yarl.URL("http://localhost:6009"),
        "token": "test-token",
    }


@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing"""
    return {
        "id": AgentId("00000000-0000-0000-0000-000000000001"),
        "scaling_group": "default",
        "status": AgentStatus.ALIVE,
        "status_changed": datetime.now(timezone.utc),
        "region": "us-east-1",
        "architecture": "x86_64",
        "addr": "10.0.0.1:6001",
        "public_host": "agent1.example.com",
        "public_key": PublicKey(b"1234567890123456789012345678901234567890"),
        "available_slots": ResourceSlot({
            "cpu": Decimal("24"),
            "mem": BinarySize.from_str("32G"),
        }),
        "occupied_slots": ResourceSlot({
            "cpu": Decimal("8"),
            "mem": BinarySize.from_str("16G"),
        }),
        "version": "24.03.0",
        "compute_plugins": [],
        "schedulable": True,
        "lost_at": None,
        "first_contact": datetime.now(timezone.utc),
    }


@pytest.fixture
async def create_test_agent(database_engine, sample_agent_data):
    """Factory fixture to create test agents in database"""
    created_agents = []

    async def _create_agent(**overrides):
        agent_data = {**sample_agent_data}
        agent_data.update(overrides)

        if "id" not in overrides:
            agent_data["id"] = AgentId(str(uuid4()))

        async with database_engine.begin_session() as db_session:
            agent = AgentRow(**agent_data)
            db_session.add(agent)
            await db_session.commit()
            created_agents.append(agent.id)
            return agent.id

    yield _create_agent

    # Cleanup
    if created_agents:
        async with database_engine.begin_session() as db_session:
            import sqlalchemy as sa

            await db_session.execute(sa.delete(AgentRow).where(AgentRow.id.in_(created_agents)))
            await db_session.commit()


@pytest.fixture
async def agent_repository(database_engine) -> AgentRepository:
    """Create AgentRepository instance with real database for integration testing"""
    return AgentRepository(db=database_engine)


@pytest.fixture
def mock_config_provider():
    """Mock config provider for agent service"""
    config_provider = MagicMock()
    config_provider.get = AsyncMock()
    return config_provider


@pytest.fixture
async def agent_service(
    database_fixture,
    etcd_fixture,
    registry_ctx,
    agent_repository,
    mock_config_provider,
) -> AgentService:
    """Create AgentService instance with real dependencies for integration testing"""
    agent_registry, _, _, _, _, _, _ = registry_ctx

    return AgentService(
        etcd=etcd_fixture,
        agent_registry=agent_registry,
        config_provider=mock_config_provider,
        agent_repository=agent_repository,
    )


@pytest.fixture
def processors(agent_service) -> AgentProcessors:
    """Create AgentProcessors instance for integration testing"""
    return AgentProcessors(
        service=agent_service,
        action_monitors=[],
    )


@pytest.fixture
def mock_agent_registry_sync(mocker, agent_service):
    """Mock agent registry sync to avoid actual agent registry calls"""
    mock_sync = mocker.patch.object(agent_service._agent_registry, "sync_agent_kernel_registry")
    mock_sync.return_value = None
    return mock_sync


@pytest.fixture
def mock_agent_recalc_usage(mocker, agent_service):
    """Mock agent registry recalc_resource_usage"""
    mock_recalc = mocker.patch.object(agent_service._agent_registry, "recalc_resource_usage")
    mock_recalc.return_value = None
    return mock_recalc


@pytest.fixture
def mock_watcher_communication(mocker, agent_service, mock_watcher_info, mock_http_session):
    """Setup complete watcher communication mocking"""
    mock_session_instance, mock_resp = mock_http_session

    mock_info = mocker.patch.object(agent_service, "_get_watcher_info", new_callable=AsyncMock)
    mock_info.return_value = mock_watcher_info

    mock_session = mocker.patch("aiohttp.ClientSession")
    mock_session.return_value = mock_session_instance

    return mock_session_instance, mock_resp


@pytest.fixture
def mock_watcher_with_delay(mocker, agent_service, mock_watcher_info):
    """Mock watcher communication with configurable delay for testing concurrency"""

    async def delayed_response(*args):
        await asyncio.sleep(0.1)
        return {"success": True}

    mock_resp = MagicMock()
    mock_resp.json = AsyncMock(side_effect=delayed_response)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session_instance = MagicMock()
    mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_instance.__aexit__ = AsyncMock(return_value=None)
    mock_session_instance.get = MagicMock(return_value=mock_resp)
    mock_session_instance.post = MagicMock(return_value=mock_resp)
    mock_session_instance.close = AsyncMock()

    mock_info = mocker.patch.object(agent_service, "_get_watcher_info", new_callable=AsyncMock)
    mock_info.return_value = mock_watcher_info

    mock_session = mocker.patch("aiohttp.ClientSession")
    mock_session.return_value = mock_session_instance

    return mock_session_instance, mock_resp


@pytest.fixture
def mock_watcher_with_error(mocker, agent_service, mock_watcher_info):
    """Mock watcher communication to simulate errors"""
    mock_resp = MagicMock()
    mock_resp.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session_instance = MagicMock()
    mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_instance.__aexit__ = AsyncMock(return_value=None)
    mock_session_instance.get = MagicMock(return_value=mock_resp)
    mock_session_instance.close = AsyncMock()

    mock_info = mocker.patch.object(agent_service, "_get_watcher_info", new_callable=AsyncMock)
    mock_info.return_value = mock_watcher_info

    mock_session = mocker.patch("aiohttp.ClientSession")
    mock_session.return_value = mock_session_instance

    return mock_session_instance
