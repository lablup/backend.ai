"""
Tests for SessionTerminator.terminate_sessions method.
Tests the batch termination of sessions marked with TERMINATING status.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.clients.agent import AgentClient, AgentClientPool
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.scheduler import (
    TerminatingKernelData,
    TerminatingSessionData,
)
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.terminator.terminator import (
    SessionTerminator,
    SessionTerminatorArgs,
)


@pytest.fixture
def mock_agent_client_pool() -> MagicMock:
    """Mock AgentClientPool for testing."""
    mock_pool = MagicMock(spec=AgentClientPool)

    # Create a dictionary to store agent clients
    agent_clients: dict[AgentId, MagicMock] = {}

    # Create mock agent clients
    def get_or_create_mock_agent_client(agent_id: AgentId) -> MagicMock:
        if agent_id not in agent_clients:
            mock_client = MagicMock(spec=AgentClient)
            mock_client.destroy_kernel = AsyncMock()
            agent_clients[agent_id] = mock_client
        return agent_clients[agent_id]

    # Create context manager for acquire()
    class MockAcquireContextManager:
        def __init__(self, agent_id: AgentId) -> None:
            self.agent_id = agent_id

        async def __aenter__(self) -> MagicMock:
            return get_or_create_mock_agent_client(self.agent_id)

        async def __aexit__(self, *args: object) -> None:
            pass

    mock_pool.acquire = MagicMock(side_effect=lambda agent_id: MockAcquireContextManager(agent_id))
    mock_pool.get_agent_client = MagicMock(side_effect=get_or_create_mock_agent_client)
    mock_pool._clients = agent_clients  # Store for test access
    return mock_pool


@pytest.fixture
def mock_repository() -> MagicMock:
    """Mock ScheduleRepository for testing."""
    mock_repo = MagicMock()
    mock_repo.get_terminating_sessions = AsyncMock()
    mock_repo.update_kernel_status_terminated = AsyncMock()
    return mock_repo


@pytest.fixture
def terminator(mock_repository: MagicMock, mock_agent_client_pool: MagicMock) -> SessionTerminator:
    """Create SessionTerminator instance with mocked dependencies."""
    mock_valkey_schedule = MagicMock()
    return SessionTerminator(
        SessionTerminatorArgs(
            repository=mock_repository,
            agent_client_pool=mock_agent_client_pool,
            valkey_schedule=mock_valkey_schedule,
        )
    )


class TestTerminateSessions:
    """Test cases for session termination in SessionTerminator."""

    async def test_terminate_sessions_no_sessions(
        self,
        terminator: SessionTerminator,
        mock_repository: MagicMock,
    ) -> None:
        """Test terminate_sessions when no sessions need termination."""
        # Setup - no terminating sessions
        terminating_sessions: list[TerminatingSessionData] = []

        # Execute - wrap in RecorderContext scope with entity_ids
        with RecorderContext[SessionId].scope("terminate", []):
            result = await terminator._terminate_sessions_internal(terminating_sessions)

        # Verify
        assert isinstance(result, ScheduleResult)
        assert len(result.scheduled_sessions) == 0

    async def test_terminate_sessions_single_success(
        self,
        terminator: SessionTerminator,
        mock_repository: MagicMock,
        mock_agent_client_pool: MagicMock,
    ) -> None:
        """Test successful termination RPC call for a single session."""
        # Setup
        session_id = SessionId(uuid4())
        kernel_id = KernelId(uuid4())
        agent_id = AgentId("test-agent-1")

        terminating_session = TerminatingSessionData(
            session_id=session_id,
            access_key=AccessKey("test-key"),
            creation_id="test-creation",
            status=SessionStatus.TERMINATING,
            status_info="USER_REQUESTED",
            session_type=SessionTypes.INTERACTIVE,
            kernels=[
                TerminatingKernelData(
                    kernel_id=kernel_id,
                    status=KernelStatus.TERMINATING,
                    container_id="container-123",
                    agent_id=agent_id,
                    agent_addr="10.0.0.1:2001",
                    occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                )
            ],
        )

        mock_repository.get_terminating_sessions.return_value = [terminating_session]

        # Configure agent client to succeed
        mock_agent = mock_agent_client_pool.get_agent_client(agent_id)
        mock_agent.destroy_kernel.return_value = None  # Success

        # Execute - wrap in RecorderContext scope with entity_ids
        with RecorderContext[SessionId].scope("terminate", [session_id]):
            result = await terminator._terminate_sessions_internal([terminating_session])

        # Verify
        # Returns empty result (status updates handled by events/sweep)
        assert isinstance(result, ScheduleResult)
        assert len(result.scheduled_sessions) == 0

        # Verify agent destroy_kernel was called with correct parameters
        # Note: AgentClient.destroy_kernel accepts SessionId type and converts to str internally
        mock_agent.destroy_kernel.assert_called_once_with(
            kernel_id,
            session_id,
            "USER_REQUESTED",
            suppress_events=False,
        )

    async def test_terminate_sessions_multiple_kernels(
        self,
        terminator: SessionTerminator,
        mock_repository: MagicMock,
        mock_agent_client_pool: MagicMock,
    ) -> None:
        """Test termination RPC calls for a session with multiple kernels."""
        # Setup
        session_id = SessionId(uuid4())
        kernel_ids = [KernelId(uuid4()) for _ in range(3)]
        agent_ids = [AgentId(f"agent-{i}") for i in range(3)]

        terminating_session = TerminatingSessionData(
            session_id=session_id,
            access_key=AccessKey("test-key"),
            creation_id="test-creation",
            status=SessionStatus.TERMINATING,
            status_info="FORCED_TERMINATION",
            session_type=SessionTypes.INTERACTIVE,
            kernels=[
                TerminatingKernelData(
                    kernel_id=kernel_ids[i],
                    status=KernelStatus.TERMINATING,
                    container_id=f"container-{i}",
                    agent_id=agent_ids[i],
                    agent_addr=f"10.0.0.{i + 1}:2001",
                    occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
                )
                for i in range(3)
            ],
        )

        # Execute - wrap in RecorderContext scope with entity_ids
        with RecorderContext[SessionId].scope("terminate", [session_id]):
            result = await terminator._terminate_sessions_internal([terminating_session])

        # Verify
        # Returns empty result (status updates handled by events/sweep)
        assert isinstance(result, ScheduleResult)
        assert len(result.scheduled_sessions) == 0

        # Verify all kernels had RPC calls made
        # Note: AgentClient.destroy_kernel accepts SessionId type and converts to str internally
        for i in range(3):
            mock_agent = mock_agent_client_pool.get_agent_client(agent_ids[i])
            mock_agent.destroy_kernel.assert_called_once_with(
                kernel_ids[i],
                session_id,
                "FORCED_TERMINATION",
                suppress_events=False,
            )

    async def test_terminate_sessions_partial_failure(
        self,
        terminator: SessionTerminator,
        mock_repository: MagicMock,
        mock_agent_client_pool: MagicMock,
    ) -> None:
        """Test partial failure in kernel termination."""
        # Setup
        session_id = SessionId(uuid4())
        kernel_ids = [uuid4(), uuid4()]
        agent_ids = [AgentId("agent-1"), AgentId("agent-2")]

        terminating_session = TerminatingSessionData(
            session_id=session_id,
            access_key=AccessKey("test-key"),
            creation_id="test-creation",
            status=SessionStatus.TERMINATING,
            status_info="TEST_PARTIAL",
            session_type=SessionTypes.INTERACTIVE,
            kernels=[
                TerminatingKernelData(
                    kernel_id=KernelId(kernel_ids[0]),
                    status=KernelStatus.TERMINATING,
                    container_id="container-1",
                    agent_id=agent_ids[0],
                    agent_addr="10.0.0.1:2001",
                    occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
                ),
                TerminatingKernelData(
                    kernel_id=KernelId(kernel_ids[1]),
                    status=KernelStatus.TERMINATING,
                    container_id="container-2",
                    agent_id=agent_ids[1],
                    agent_addr="10.0.0.2:2001",
                    occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
                ),
            ],
        )

        mock_repository.get_terminating_sessions.return_value = [terminating_session]

        # Configure first agent to succeed, second to fail
        mock_agent1 = mock_agent_client_pool.get_agent_client(agent_ids[0])
        mock_agent1.destroy_kernel.return_value = None  # Success

        mock_agent2 = mock_agent_client_pool.get_agent_client(agent_ids[1])
        mock_agent2.destroy_kernel.side_effect = Exception("Agent connection failed")

        # Execute - wrap in RecorderContext scope with entity_ids
        with RecorderContext[SessionId].scope("terminate", [session_id]):
            result = await terminator._terminate_sessions_internal([terminating_session])

        # Verify
        # Session should not be counted as terminated due to partial failure
        assert len(result.scheduled_sessions) == 0

    async def test_terminate_sessions_concurrent_execution(
        self,
        terminator: SessionTerminator,
        mock_repository: MagicMock,
        mock_agent_client_pool: MagicMock,
    ) -> None:
        """Test that kernel termination RPC calls are executed concurrently."""
        # Setup multiple sessions
        sessions = []
        all_kernel_ids = []
        all_agent_ids = []
        for i in range(3):
            session_id = SessionId(uuid4())
            kernels = []
            for j in range(2):  # 2 kernels per session
                kernel_id = uuid4()
                agent_id = AgentId(f"agent-{i}-{j}")
                all_kernel_ids.append(kernel_id)
                all_agent_ids.append(agent_id)
                kernels.append(
                    TerminatingKernelData(
                        kernel_id=KernelId(kernel_id),
                        status=KernelStatus.TERMINATING,
                        container_id=f"container-{i}-{j}",
                        agent_id=agent_id,
                        agent_addr=f"10.0.{i}.{j}:2001",
                        occupied_slots=ResourceSlot({
                            "cpu": Decimal("1"),
                            "mem": Decimal("2048"),
                        }),
                    )
                )
            sessions.append(
                TerminatingSessionData(
                    session_id=session_id,
                    access_key=AccessKey(f"key-{i}"),
                    creation_id=f"creation-{i}",
                    status=SessionStatus.TERMINATING,
                    status_info="BATCH_TERMINATION",
                    session_type=SessionTypes.INTERACTIVE,
                    kernels=kernels,
                )
            )

        mock_repository.get_terminating_sessions.return_value = sessions

        # Add delay to agent calls to verify concurrency
        async def delayed_destroy(*args, **kwargs):
            await asyncio.sleep(0.1)
            return

        for agent_id in all_agent_ids:
            mock_agent = mock_agent_client_pool.get_agent_client(agent_id)
            mock_agent.destroy_kernel.side_effect = delayed_destroy

        # Extract session_ids for RecorderContext scope
        session_ids = [s.session_id for s in sessions]

        # Execute - wrap in RecorderContext scope with entity_ids
        import time

        start_time = time.time()
        with RecorderContext[SessionId].scope("terminate", session_ids):
            result = await terminator._terminate_sessions_internal(sessions)
        elapsed = time.time() - start_time

        # Verify
        # Returns empty result (status updates handled by events/sweep)
        assert isinstance(result, ScheduleResult)
        assert len(result.scheduled_sessions) == 0

        # Verify all RPC calls were made
        for i, agent_id in enumerate(all_agent_ids):
            mock_agent = mock_agent_client_pool.get_agent_client(agent_id)
            assert mock_agent.destroy_kernel.call_count == 1

        # If executed sequentially, it would take at least 0.6 seconds (6 kernels * 0.1s)
        # With concurrent execution, it should be much faster
        assert elapsed < 0.4  # Allow some overhead for metrics and other operations

    async def test_terminate_sessions_empty_kernel_list(
        self,
        terminator: SessionTerminator,
        mock_repository: MagicMock,
    ) -> None:
        """Test session with no kernels."""
        # Setup
        session_id = SessionId(uuid4())

        terminating_session = TerminatingSessionData(
            session_id=session_id,
            access_key=AccessKey("test-key"),
            creation_id="test-creation",
            status=SessionStatus.TERMINATING,
            status_info="NO_KERNELS",
            session_type=SessionTypes.INTERACTIVE,
            kernels=[],  # No kernels
        )

        # Execute - wrap in RecorderContext scope with entity_ids
        with RecorderContext[SessionId].scope("terminate", [session_id]):
            result = await terminator._terminate_sessions_internal([terminating_session])

        # Verify
        # Session without kernels cannot be terminated
        assert len(result.scheduled_sessions) == 0
