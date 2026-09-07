"""
Tests for OrphanKernelCleanupObserver.

Mock-based unit tests for verifying orphan kernel cleanup logic.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Protocol
from unittest.mock import AsyncMock, PropertyMock
from uuid import uuid4

import pytest

from ai.backend.agent.observer.orphan_kernel_cleanup import OrphanKernelCleanupObserver
from ai.backend.agent.types import LifecycleEvent
from ai.backend.common.clients.valkey_client.valkey_schedule import KernelStatus
from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    ORPHAN_KERNEL_THRESHOLD_SEC,
    HealthCheckStatus,
)
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import AgentId, KernelId, SessionId

#: The observer's own clock, patched by path so the debounce can be measured in test time.
_MONOTONIC = "ai.backend.agent.observer.orphan_kernel_cleanup.time.monotonic"


class _Clock:
    """A monotonic clock the test moves, so a debounce measured in minutes runs in no time."""

    def __init__(self) -> None:
        self._now = 0.0

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


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

    These tests verify the cleanup conditions:
    - agent_last_check must exist, and be fresh
    - a kernel the manager checked and stopped checking is an orphan:
      kernel.last_check < agent_last_check - THRESHOLD
    - a kernel the manager has NEVER checked is an orphan too, but only after it has stayed
      unknown for THRESHOLD seconds -- it is also what a kernel just created looks like
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
        # Redis' clock, and the manager's cluster-wide "I am looking at kernels" mark that the
        # gate actually reads. Both at 1000, so the manager is sweeping right now.
        client.get_redis_time = AsyncMock(return_value=1000)
        client.get_manager_sweep_epoch = AsyncMock(return_value=1000)
        return client

    @pytest.fixture
    def observer(
        self,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
    ) -> OrphanKernelCleanupObserver:
        """Create observer with mocked dependencies."""
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

    async def test_skip_when_kernel_status_none(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
    ) -> None:
        """Test that observe() does not reap on the first pass when status is None."""
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: None,  # No Redis entry
        }

        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    async def test_skip_when_kernel_last_check_is_none(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
    ) -> None:
        """Test that observe() does not reap on the first pass when last_check is None."""
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

    # ===== A kernel the manager has never checked =====

    async def test_an_unknown_kernel_is_reaped_once_it_stays_unknown(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """What an agent restart leaves behind: the presence key's TTL passed while the agent was
        down, the agent's own presence observer recreated it with no last_check, and the manager
        has no such kernel to check. Read as "not enough information" this survived forever, and
        held its allocation -- a later session on this node hung PREPARED with
        InsufficientResource."""
        clock = _Clock()
        monkeypatch.setattr(_MONOTONIC, clock)
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=1000,
                last_check=None,
                created_at=1000,
            ),
        }

        await observer.observe()
        mock_agent.inject_container_lifecycle_event.assert_not_called()

        # Both clocks, not just the debounce: a test that advanced only the monotonic one could
        # not see a liveness gate that goes stale while the debounce runs.
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC)
        mock_valkey_client.get_redis_time.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC
        mock_valkey_client.get_manager_sweep_epoch.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_called_once_with(
            kernel_id,
            session_id,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
            suppress_events=True,
        )

    async def test_an_unknown_kernel_the_manager_then_checks_is_kept(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # The other thing an unknown kernel can be: one just created, which the manager has not
        # got to yet. The debounce is what tells the two apart.
        clock = _Clock()
        monkeypatch.setattr(_MONOTONIC, clock)
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {kernel_id: None}

        await observer.observe()
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=1000,
                last_check=1000,
                created_at=900,
            ),
        }
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC * 10)
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    async def test_nothing_is_reaped_when_the_manager_stopped_checking_this_agent(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A stale agent_last_check says the MANAGER is not checking, which says nothing about any
        one kernel. Reaping on it would empty a healthy node the moment the manager restarts."""
        clock = _Clock()
        monkeypatch.setattr(_MONOTONIC, clock)
        mock_valkey_client.get_agent_last_check.return_value = 1000
        mock_valkey_client.get_redis_time.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC + 1
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {kernel_id: None}

        await observer.observe()
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC * 10)
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    async def test_nothing_is_reaped_when_the_manager_is_not_sweeping_at_all(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # The mark expires, so a manager that has stopped leaves nothing standing.
        clock = _Clock()
        monkeypatch.setattr(_MONOTONIC, clock)
        mock_valkey_client.get_agent_last_check.return_value = 1000
        mock_valkey_client.get_manager_sweep_epoch.return_value = None
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {kernel_id: None}

        await observer.observe()
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC * 10)
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    async def test_the_orphan_is_reaped_when_it_is_the_only_kernel_on_the_node(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The case the reap exists for, and the one a per-agent liveness gate deadlocks on.

        The manager stamps agent_last_check only for agents that still have a kernel it knows
        about. When the orphan is this node's ONLY kernel there is no such kernel, so that
        timestamp is frozen at whatever it was before the session was terminated -- and it goes
        on ageing while the debounce runs. A gate that asked it to be fresh would clear the
        debounce every pass and never reap the one node that needs it.
        """
        clock = _Clock()
        monkeypatch.setattr(_MONOTONIC, clock)
        # Frozen: the manager has had nothing on this agent to check since the outage.
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {kernel_id: None}

        await observer.observe()
        mock_agent.inject_container_lifecycle_event.assert_not_called()

        # Wall-clock and the debounce move together, and past the threshold: that is the point.
        # agent_last_check is now stale by more than the window, while the manager is still
        # sweeping -- it just has nothing on THIS agent to sweep.
        elapsed = ORPHAN_KERNEL_THRESHOLD_SEC + 1
        clock.advance(elapsed)
        mock_valkey_client.get_redis_time.return_value = 1000 + elapsed
        mock_valkey_client.get_manager_sweep_epoch.return_value = 1000 + elapsed
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_called_once_with(
            kernel_id,
            session_id,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
            suppress_events=True,
        )

    async def test_the_debounce_restarts_after_the_manager_goes_quiet(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Time spent while the manager was not checking is not time the kernel was "unknown to a
        # manager that was looking"; counting it would reap on the first pass after a restart.
        clock = _Clock()
        monkeypatch.setattr(_MONOTONIC, clock)
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {kernel_id: None}
        await observer.observe()

        mock_valkey_client.get_redis_time.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC + 1
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC)
        await observer.observe()  # manager quiet: the debounce is dropped

        mock_valkey_client.get_redis_time.return_value = 1000
        await observer.observe()  # manager back: this is the first pass again

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    def test_observe_interval(self, observer: OrphanKernelCleanupObserver) -> None:
        """Test that observe_interval returns correct value (5 minutes)."""
        assert observer.observe_interval() == 300.0

    def test_timeout(self, observer: OrphanKernelCleanupObserver) -> None:
        """Test that timeout returns correct value (30 seconds)."""
        assert observer.timeout() == 30.0

    def test_name(self, observer: OrphanKernelCleanupObserver) -> None:
        """Test that name returns correct value."""
        assert observer.name == "orphan_kernel_cleanup"
