"""
Tests for Scheduler.terminate_sessions method.
Tests the batch termination of sessions marked with TERMINATING status.
"""

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
from ai.backend.manager.clients.agent import AgentClient, AgentPool
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.schedule.repository import (
    TerminatingKernelData,
    TerminatingSessionData,
)
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler, SchedulerArgs


@pytest.fixture
def mock_agent_pool():
    """Mock AgentPool for testing."""
    mock_pool = MagicMock(spec=AgentPool)

    # Create a dictionary to store agent clients
    agent_clients = {}

    # Create mock agent clients
    def get_or_create_mock_agent_client(agent_id, **kwargs):
        if agent_id not in agent_clients:
            mock_client = MagicMock(spec=AgentClient)
            mock_client.destroy_kernel = AsyncMock()
            agent_clients[agent_id] = mock_client
        return agent_clients[agent_id]

    mock_pool.get_agent_client = MagicMock(side_effect=get_or_create_mock_agent_client)
    mock_pool._clients = agent_clients  # Store for test access
    return mock_pool


@pytest.fixture
def mock_repository():
    """Mock ScheduleRepository for testing."""
    mock_repo = MagicMock()
    mock_repo.get_terminating_sessions = AsyncMock()
    mock_repo.batch_update_terminated_status = AsyncMock()
    return mock_repo


@pytest.fixture
def scheduler(mock_repository, mock_agent_pool):
    """Create Scheduler instance with mocked dependencies."""
    args = SchedulerArgs(
        validator=MagicMock(),
        sequencer=MagicMock(),
        agent_selector=MagicMock(),
        allocator=MagicMock(),
        repository=mock_repository,
        deployment_repository=MagicMock(),
        config_provider=MagicMock(),
        lock_factory=MagicMock(),
        agent_pool=mock_agent_pool,
        network_plugin_ctx=MagicMock(),
        valkey_schedule=MagicMock(),
    )
    return Scheduler(args)


