"""
Tests for OrphanKernelCleanupObserver.

Mock-based unit tests for verifying orphan kernel cleanup logic.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Protocol
from unittest.mock import AsyncMock, Mock, PropertyMock
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

# The observer's own clock, patched by path so the debounce runs in test time.
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

    def is_kernel_creation_in_flight(self, kernel_id: KernelId) -> bool: ...


class TestOrphanKernelCleanupObserver:
    """Test cases for OrphanKernelCleanupObserver.

    Rule (a): a kernel the manager checked and then stopped checking is an orphan
    (kernel.last_check < agent_last_check - THRESHOLD). Rule (b): a running kernel no
    sweeping manager has ever checked is one after staying unknown for THRESHOLD.
    """

    @pytest.fixture
    def clock(self, monkeypatch: pytest.MonkeyPatch) -> _Clock:
        clock = _Clock()
        monkeypatch.setattr(_MONOTONIC, clock)
        return clock

    @pytest.fixture
    def mock_agent(self) -> AsyncMock:
        """Create a mock agent."""
        agent = AsyncMock(spec=AgentProtocol)
        agent.id = AgentId("test-agent-1")
        # Use PropertyMock for kernel_registry
        type(agent).kernel_registry = PropertyMock(return_value={})
        agent.inject_container_lifecycle_event = AsyncMock()
        agent.is_kernel_creation_in_flight = Mock(return_value=False)
        return agent

    @pytest.fixture
    def mock_valkey_client(self) -> AsyncMock:
        """Create a mock ValkeyScheduleClient."""
        client = AsyncMock()
        client.get_agent_last_check = AsyncMock(return_value=None)
        client.get_kernel_presence_batch = AsyncMock(return_value={})
        # Redis' clock and the manager's sweep mark, both at 1000: the manager sweeps now.
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
        """Test that observe() does not reap on the first pass when agent_last_check is None."""
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

    # ===== A kernel the manager has never checked (rule b) =====

    @staticmethod
    def _running_unchecked() -> KernelStatus:
        """A kernel this agent reports running that no manager sweep has ever stamped."""
        return KernelStatus(
            presence=HealthCheckStatus.HEALTHY,
            last_presence=1000,
            last_check=None,
            created_at=1000,
        )

    async def test_an_unknown_kernel_is_reaped_once_it_stays_unknown(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
    ) -> None:
        """What an agent restart leaves behind: the presence key expired while the agent was
        down, its presence observer recreated it without last_check, and the manager has no
        such kernel to check."""
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }

        await observer.observe()
        mock_agent.inject_container_lifecycle_event.assert_not_called()

        # Both clocks move, so a gate going stale during the debounce would show.
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC)
        mock_valkey_client.get_redis_time.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC
        mock_valkey_client.get_manager_sweep_epoch.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_called_once_with(
            kernel_id,
            session_id,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
            suppress_events=False,
        )

    async def test_an_unknown_kernel_the_manager_then_checks_is_kept(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
    ) -> None:
        # A kernel just started, which the manager has not swept yet: the debounce keeps it.
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }

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

    @pytest.mark.parametrize(
        "status",
        [
            pytest.param(None, id="no-presence-key"),
            pytest.param(
                KernelStatus(
                    presence=HealthCheckStatus.STALE,
                    last_presence=100,
                    last_check=None,
                    created_at=100,
                ),
                id="container-not-running",
            ),
            pytest.param(
                KernelStatus(
                    presence=None,
                    last_presence=None,
                    last_check=None,
                    created_at=100,
                ),
                id="presence-never-reported",
            ),
        ],
    )
    async def test_a_kernel_still_being_created_is_never_reaped_as_unknown(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
        status: KernelStatus | None,
    ) -> None:
        """The manager stamps only kernels it holds RUNNING. A kernel whose container is not
        running here (a long pull or create) is unchecked for a legitimate reason."""
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {kernel_id: status}

        await observer.observe()
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC * 10)
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    async def test_nothing_is_reaped_when_the_manager_sweep_went_stale(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
    ) -> None:
        """A stale sweep mark says the manager is not looking, which says nothing about any
        one kernel. Reaping on it would empty a healthy node while the manager restarts."""
        mock_valkey_client.get_agent_last_check.return_value = 1000
        mock_valkey_client.get_redis_time.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC + 1
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }

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
        clock: _Clock,
    ) -> None:
        """agent_last_check stays frozen when the orphan is the node's only kernel, since the
        manager has nothing on it to check; the cluster-wide mark is what keeps advancing."""
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }

        await observer.observe()
        mock_agent.inject_container_lifecycle_event.assert_not_called()

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
            suppress_events=False,
        )

    async def test_the_debounce_restarts_after_the_manager_goes_quiet(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
    ) -> None:
        # Time the manager was not looking is not time the kernel was unknown to a looking one.
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }
        await observer.observe()

        mock_valkey_client.get_redis_time.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC + 1
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC)
        await observer.observe()  # manager quiet: the debounce is dropped

        mock_valkey_client.get_redis_time.return_value = 1000
        await observer.observe()  # manager back: this is the first pass again

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    async def test_an_outage_that_outlives_the_agent_timestamp_still_reaps(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
    ) -> None:
        """agent:last_check expires after 20 minutes and is never rewritten for a node whose
        only kernel is the orphan, so rule (b) must not depend on it."""
        mock_valkey_client.get_agent_last_check.return_value = None
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }

        await observer.observe()
        mock_agent.inject_container_lifecycle_event.assert_not_called()

        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC)
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_called_once_with(
            kernel_id,
            session_id,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
            suppress_events=False,
        )

    async def test_a_kernel_whose_creation_is_in_flight_is_not_reaped_as_unknown(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
    ) -> None:
        # An init timeout above the threshold leaves a running, unchecked container initializing.
        mock_valkey_client.get_agent_last_check.return_value = 1000
        mock_agent.is_kernel_creation_in_flight.return_value = True
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }

        await observer.observe()
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC * 10)
        await observer.observe()

        mock_agent.is_kernel_creation_in_flight.assert_called_with(kernel_id)
        mock_agent.inject_container_lifecycle_event.assert_not_called()

    async def test_the_debounce_restarts_when_the_mark_goes_stale_without_agent_last_check(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
    ) -> None:
        # The stale pass returns early (no agent_last_check); it must still drop the wait timer.
        mock_valkey_client.get_agent_last_check.return_value = None
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }
        await observer.observe()  # fresh: the wait starts

        mock_valkey_client.get_redis_time.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC + 1
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC)
        await observer.observe()  # stale

        mock_valkey_client.get_redis_time.return_value = 1000
        await observer.observe()  # fresh again: the wait starts over
        mock_agent.inject_container_lifecycle_event.assert_not_called()

        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC)
        await observer.observe()
        mock_agent.inject_container_lifecycle_event.assert_called_once_with(
            kernel_id,
            session_id,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
            suppress_events=False,
        )

    # ===== Managers that never publish the sweep mark (rolling upgrade) =====

    async def test_rule_a_still_reaps_when_no_manager_publishes_the_mark(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
    ) -> None:
        """Against managers that predate the mark, the agent keeps the previous behavior."""
        agent_last_check = 1000
        kernel_last_check = agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC - 100
        mock_valkey_client.get_manager_sweep_epoch.return_value = None
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

    async def test_rule_b_is_off_when_no_manager_publishes_the_mark(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
    ) -> None:
        mock_valkey_client.get_manager_sweep_epoch.return_value = None
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }

        await observer.observe()
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC * 10)
        await observer.observe()

        mock_agent.inject_container_lifecycle_event.assert_not_called()

    # ===== A mark that was seen, then expired or went stale =====

    @staticmethod
    def _make_mark_not_fresh(mock_valkey_client: AsyncMock, mark: str) -> None:
        if mark == "expired":
            mock_valkey_client.get_manager_sweep_epoch.return_value = None
        else:
            mock_valkey_client.get_redis_time.return_value = 1000 + ORPHAN_KERNEL_THRESHOLD_SEC + 1

    @pytest.mark.parametrize("mark", ["expired", "stale"])
    async def test_rule_a_still_reaps_once_a_seen_mark_is_not_fresh(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        mark: str,
    ) -> None:
        """Rule (a) gates itself on agent_last_check, so the mark only switches rule (b)."""
        agent_last_check = 1000
        kernel_last_check = agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC - 100
        mock_valkey_client.get_agent_last_check.return_value = agent_last_check
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: KernelStatus(
                presence=HealthCheckStatus.HEALTHY,
                last_presence=agent_last_check,
                last_check=agent_last_check,
                created_at=0,
            ),
        }
        await observer.observe()  # the mark is seen fresh
        mock_agent.inject_container_lifecycle_event.assert_not_called()

        self._make_mark_not_fresh(mock_valkey_client, mark)
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

    @pytest.mark.parametrize("mark", ["expired", "stale"])
    async def test_rule_b_is_off_once_a_seen_mark_is_not_fresh(
        self,
        observer: OrphanKernelCleanupObserver,
        mock_agent: AsyncMock,
        mock_valkey_client: AsyncMock,
        kernel_id: KernelId,
        session_id: SessionId,
        clock: _Clock,
        mark: str,
    ) -> None:
        mock_valkey_client.get_agent_last_check.return_value = 1000
        type(mock_agent).kernel_registry = PropertyMock(
            return_value={kernel_id: MockKernel(session_id=session_id)}
        )
        mock_valkey_client.get_kernel_presence_batch.return_value = {
            kernel_id: self._running_unchecked()
        }
        await observer.observe()  # the mark is seen fresh

        self._make_mark_not_fresh(mock_valkey_client, mark)
        clock.advance(ORPHAN_KERNEL_THRESHOLD_SEC * 10)
        await observer.observe()

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
