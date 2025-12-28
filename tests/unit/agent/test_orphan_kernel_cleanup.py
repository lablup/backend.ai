"""
Tests for OrphanKernelCleanupObserver.

Mock-based unit tests for verifying orphan kernel cleanup logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, MutableMapping, Protocol
from unittest.mock import AsyncMock, PropertyMock
from uuid import uuid4

import pytest

from ai.backend.agent.types import LifecycleEvent
from ai.backend.common.clients.valkey_client.valkey_schedule import KernelStatus
from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    ORPHAN_KERNEL_THRESHOLD_SEC,
    HealthCheckStatus,
)
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import AgentId, KernelId, SessionId

if TYPE_CHECKING:
    from ai.backend.agent.observer.orphan_kernel_cleanup import OrphanKernelCleanupObserver


@dataclass
class MockKernel:
    """Mock kernel object for testing."""

    session_id: SessionId


class KernelProtocol(Protocol):
    """Protocol for kernel interface."""

    session_id: SessionId


class AgentProtocol(Protocol):
    """Protocol for agent interface used by the observer."""

    id: AgentId
    kernel_registry: MutableMapping[KernelId, KernelProtocol]

    async def inject_container_lifecycle_event(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event: LifecycleEvent,
        reason: KernelLifecycleEventReason,
        *,
        suppress_events: bool = False,
    ) -> None: ...


class TestOrphanKernelCleanupObserver:
    """Test cases for OrphanKernelCleanupObserver.

    These tests verify the strict cleanup conditions:
    - agent_last_check must exist
    - kernel status must exist in Redis
    - kernel.last_check < agent_last_check - THRESHOLD
    """

    @pytest.fixture
    def mock_agent(self) -> AsyncMock:
        """Create a mock agent."""
        agent = AsyncMock(spec=AgentProtocol)
        agent.id = AgentId("test-agent-1")
        # Use PropertyMock for kernel_registry
        type(agent).kernel_registry = PropertyMock(return_value={})
        agent.inject_container_lifecycle_event = AsyncMock()
        return agent

    @pytest.fixture
    def mock_valkey_client(self) -> AsyncMock:
        """Create a mock ValkeyScheduleClient."""
        client = AsyncMock()
        client.get_agent_last_check = AsyncMock(return_value=None)
        client.get_kernel_presence_batch = AsyncMock(return_value={})
        return client

    @pytest.fixture
    def observer(
        self,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
    ) -> OrphanKernelCleanupObserver:
        """Create observer with mocked dependencies."""
        from ai.backend.agent.observer.orphan_kernel_cleanup import OrphanKernelCleanupObserver

        return OrphanKernelCleanupObserver(mock_agent, mock_valkey_client)

    @pytest.fixture
    def kernel_id(self) -> KernelId:
        """Generate a kernel ID."""
        return KernelId(uuid4())

    @pytest.fixture
    def session_id(self) -> SessionId:
        """Generate a session ID."""
        return SessionId(uuid4())

    # ===== Tests =====

    @pytest.mark.asyncio
    async def test_skip_when_no_agent_last_check(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
    ) -> None:
        """Test that observe() skips when agent_last_check is None."""
        mock_valkey_client.get_agent_last_check.return_value = None

        await observer.observe()

        # Should not call inject_container_lifecycle_event
        mock_agent.inject_container_lifecycle_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_when_no_kernels_in_registry(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
    ) -> None:
        """Test that observe() skips when kernel_registry is empty."""
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(return_value={})

        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_when_kernel_status_none(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
    ) -> None:
        """Test that observe() skips kernel when status is None (no Redis entry)."""
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: None,  # No Redis entry
        }

        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_when_kernel_last_check_is_none(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
    ) -> None:
        """Test that observe() skips kernel when last_check is None."""
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=900,
                last_check=None,  # last_check is None
                created_at=800,
            ),
        }

        await observer.observe()

        # Should not call inject_container_lifecycle_event when last_check is None
        mock_agent.inject_container_lifecycle_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_when_kernel_recently_checked(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
    ) -> None:
        """Test that observe() skips kernel when last_check is within threshold."""
        agent_last_check = 1000
        # kernel.last_check is within threshold (difference < ORPHAN_KERNEL_THRESHOLD_SEC)
        kernel_last_check = agent_last_check - (ORPHAN_KERNEL_THRESHOLD_SEC - 100)

        mock_valkey_client.get_agent_last_check.return_value = agent_last_check
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=kernel_last_check,
                last_check=kernel_last_check,
                created_at=0,
            ),
        }

        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_when_kernel_exactly_at_threshold(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
    ) -> None:
        """Test that observe() skips kernel when last_check is exactly at threshold."""
        agent_last_check = 1000
        # kernel.last_check is exactly at threshold (not orphan)
        kernel_last_check = agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC

        mock_valkey_client.get_agent_last_check.return_value = agent_last_check
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=kernel_last_check,
                last_check=kernel_last_check,
                created_at=0,
            ),
        }

        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_orphan_kernel(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
    ) -> None:
        """Test that observe() cleans up orphan kernel when condition is met."""
        agent_last_check = 1000
        # kernel.last_check exceeds threshold (orphan condition: last_check < agent - threshold)
        kernel_last_check = agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC - 100

        mock_valkey_client.get_agent_last_check.return_value = agent_last_check
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=kernel_last_check,
                last_check=kernel_last_check,
                created_at=0,
            ),
        }

        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_called_once_with(
            kernel_id,
            session_id,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
            suppress_events=True,
        )

    @pytest.mark.asyncio
    async def test_cleanup_multiple_orphan_kernels(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
    ) -> None:
        """Test that observe() cleans up multiple orphan kernels."""
        agent_last_check = 1000
        orphan_threshold = agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC - 100
        healthy_threshold = agent_last_check - (ORPHAN_KERNEL_THRESHOLD_SEC - 100)

        orphan_kernel_1 = KernelId(uuid4())
        orphan_kernel_2 = KernelId(uuid4())
        healthy_kernel = KernelId(uuid4())

        orphan_session_1 = SessionId(uuid4())
        orphan_session_2 = SessionId(uuid4())
        healthy_session = SessionId(uuid4())

        mock_valkey_client.get_agent_last_check.return_value = agent_last_check
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={
                orphan_kernel_1: MockKernel(session_id=orphan_session_1),
                orphan_kernel_2: MockKernel(session_id=orphan_session_2),
                healthy_kernel: MockKernel(session_id=healthy_session),
            }
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            orphan_kernel_1: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=orphan_threshold,
                last_check=orphan_threshold,
                created_at=0,
            ),
            orphan_kernel_2: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=orphan_threshold,
                last_check=orphan_threshold,
                created_at=0,
            ),
            healthy_kernel: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=healthy_threshold,
                last_check=healthy_threshold,
                created_at=0,
            ),
        }

        await observer.observe()

        # inject_container_lifecycle_event should be called twice (for orphan kernels only)
        assert mock_agent.inject_container_lifecycle_event.call_count == 2

        # Verify the correct kernels were cleaned up
        called_kernel_ids = {
            call[0][0] for call in mock_agent.inject_container_lifecycle_event.call_args_list
        }
        assert orphan_kernel_1 in called_kernel_ids
        assert orphan_kernel_2 in called_kernel_ids
        assert healthy_kernel not in called_kernel_ids

    @pytest.mark.asyncio
    async def test_continue_on_cleanup_failure(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
    ) -> None:
        """Test that observe() continues processing after inject_container_lifecycle_event failure."""
        agent_last_check = 1000
        orphan_threshold = agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC - 100

        orphan_kernel_1 = KernelId(uuid4())
        orphan_kernel_2 = KernelId(uuid4())

        orphan_session_1 = SessionId(uuid4())
        orphan_session_2 = SessionId(uuid4())

        mock_valkey_client.get_agent_last_check.return_value = agent_last_check
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={
                orphan_kernel_1: MockKernel(session_id=orphan_session_1),
                orphan_kernel_2: MockKernel(session_id=orphan_session_2),
            }
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            orphan_kernel_1: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=orphan_threshold,
                last_check=orphan_threshold,
                created_at=0,
            ),
            orphan_kernel_2: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=orphan_threshold,
                last_check=orphan_threshold,
                created_at=0,
            ),
        }

        # First call raises exception
        mock_agent.inject_container_lifecycle_event.side_effect = [
            Exception("Cleanup failed"),
            None,  # Second call succeeds
        ]

        # Should not raise, should continue processing
        await observer.observe()

        # Both calls should have been attempted
        assert mock_agent.inject_container_lifecycle_event.call_count == 2

    @pytest.mark.asyncio
    async def test_mixed_kernel_statuses(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
    ) -> None:
        """Test that observe() handles mixed kernel statuses correctly."""
        agent_last_check = 1000
        orphan_threshold = agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC - 100
        healthy_threshold = agent_last_check - (ORPHAN_KERNEL_THRESHOLD_SEC - 100)

        orphan_kernel = KernelId(uuid4())
        healthy_kernel = KernelId(uuid4())
        no_redis_kernel = KernelId(uuid4())

        orphan_session = SessionId(uuid4())
        healthy_session = SessionId(uuid4())
        no_redis_session = SessionId(uuid4())

        mock_valkey_client.get_agent_last_check.return_value = agent_last_check
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={
                orphan_kernel: MockKernel(session_id=orphan_session),
                healthy_kernel: MockKernel(session_id=healthy_session),
                no_redis_kernel: MockKernel(session_id=no_redis_session),
            }
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            orphan_kernel: KernelStatus(
                presence=HealthCheckStatus.STALE,  # Even stale kernel should be cleaned if orphan
                last_presence=orphan_threshold,
                last_check=orphan_threshold,
                created_at=0,
            ),
            healthy_kernel: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=healthy_threshold,
                last_check=healthy_threshold,
                created_at=0,
            ),
            no_redis_kernel: None,  # No Redis entry - skip
        }

        await observer.observe()

        # Only orphan kernel should be cleaned up
        mock_agent.inject_container_lifecycle_event.assert_called_once_with(
            orphan_kernel,
            orphan_session,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
            suppress_events=True,
        )

    def test_observe_interval(self, observer: OrphanKernelCleanupObserver) -> None:
        """Test that observe_interval returns correct value (5 minutes)."""
        assert observer.observe_interval() == 300.0

    def test_timeout(self, observer: OrphanKernelCleanupObserver) -> None:
        """Test that timeout returns correct value (30 seconds)."""
        assert observer.timeout() == 30.0

    def test_name(self, observer: OrphanKernelCleanupObserver) -> None:
        """Test that name returns correct value."""
        assert observer.name == "orphan_kernel_cleanup"
