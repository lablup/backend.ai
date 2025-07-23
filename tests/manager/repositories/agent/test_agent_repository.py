from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import (
    AgentId,
    BinarySize,
    ResourceSlot,
)
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.services.agent.types import AgentData

# Test agent IDs
TEST_AGENT_ID = AgentId("00000000-0000-0000-0000-000000000001")
TEST_AGENT_ID_2 = AgentId("00000000-0000-0000-0000-000000000002")
NONEXISTENT_AGENT_ID = AgentId("99999999-9999-9999-9999-999999999999")

# Test scaling group
TEST_SCALING_GROUP = "default"

# Test resource slots
TEST_AVAILABLE_SLOTS = ResourceSlot({
    "cpu": Decimal("24"),
    "mem": BinarySize.from_str("32G"),
    "cuda.shares": Decimal("4"),
})

TEST_OCCUPIED_SLOTS = ResourceSlot({
    "cpu": Decimal("8"),
    "mem": BinarySize.from_str("16G"),
    "cuda.shares": Decimal("2"),
})

# Test agent row fixture
AGENT_ROW_FIXTURE = AgentRow(
    id=TEST_AGENT_ID,
    scaling_group=TEST_SCALING_GROUP,
    status=AgentStatus.ALIVE,
    status_changed=datetime.now(timezone.utc),
    region="us-east-1",
    architecture="x86_64",
    addr="10.0.0.1:6001",
    public_host="agent1.example.com",
    public_key="test-public-key",
    available_slots=TEST_AVAILABLE_SLOTS,
    occupied_slots=TEST_OCCUPIED_SLOTS,
    version="24.03.0",
    compute_plugins=[],
    schedulable=True,
    lost_at=None,
    first_contact=datetime.now(timezone.utc),
)

# Test agent data fixture (DTO)
AGENT_DATA_FIXTURE = AgentData(
    id=TEST_AGENT_ID,
    scaling_group=TEST_SCALING_GROUP,
    status=AgentStatus.ALIVE,
    status_changed=datetime.now(timezone.utc),
    region="us-east-1",
    architecture="x86_64",
    addr="10.0.0.1:6001",
    public_host="agent1.example.com",
    available_slots=TEST_AVAILABLE_SLOTS,
    occupied_slots=TEST_OCCUPIED_SLOTS,
    version="24.03.0",
    compute_plugins=[],
    schedulable=True,
    first_contact=datetime.now(timezone.utc),
    lost_at=None,
)

# Watcher response fixtures
WATCHER_STATUS_RESPONSE = {
    "status": "running",
    "version": "24.03.0",
    "uptime": 3600,
    "plugins": ["docker", "jail"],
}

WATCHER_SUCCESS_RESPONSE = {
    "success": True,
    "message": "Operation completed successfully",
}

WATCHER_ERROR_RESPONSE = {
    "success": False,
    "error": "Connection refused",
}

# Modify agent input fixture
MODIFY_AGENT_INPUT_DICT = {
    "schedulable": False,
    "scaling_group": "new-group",
}


@pytest.fixture
def mock_db_engine():
    """Mock database engine"""
    mock = MagicMock(spec=ExtendedAsyncSAEngine)
    return mock


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    mock = AsyncMock()
    mock.scalar = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def agent_repository(mock_db_engine, mock_db_session):
    """Create AgentRepository with mocked database"""
    # Make the db engine return our mock session
    mock_db_engine.begin_readonly_session.return_value = mock_db_session

    return AgentRepository(db=mock_db_engine)


