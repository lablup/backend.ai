"""
Integration tests for the asynchronous session termination flow.
Tests the complete flow from destroy_session request to actual termination.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import AccessKey, AgentId, KernelId, SessionId
from ai.backend.manager.clients.agent import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.session import SessionStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.schedule.repository import (
    MarkTerminatingResult,
    ScheduleRepository,
    TerminatingKernelData,
    TerminatingSessionData,
)
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.services.session.service import SessionService
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler, SchedulerArgs
from ai.backend.manager.sokovan.scheduler.validators.validator import SchedulingValidator
from ai.backend.manager.types import DistributedLockFactory


@pytest.fixture
def mock_database():
    """Mock database engine."""
    mock_db = MagicMock(spec=ExtendedAsyncSAEngine)
    return mock_db


@pytest.fixture
def mock_config_provider():
    """Mock configuration provider."""
    mock_provider = MagicMock(spec=ManagerConfigProvider)
    mock_provider.config.manager.session_schedule_lock_lifetime = 10.0
    mock_provider.config.manager.agent_selection_resource_priority = ["cpu", "mem"]
    return mock_provider


@pytest.fixture
def mock_valkey_stat():
    """Mock Valkey stat client."""
    return MagicMock(spec=ValkeyStatClient)


@pytest.fixture
def mock_valkey_schedule():
    """Mock Valkey schedule client."""
    mock_client = MagicMock(spec=ValkeyScheduleClient)
    mock_client.produce = AsyncMock()
    return mock_client


@pytest.fixture
def mock_event_producer():
    """Mock event producer."""
    return MagicMock(spec=EventProducer)


@pytest.fixture
def mock_scheduler_dispatcher():
    """Mock scheduler dispatcher."""
    return MagicMock(spec=SchedulerDispatcher)


@pytest.fixture
def mock_lock_factory():
    """Mock distributed lock factory."""
    mock_factory = MagicMock(spec=DistributedLockFactory)
    mock_lock = MagicMock()
    mock_lock.__aenter__ = AsyncMock(return_value=mock_lock)
    mock_lock.__aexit__ = AsyncMock()
    mock_factory.return_value = mock_lock
    return mock_factory


@pytest.fixture
def mock_agent_pool():
    """Mock agent pool with agent clients."""
    mock_pool = MagicMock(spec=AgentPool)
    
    def create_mock_agent_client(agent_id):
        mock_client = MagicMock()
        mock_client.destroy_kernel = AsyncMock()
        return mock_client
    
    mock_pool.get_agent_client = MagicMock(side_effect=create_mock_agent_client)
    return mock_pool


@pytest.fixture
async def repository(mock_database, mock_valkey_stat, mock_config_provider):
    """Create ScheduleRepository instance."""
    return ScheduleRepository(
        db=mock_database,
        valkey_stat=mock_valkey_stat,
        config_provider=mock_config_provider,
    )


@pytest.fixture
async def scheduler(
    repository,
    mock_config_provider,
    mock_lock_factory,
    mock_agent_pool,
    mock_valkey_stat,
):
    """Create Scheduler instance."""
    args = SchedulerArgs(
        validator=MagicMock(spec=SchedulingValidator),
        sequencer=MagicMock(),
        agent_selector=MagicMock(),
        allocator=MagicMock(),
        repository=repository,
        config_provider=mock_config_provider,
        lock_factory=mock_lock_factory,
        agent_pool=mock_agent_pool,
        valkey_stat=mock_valkey_stat,
    )
    return Scheduler(args)


@pytest.fixture
async def schedule_coordinator(
    scheduler,
    mock_valkey_schedule,
    mock_event_producer,
    mock_scheduler_dispatcher,
):
    """Create ScheduleCoordinator instance."""
    return ScheduleCoordinator(
        valkey_schedule=mock_valkey_schedule,
        scheduler=scheduler,
        event_producer=mock_event_producer,
        scheduler_dispatcher=mock_scheduler_dispatcher,
    )


@pytest.fixture
async def session_service(schedule_coordinator):
    """Create SessionService with ScheduleCoordinator."""
    mock_service = MagicMock(spec=SessionService)
    mock_service._schedule_coordinator = schedule_coordinator
    return mock_service


class TestAsyncTerminationFlow:
    """Integration tests for the complete async termination flow."""

    async def test_complete_flow_single_session(
        self,
        session_service,
        scheduler,
        repository,
        mock_agent_pool,
        mock_valkey_schedule,
    ):
        """Test complete flow for terminating a single session."""
        # Setup
        session_id = SessionId(uuid4())
        kernel_id = KernelId(uuid4())
        agent_id = AgentId("test-agent")
        
        # Mock repository methods
        with patch.object(repository, 'mark_sessions_terminating') as mock_mark:
            mock_mark.return_value = MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[str(session_id)],
                skipped_sessions=[],
                not_found_sessions=[],
            )
            
            with patch.object(repository, 'get_terminating_sessions') as mock_get:
                mock_get.return_value = [
                    TerminatingSessionData(
                        session_id=session_id,
                        access_key=AccessKey("test-key"),
                        creation_id="test-creation",
                        status=SessionStatus.TERMINATING,
                        status_info="USER_REQUESTED",
                        kernels=[
                            TerminatingKernelData(
                                kernel_id=kernel_id,
                                status=KernelStatus.TERMINATING,
                                container_id="container-123",
                                agent_id=agent_id,
                                agent_addr="10.0.0.1:2001",
                            )
                        ],
                    )
                ]
                
                with patch.object(repository, 'batch_update_terminated_status') as mock_update:
                    mock_update.return_value = None
                    
                    # Step 1: User requests session destruction
                    result = await session_service._schedule_coordinator.mark_sessions_for_termination(
                        [str(session_id)],
                        reason="USER_REQUESTED",
                    )
                    
                    # Verify marking was successful
                    assert result.has_processed()
                    assert str(session_id) in result.terminating_sessions
                    
                    # Verify scheduling was requested
                    mock_valkey_schedule.produce.assert_called_once_with(
                        ScheduleType.TERMINATE.value,
                        immediate=True,
                    )
                    
                    # Step 2: Scheduler processes terminating sessions
                    schedule_result = await scheduler.terminate_sessions()
                    
                    # Verify termination was successful
                    assert schedule_result.succeeded_count == 1
                    
                    # Verify agent destroy_kernel was called
                    mock_agent = mock_agent_pool.get_agent_client(agent_id)
                    mock_agent.destroy_kernel.assert_called_once_with(
                        str(kernel_id),
                        str(session_id),
                        "USER_REQUESTED",
                    )
                    
                    # Verify database was updated
                    mock_update.assert_called_once()

    async def test_complete_flow_multiple_sessions(
        self,
        session_service,
        scheduler,
        repository,
        mock_agent_pool,
        mock_valkey_schedule,
    ):
        """Test complete flow for terminating multiple sessions concurrently."""
        # Setup multiple sessions
        sessions = []
        for i in range(3):
            session_id = SessionId(uuid4())
            kernel_id = KernelId(uuid4())
            agent_id = AgentId(f"agent-{i}")
            sessions.append({
                "session_id": session_id,
                "kernel_id": kernel_id,
                "agent_id": agent_id,
            })
        
        session_ids = [str(s["session_id"]) for s in sessions]
        
        # Mock repository methods
        with patch.object(repository, 'mark_sessions_terminating') as mock_mark:
            mock_mark.return_value = MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=session_ids,
                skipped_sessions=[],
                not_found_sessions=[],
            )
            
            terminating_sessions = [
                TerminatingSessionData(
                    session_id=s["session_id"],
                    access_key=AccessKey(f"key-{i}"),
                    creation_id=f"creation-{i}",
                    status=SessionStatus.TERMINATING,
                    status_info="BATCH_TERMINATION",
                    kernels=[
                        TerminatingKernelData(
                            kernel_id=s["kernel_id"],
                            status=KernelStatus.TERMINATING,
                            container_id=f"container-{i}",
                            agent_id=s["agent_id"],
                            agent_addr=f"10.0.0.{i+1}:2001",
                        )
                    ],
                )
                for i, s in enumerate(sessions)
            ]
            
            with patch.object(repository, 'get_terminating_sessions') as mock_get:
                mock_get.return_value = terminating_sessions
                
                with patch.object(repository, 'batch_update_terminated_status') as mock_update:
                    mock_update.return_value = None
                    
                    # Step 1: Request batch termination
                    result = await session_service._schedule_coordinator.mark_sessions_for_termination(
                        session_ids,
                        reason="BATCH_TERMINATION",
                    )
                    
                    # Verify all sessions were marked
                    assert len(result.terminating_sessions) == 3
                    
                    # Step 2: Process terminations concurrently
                    import time
                    
                    # Add slight delay to agent calls to verify concurrency
                    async def delayed_destroy(*args):
                        await asyncio.sleep(0.01)
                        return None
                    
                    for s in sessions:
                        mock_agent = mock_agent_pool.get_agent_client(s["agent_id"])
                        mock_agent.destroy_kernel.side_effect = delayed_destroy
                    
                    start_time = time.time()
                    schedule_result = await scheduler.terminate_sessions()
                    elapsed = time.time() - start_time
                    
                    # Verify concurrent execution (should be faster than sequential)
                    assert schedule_result.succeeded_count == 3
                    assert elapsed < 0.05  # Should execute concurrently
                    
                    # Verify all agents were called
                    for s in sessions:
                        mock_agent = mock_agent_pool.get_agent_client(s["agent_id"])
                        mock_agent.destroy_kernel.assert_called_once()

    async def test_flow_with_mixed_session_states(
        self,
        session_service,
        scheduler,
        repository,
        mock_valkey_schedule,
    ):
        """Test flow with sessions in different states."""
        # Setup sessions with different states
        pending_session = str(uuid4())
        running_session = str(uuid4())
        terminating_session = str(uuid4())
        
        all_sessions = [pending_session, running_session, terminating_session]
        
        # Mock repository to return different results based on state
        with patch.object(repository, 'mark_sessions_terminating') as mock_mark:
            mock_mark.return_value = MarkTerminatingResult(
                cancelled_sessions=[pending_session],  # PENDING -> CANCELLED
                terminating_sessions=[running_session],  # RUNNING -> TERMINATING
                skipped_sessions=[terminating_session],  # Already TERMINATING
                not_found_sessions=[],
            )
            
            # Request termination for all sessions
            result = await session_service._schedule_coordinator.mark_sessions_for_termination(
                all_sessions,
                reason="MIXED_STATES",
            )
            
            # Verify correct categorization
            assert pending_session in result.cancelled_sessions
            assert running_session in result.terminating_sessions
            assert terminating_session in result.skipped_sessions
            
            # Verify scheduling is requested only if sessions were processed
            assert result.has_processed()
            mock_valkey_schedule.produce.assert_called_once()

    async def test_flow_with_partial_failure(
        self,
        session_service,
        scheduler,
        repository,
        mock_agent_pool,
    ):
        """Test flow when some kernels fail to terminate."""
        # Setup
        session_id = SessionId(uuid4())
        kernel_ids = [KernelId(uuid4()), KernelId(uuid4())]
        agent_ids = [AgentId("agent-1"), AgentId("agent-2")]
        
        # Mock repository methods
        with patch.object(repository, 'mark_sessions_terminating') as mock_mark:
            mock_mark.return_value = MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[str(session_id)],
                skipped_sessions=[],
                not_found_sessions=[],
            )
            
            with patch.object(repository, 'get_terminating_sessions') as mock_get:
                mock_get.return_value = [
                    TerminatingSessionData(
                        session_id=session_id,
                        access_key=AccessKey("test-key"),
                        creation_id="test-creation",
                        status=SessionStatus.TERMINATING,
                        status_info="PARTIAL_TEST",
                        kernels=[
                            TerminatingKernelData(
                                kernel_id=kernel_ids[0],
                                status=KernelStatus.TERMINATING,
                                container_id="container-1",
                                agent_id=agent_ids[0],
                                agent_addr="10.0.0.1:2001",
                            ),
                            TerminatingKernelData(
                                kernel_id=kernel_ids[1],
                                status=KernelStatus.TERMINATING,
                                container_id="container-2",
                                agent_id=agent_ids[1],
                                agent_addr="10.0.0.2:2001",
                            ),
                        ],
                    )
                ]
                
                with patch.object(repository, 'batch_update_terminated_status') as mock_update:
                    mock_update.return_value = None
                    
                    # Configure first agent to succeed, second to fail
                    mock_agent1 = mock_agent_pool.get_agent_client(agent_ids[0])
                    mock_agent1.destroy_kernel.return_value = None
                    
                    mock_agent2 = mock_agent_pool.get_agent_client(agent_ids[1])
                    mock_agent2.destroy_kernel.side_effect = Exception("Network error")
                    
                    # Request termination
                    result = await session_service._schedule_coordinator.mark_sessions_for_termination(
                        [str(session_id)],
                        reason="PARTIAL_TEST",
                    )
                    
                    assert result.has_processed()
                    
                    # Process termination with partial failure
                    schedule_result = await scheduler.terminate_sessions()
                    
                    # Session should not be counted as successfully terminated
                    assert schedule_result.succeeded_count == 0
                    
                    # Verify batch update was still called
                    mock_update.assert_called_once()
                    
                    # The session should remain in TERMINATING state for retry
                    call_args = mock_update.call_args[0][0]
                    assert len(call_args) == 1
                    assert not call_args[0].should_terminate_session

    async def test_flow_with_recursive_termination(
        self,
        session_service,
        repository,
        mock_valkey_schedule,
    ):
        """Test recursive termination of dependent sessions."""
        # Setup main session and dependencies
        main_session = str(uuid4())
        dep_session1 = str(uuid4())
        dep_session2 = str(uuid4())
        
        all_sessions = [main_session, dep_session1, dep_session2]
        
        # Mock repository to handle recursive termination
        with patch.object(repository, 'mark_sessions_terminating') as mock_mark:
            mock_mark.return_value = MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=all_sessions,  # All marked for termination
                skipped_sessions=[],
                not_found_sessions=[],
            )
            
            # Request recursive termination
            result = await session_service._schedule_coordinator.mark_sessions_for_termination(
                all_sessions,
                reason="RECURSIVE_TERMINATION",
            )
            
            # Verify all sessions were marked
            assert len(result.terminating_sessions) == 3
            for session_id in all_sessions:
                assert session_id in result.terminating_sessions
            
            # Verify scheduling was requested
            mock_valkey_schedule.produce.assert_called_once_with(
                ScheduleType.TERMINATE.value,
                immediate=True,
            )

    async def test_flow_idempotency(
        self,
        session_service,
        repository,
        mock_valkey_schedule,
    ):
        """Test that termination requests are idempotent."""
        # Setup
        session_id = str(uuid4())
        
        # First request - session gets marked
        with patch.object(repository, 'mark_sessions_terminating') as mock_mark:
            mock_mark.return_value = MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[session_id],
                skipped_sessions=[],
                not_found_sessions=[],
            )
            
            result1 = await session_service._schedule_coordinator.mark_sessions_for_termination(
                [session_id],
                reason="FIRST_REQUEST",
            )
            
            assert result1.has_processed()
            assert session_id in result1.terminating_sessions
        
        # Second request - session already terminating
        with patch.object(repository, 'mark_sessions_terminating') as mock_mark:
            mock_mark.return_value = MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[],
                skipped_sessions=[session_id],  # Already terminating
                not_found_sessions=[],
            )
            
            result2 = await session_service._schedule_coordinator.mark_sessions_for_termination(
                [session_id],
                reason="DUPLICATE_REQUEST",
            )
            
            # Should not process again
            assert not result2.has_processed()
            assert session_id in result2.skipped_sessions
            
            # No additional scheduling should be requested
            assert mock_valkey_schedule.produce.call_count == 1  # Only from first request

    async def test_flow_performance_with_many_sessions(
        self,
        scheduler,
        repository,
        mock_agent_pool,
    ):
        """Test performance with a large number of sessions."""
        # Setup many sessions
        num_sessions = 100
        sessions_data = []
        
        for i in range(num_sessions):
            session_id = SessionId(uuid4())
            kernel_id = KernelId(uuid4())
            agent_id = AgentId(f"agent-{i % 10}")  # Distribute across 10 agents
            
            sessions_data.append(
                TerminatingSessionData(
                    session_id=session_id,
                    access_key=AccessKey(f"key-{i}"),
                    creation_id=f"creation-{i}",
                    status=SessionStatus.TERMINATING,
                    status_info="BULK_TERMINATION",
                    kernels=[
                        TerminatingKernelData(
                            kernel_id=kernel_id,
                            status=KernelStatus.TERMINATING,
                            container_id=f"container-{i}",
                            agent_id=agent_id,
                            agent_addr=f"10.0.0.{(i % 10) + 1}:2001",
                        )
                    ],
                )
            )
        
        with patch.object(repository, 'get_terminating_sessions') as mock_get:
            mock_get.return_value = sessions_data
            
            with patch.object(repository, 'batch_update_terminated_status') as mock_update:
                mock_update.return_value = None
                
                # Measure termination time
                import time
                start_time = time.time()
                
                result = await scheduler.terminate_sessions()
                
                elapsed = time.time() - start_time
                
                # Should handle 100 sessions efficiently
                assert result.succeeded_count == num_sessions
                assert elapsed < 1.0  # Should complete within 1 second
                
                # Verify batch update was called once with all results
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0][0]
                assert len(call_args) == num_sessions