class TestTerminateSessions:
    """Test cases for session termination in Scheduler."""

    async def test_terminate_sessions_no_sessions(
        self,
        scheduler: Scheduler,
        mock_repository,
    ):
        """Test terminate_sessions when no sessions need termination."""
        # Setup - no terminating sessions
        mock_repository.get_terminating_sessions.return_value = []

        # Execute
        result = await scheduler.terminate_sessions()

        # Verify
        assert isinstance(result, ScheduleResult)
        assert len(result.scheduled_sessions) == 0
        mock_repository.batch_update_terminated_status.assert_not_called()

    async def test_terminate_sessions_single_success(
        self,
        scheduler: Scheduler,
        mock_repository,
        mock_agent_pool,
    ):
        """Test successful termination of a single session."""
        # Setup
        session_id = SessionId(uuid4())
        kernel_id = uuid4()
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
                    kernel_id=KernelId(kernel_id),
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
        mock_agent = mock_agent_pool.get_agent_client(agent_id)
        mock_agent.destroy_kernel.return_value = None  # Success

        # Execute
        result = await scheduler.terminate_sessions()

        # Verify
        # Single session should be successfully terminated
        assert len(result.scheduled_sessions) == 1
        assert result.scheduled_sessions[0].session_id == session_id
        assert result.scheduled_sessions[0].creation_id == "test-creation"

        # Verify agent destroy_kernel was called with correct parameters
        mock_agent.destroy_kernel.assert_called_once_with(
            str(kernel_id),
            str(session_id),
            "USER_REQUESTED",
        )

        # Verify batch update was called
        mock_repository.batch_update_terminated_status.assert_called_once()

        # Check the termination results passed to batch update
        call_args = mock_repository.batch_update_terminated_status.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].session_id == session_id
        assert call_args[0].should_terminate_session is True

    async def test_terminate_sessions_multiple_kernels(
        self,
        scheduler: Scheduler,
        mock_repository,
        mock_agent_pool,
    ):
        """Test termination of a session with multiple kernels."""
        # Setup
        session_id = SessionId(uuid4())
        kernel_ids = [uuid4() for _ in range(3)]
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
                    kernel_id=KernelId(kernel_ids[i]),
                    status=KernelStatus.TERMINATING,
                    container_id=f"container-{i}",
                    agent_id=agent_ids[i],
                    agent_addr=f"10.0.0.{i + 1}:2001",
                    occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
                )
                for i in range(3)
            ],
        )

        mock_repository.get_terminating_sessions.return_value = [terminating_session]

        # Execute
        result = await scheduler.terminate_sessions()

        # Verify
        # Session with multiple kernels should be successfully terminated
        assert len(result.scheduled_sessions) == 1
        assert result.scheduled_sessions[0].session_id == session_id
        assert result.scheduled_sessions[0].creation_id == "test-creation"

        # Verify all kernels were terminated
        for i in range(3):
            mock_agent = mock_agent_pool.get_agent_client(agent_ids[i])
            mock_agent.destroy_kernel.assert_called_once_with(
                str(kernel_ids[i]),
                str(session_id),
                "FORCED_TERMINATION",
            )

    async def test_terminate_sessions_partial_failure(
        self,
        scheduler: Scheduler,
        mock_repository,
        mock_agent_pool,
    ):
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
        mock_agent1 = mock_agent_pool.get_agent_client(agent_ids[0])
        mock_agent1.destroy_kernel.return_value = None  # Success

        mock_agent2 = mock_agent_pool.get_agent_client(agent_ids[1])
        mock_agent2.destroy_kernel.side_effect = Exception("Agent connection failed")

        # Execute
        result = await scheduler.terminate_sessions()

        # Verify
        # Session should not be counted as terminated due to partial failure
        assert len(result.scheduled_sessions) == 0

        # Verify batch update was still called
        mock_repository.batch_update_terminated_status.assert_called_once()

        # Check termination results
        call_args = mock_repository.batch_update_terminated_status.call_args[0][0]
        assert len(call_args) == 1
        session_result = call_args[0]
        assert session_result.should_terminate_session is False  # Partial failure
        assert len(session_result.kernel_results) == 2
        assert session_result.kernel_results[0].success is True
        assert session_result.kernel_results[1].success is False

    async def test_terminate_sessions_concurrent_execution(
        self,
        scheduler: Scheduler,
        mock_repository,
        mock_agent_pool,
    ):
        """Test that kernel terminations are executed concurrently."""
        # Setup multiple sessions
        sessions = []
        for i in range(3):
            session_id = SessionId(uuid4())
            sessions.append(
                TerminatingSessionData(
                    session_id=session_id,
                    access_key=AccessKey(f"key-{i}"),
                    creation_id=f"creation-{i}",
                    status=SessionStatus.TERMINATING,
                    status_info="BATCH_TERMINATION",
                    session_type=SessionTypes.INTERACTIVE,
                    kernels=[
                        TerminatingKernelData(
                            kernel_id=KernelId(uuid4()),
                            status=KernelStatus.TERMINATING,
                            container_id=f"container-{i}-{j}",
                            agent_id=AgentId(f"agent-{i}-{j}"),
                            agent_addr=f"10.0.{i}.{j}:2001",
                            occupied_slots=ResourceSlot({
                                "cpu": Decimal("1"),
                                "mem": Decimal("2048"),
                            }),
                        )
                        for j in range(2)  # 2 kernels per session
                    ],
                )
            )

        mock_repository.get_terminating_sessions.return_value = sessions

        # Add delay to agent calls to verify concurrency
        async def delayed_destroy(*args):
            await asyncio.sleep(0.1)
            return None

        for session in sessions:
            for kernel in session.kernels:
                mock_agent = mock_agent_pool.get_agent_client(kernel.agent_id)
                mock_agent.destroy_kernel.side_effect = delayed_destroy

        # Execute
        import time

        start_time = time.time()
        result = await scheduler.terminate_sessions()
        elapsed = time.time() - start_time

        # Verify
        # All sessions should be successfully terminated
        assert len(result.scheduled_sessions) == 3
        for i, scheduled in enumerate(result.scheduled_sessions):
            assert scheduled.creation_id == f"creation-{i}"

        # If executed sequentially, it would take at least 0.6 seconds (6 kernels * 0.1s)
        # With concurrent execution, it should be much faster
        assert elapsed < 0.4  # Allow some overhead for metrics and other operations

    async def test_terminate_sessions_skip_kernels_without_agent(
        self,
        scheduler: Scheduler,
        mock_repository,
        mock_agent_pool,
    ):
        """Test that kernels without agent_id or container_id are skipped."""
        # Setup
        session_id = SessionId(uuid4())

        terminating_session = TerminatingSessionData(
            session_id=session_id,
            access_key=AccessKey("test-key"),
            creation_id="test-creation",
            status=SessionStatus.TERMINATING,
            status_info="TEST_SKIP",
            session_type=SessionTypes.INTERACTIVE,
            kernels=[
                # Kernel with both agent_id and container_id
                TerminatingKernelData(
                    kernel_id=KernelId(uuid4()),
                    status=KernelStatus.TERMINATING,
                    container_id="container-1",
                    agent_id=AgentId("agent-1"),
                    agent_addr="10.0.0.1:2001",
                    occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
                ),
                # Kernel without agent_id
                TerminatingKernelData(
                    kernel_id=KernelId(uuid4()),
                    status=KernelStatus.TERMINATING,
                    container_id="container-2",
                    agent_id=None,
                    occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
                    agent_addr=None,
                ),
                # Kernel without container_id
                TerminatingKernelData(
                    kernel_id=KernelId(uuid4()),
                    status=KernelStatus.TERMINATING,
                    container_id=None,
                    agent_id=AgentId("agent-2"),
                    agent_addr="10.0.0.2:2001",
                    occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
                ),
            ],
        )

        mock_repository.get_terminating_sessions.return_value = [terminating_session]

        # Execute
        await scheduler.terminate_sessions()

        # Verify
        # Only the first kernel should be terminated
        mock_agent1 = mock_agent_pool.get_agent_client(AgentId("agent-1"))
        mock_agent1.destroy_kernel.assert_called_once()

        # Agent-2 should not be called (kernel has no container_id)
        mock_agent2 = mock_agent_pool.get_agent_client(AgentId("agent-2"))
        mock_agent2.destroy_kernel.assert_not_called()

    async def test_terminate_sessions_empty_kernel_list(
        self,
        scheduler: Scheduler,
        mock_repository,
    ):
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

        mock_repository.get_terminating_sessions.return_value = [terminating_session]

        # Execute
        result = await scheduler.terminate_sessions()

        # Verify
        # Session without kernels cannot be terminated
        assert len(result.scheduled_sessions) == 0

        # Batch update should still be called
        mock_repository.batch_update_terminated_status.assert_called_once()

        # Check that session is not marked as terminated
        call_args = mock_repository.batch_update_terminated_status.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].should_terminate_session is False