class TestAgentRepository:
    """Unit tests for AgentRepository"""

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self,
        agent_repository,
        mock_db_session,
        mock_db_engine,
    ):
        """Test successful retrieval of agent by ID"""
        # Setup mock to return our test agent row
        mock_db_session.scalar.return_value = AGENT_ROW_FIXTURE

        # Execute
        result = await agent_repository.get_by_id(TEST_AGENT_ID)

        # Verify
        assert result is not None
        assert isinstance(result, AgentData)
        assert result.id == TEST_AGENT_ID
        assert result.scaling_group == AGENT_ROW_FIXTURE.scaling_group
        assert result.status == AGENT_ROW_FIXTURE.status
        assert result.addr == AGENT_ROW_FIXTURE.addr

        # Verify database interactions
        mock_db_engine.begin_readonly_session.assert_called_once()

        # Verify the SQL query was constructed correctly
        query_call = mock_db_session.scalar.call_args
        assert len(query_call.args) == 1
        query = query_call.args[0]

        # The query should be a select statement on AgentRow
        assert hasattr(query, "_where_criteria")

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        agent_repository,
        mock_db_session,
        mock_db_engine,
    ):
        """Test retrieval when agent doesn't exist"""
        # Setup mock to return None
        mock_db_session.scalar.return_value = None

        # Execute
        result = await agent_repository.get_by_id(NONEXISTENT_AGENT_ID)

        # Verify
        assert result is None

        # Verify database was queried
        mock_db_engine.begin_readonly_session.assert_called_once()
        mock_db_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_database_error(
        self,
        agent_repository,
        mock_db_session,
        mock_db_engine,
    ):
        """Test error handling when database fails"""
        # Setup mock to raise an exception
        mock_db_session.scalar.side_effect = Exception("Database connection failed")

        # Execute and verify exception is propagated
        with pytest.raises(Exception, match="Database connection failed"):
            await agent_repository.get_by_id(TEST_AGENT_ID)

    @pytest.mark.asyncio
    async def test_get_by_id_session_context_manager(
        self,
        agent_repository,
        mock_db_session,
        mock_db_engine,
    ):
        """Test that database session is properly managed"""
        # Setup
        mock_db_session.scalar.return_value = AGENT_ROW_FIXTURE

        # Execute
        await agent_repository.get_by_id(TEST_AGENT_ID)

        # Verify session context manager was used correctly
        mock_db_session.__aenter__.assert_called_once()
        mock_db_session.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_multiple_calls(
        self,
        agent_repository,
        mock_db_session,
        mock_db_engine,
    ):
        """Test multiple calls create new sessions"""
        # Setup
        mock_db_session.scalar.return_value = AGENT_ROW_FIXTURE

        # Execute multiple calls
        agent_ids = [TEST_AGENT_ID, NONEXISTENT_AGENT_ID, TEST_AGENT_ID]
        for agent_id in agent_ids:
            await agent_repository.get_by_id(agent_id)

        # Verify new session was created for each call
        assert mock_db_engine.begin_readonly_session.call_count == 3
        assert mock_db_session.scalar.call_count == 3

    @pytest.mark.asyncio
    async def test_agent_data_conversion(
        self,
        agent_repository,
        mock_db_session,
        mock_db_engine,
    ):
        """Test that AgentRow is correctly converted to AgentData"""
        # Setup with a complete agent row
        mock_db_session.scalar.return_value = AGENT_ROW_FIXTURE

        # Execute
        result = await agent_repository.get_by_id(TEST_AGENT_ID)

        # Verify all fields are correctly mapped
        assert result is not None
        assert result.id == AGENT_ROW_FIXTURE.id
        assert result.scaling_group == AGENT_ROW_FIXTURE.scaling_group
        assert result.status == AGENT_ROW_FIXTURE.status
        assert result.status_changed == AGENT_ROW_FIXTURE.status_changed
        assert result.region == AGENT_ROW_FIXTURE.region
        assert result.architecture == AGENT_ROW_FIXTURE.architecture
        assert result.addr == AGENT_ROW_FIXTURE.addr
        assert result.public_host == AGENT_ROW_FIXTURE.public_host
        assert result.available_slots == AGENT_ROW_FIXTURE.available_slots
        assert result.occupied_slots == AGENT_ROW_FIXTURE.occupied_slots
        assert result.version == AGENT_ROW_FIXTURE.version
        assert result.compute_plugins == AGENT_ROW_FIXTURE.compute_plugins
        assert result.schedulable == AGENT_ROW_FIXTURE.schedulable
