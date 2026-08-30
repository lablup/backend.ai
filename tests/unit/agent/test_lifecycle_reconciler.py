"""The periodic sweep that reconciles the kernel registry against what is actually running.

This is the agent's only safety net for a lifecycle event it missed — an agent restart, a crash, a
destroy that did not take. It had no direct test at all, which matters most for the branch this
module exists to exercise: `_handle_destroy_event` deliberately leaves a kernel in the registry
when its destroy raises, and the comment there promises "the periodic reconciler retries from both
directions". That promise is what these tests hold it to.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, cast

import pytest
from prometheus_client import REGISTRY

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.metrics.metric import SyncContainerLifecycleObserver
from ai.backend.agent.types import Container, LifecycleEvent
from ai.backend.common.docker import LabelName
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import (
    ContainerId,
    ContainerStatus,
    KernelId,
    KernelLifecycleStatus,
    SessionId,
)


class _Kernel:
    def __init__(
        self,
        session_id: SessionId,
        container_id: str | None,
        state: KernelLifecycleStatus,
        termination_reason: Any = None,
    ) -> None:
        self.session_id = session_id
        self.container_id = container_id
        self.state = state
        self.termination_reason = termination_reason


class _Observer:
    def __init__(self) -> None:
        self.triggered = 0
        self.successes: list[int] = []
        self.failures: list[str] = []
        self.unreclaimed: list[int] = []

    def observe_container_lifecycle_triggered(self, *, agent_id: Any) -> None:
        self.triggered += 1

    def observe_container_lifecycle_success(
        self, *, agent_id: Any, num_synced_kernels: int
    ) -> None:
        self.successes.append(num_synced_kernels)

    def observe_container_lifecycle_failure(
        self, *, agent_id: Any, exception: BaseException
    ) -> None:
        self.failures.append(type(exception).__name__)

    def observe_unreclaimed_containers(self, *, agent_id: Any, count: int) -> None:
        self.unreclaimed.append(count)


class _Agent:
    """Only what the sweep touches."""

    def __init__(self, containers: list[tuple[KernelId, Container]] | Exception) -> None:
        self.id = "i-test"
        self.registry_lock = asyncio.Lock()
        self.kernel_registry: dict[KernelId, _Kernel] = {}
        self.restarting_kernels: set[KernelId] = set()
        self.container_lifecycle_queue: asyncio.Queue[Any] = asyncio.Queue()
        self._ongoing_destruction_tasks: dict[KernelId, Any] = {}
        self._sync_container_lifecycle_observer = _Observer()
        self._containers = containers
        self.container_counts: list[int] = []
        self.error_events = 0

    async def enumerate_containers(self, status_filter: Any) -> list[tuple[KernelId, Container]]:
        if isinstance(self._containers, Exception):
            raise self._containers
        return self._containers

    async def set_container_count(self, container_count: int) -> None:
        self.container_counts.append(container_count)

    async def produce_error_event(self) -> None:
        self.error_events += 1


def _container(kernel_id: KernelId, session_id: SessionId, status: ContainerStatus) -> Container:
    return Container(
        id=ContainerId(str(kernel_id).replace("-", "")[:32].ljust(64, "0")),
        status=status,
        image="registry/py:3.12",
        labels={LabelName.SESSION_ID.value: str(session_id)},
        ports=[],
        backend_obj=None,
    )


async def _sweep(agent: _Agent) -> list[Any]:
    await AbstractAgent.sync_container_lifecycles(cast(Any, agent))
    out = []
    while not agent.container_lifecycle_queue.empty():
        out.append(agent.container_lifecycle_queue.get_nowait())
    return out


class TestAContainerTheRegistryDoesNotKnow:
    async def test_it_is_destroyed(self) -> None:
        """An orphan: it outlived an agent restart, or its creation failed after the container
        existed. Nothing else will ever come back for it."""
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        agent = _Agent([(kernel_id, _container(kernel_id, session_id, ContainerStatus.RUNNING))])

        events = await _sweep(agent)

        assert [(e.kernel_id, e.event) for e in events] == [(kernel_id, LifecycleEvent.DESTROY)]
        assert events[0].reason == KernelLifecycleEventReason.TERMINATED_UNKNOWN_CONTAINER

    async def test_a_restarting_kernel_is_left_alone(self) -> None:
        """A restart takes the container down and brings a new one up; the window between is not
        an orphan."""
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        agent = _Agent([(kernel_id, _container(kernel_id, session_id, ContainerStatus.RUNNING))])
        agent.restarting_kernels.add(kernel_id)

        assert await _sweep(agent) == []


class TestAKernelWhoseContainerIsGone:
    async def test_it_is_cleaned_with_container_not_found(self) -> None:
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        agent = _Agent([])
        agent.kernel_registry[kernel_id] = _Kernel(
            session_id, "c" * 64, KernelLifecycleStatus.RUNNING
        )

        events = await _sweep(agent)

        assert [(e.event, e.reason) for e in events] == [
            (LifecycleEvent.CLEAN, KernelLifecycleEventReason.CONTAINER_NOT_FOUND)
        ]

    async def test_a_kernel_still_being_prepared_is_left_alone(self) -> None:
        """It has no container yet by design; cleaning it would kill a starting session."""
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        agent = _Agent([])
        agent.kernel_registry[kernel_id] = _Kernel(
            session_id, None, KernelLifecycleStatus.PREPARING
        )

        assert await _sweep(agent) == []


class TestADeadContainer:
    async def test_it_is_cleaned(self) -> None:
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        agent = _Agent([(kernel_id, _container(kernel_id, session_id, ContainerStatus.EXITED))])

        events = await _sweep(agent)

        assert [e.event for e in events] == [LifecycleEvent.CLEAN]

    async def test_a_container_without_a_session_label_is_skipped(self) -> None:
        """The event stream carries every container on the node."""
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        container = _container(kernel_id, session_id, ContainerStatus.EXITED)
        container.labels = {}
        agent = _Agent([(kernel_id, container)])

        assert await _sweep(agent) == []


class TestADestroyThatDidNotTake:
    """The case the destroy handler leaves for this sweep, and the one it had no branch for.

    A kernel is TERMINATING only because `destroy_kernel` was entered for it, and the handler keeps
    it in the registry when that raised. Such a kernel is in the registry AND alive, so it falls
    into neither set-difference the sweep used to compute — nothing was re-issued and nothing was
    reported. Measured before this branch existed: containers in that state ran for weeks.
    """

    def _stuck(self) -> tuple[_Agent, KernelId]:
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        container = _container(kernel_id, session_id, ContainerStatus.RUNNING)
        agent = _Agent([(kernel_id, container)])
        agent.kernel_registry[kernel_id] = _Kernel(
            session_id,
            container.id,
            KernelLifecycleStatus.TERMINATING,
            termination_reason=KernelLifecycleEventReason.USER_REQUESTED,
        )
        return agent, kernel_id

    async def test_the_destroy_is_re_issued(self) -> None:
        agent, kernel_id = self._stuck()

        events = await _sweep(agent)

        assert [(e.kernel_id, e.event) for e in events] == [(kernel_id, LifecycleEvent.DESTROY)]

    async def test_the_original_reason_is_carried_over(self) -> None:
        """A retry is the same termination, not a new one — the user asked once."""
        agent, _ = self._stuck()

        events = await _sweep(agent)

        assert events[0].reason == KernelLifecycleEventReason.USER_REQUESTED

    async def test_it_is_reported(self) -> None:
        """The signal that was missing. A destroy failure happens in the queue handler, which no
        counter here watched, so a node that could not kill its containers looked idle."""
        agent, _ = self._stuck()

        await _sweep(agent)

        assert agent._sync_container_lifecycle_observer.unreclaimed == [1]

    async def test_a_destroy_still_in_flight_is_not_disturbed(self) -> None:
        """TERMINATING is also the state of a destroy running right now; re-issuing into that would
        run two destroys for one kernel concurrently."""
        agent, kernel_id = self._stuck()
        agent._ongoing_destruction_tasks[kernel_id] = object()

        assert await _sweep(agent) == []
        assert agent._sync_container_lifecycle_observer.unreclaimed == [0]

    async def test_a_running_kernel_is_not_touched(self) -> None:
        """The ordinary case: registry-known, alive, and nobody asked it to stop."""
        kernel_id, session_id = KernelId(uuid.uuid4()), SessionId(uuid.uuid4())
        container = _container(kernel_id, session_id, ContainerStatus.RUNNING)
        agent = _Agent([(kernel_id, container)])
        agent.kernel_registry[kernel_id] = _Kernel(
            session_id, container.id, KernelLifecycleStatus.RUNNING
        )

        assert await _sweep(agent) == []
        assert agent._sync_container_lifecycle_observer.unreclaimed == [0]

    async def test_zero_is_published_so_the_gauge_can_be_alerted_on(self) -> None:
        """A series that only appears while something is wrong cannot be alerted on, and "no
        series" is what this looked like for weeks."""
        agent = _Agent([])

        await _sweep(agent)

        assert agent._sync_container_lifecycle_observer.unreclaimed == [0]


class TestTheCounters:
    """trigger / success / failure are per-sweep and are read side by side. `success` used to be
    incremented by the number of kernels synced, so "1024 triggered, 292 succeeded" actually read
    "1024 sweeps, 292 kernels" — and an idle agent showed success frozen while trigger climbed."""

    async def test_an_idle_sweep_counts_as_one_success(self) -> None:
        agent = _Agent([])

        await _sweep(agent)

        obs = agent._sync_container_lifecycle_observer
        assert (obs.triggered, obs.successes) == (1, [0])

    async def test_the_kernel_count_is_reported_separately(self) -> None:
        agent = _Agent([
            (
                kid := KernelId(uuid.uuid4()),
                _container(kid, SessionId(uuid.uuid4()), ContainerStatus.EXITED),
            ),
            (
                kid2 := KernelId(uuid.uuid4()),
                _container(kid2, SessionId(uuid.uuid4()), ContainerStatus.EXITED),
            ),
        ])

        await _sweep(agent)

        assert agent._sync_container_lifecycle_observer.successes == [2]

    async def test_a_failed_sweep_is_counted_as_a_failure_not_a_success(self) -> None:
        agent = _Agent(RuntimeError("the runtime is gone"))

        await _sweep(agent)

        obs = agent._sync_container_lifecycle_observer
        assert obs.failures == ["RuntimeError"]
        assert obs.successes == []
        assert agent.error_events == 1

    async def test_a_sweep_that_raised_does_not_stop_the_next_one(self) -> None:
        """It runs on a timer; raising out of it would end the node's only safety net."""
        agent = _Agent(RuntimeError("transient"))

        await _sweep(agent)
        agent._containers = []
        await _sweep(agent)

        assert agent._sync_container_lifecycle_observer.triggered == 2
        assert agent._sync_container_lifecycle_observer.successes == [0]


class TestTheContainerCount:
    async def test_only_our_own_active_containers_are_counted(self) -> None:
        alive, dead = KernelId(uuid.uuid4()), KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())
        agent = _Agent([
            (alive, _container(alive, session_id, ContainerStatus.RUNNING)),
            (dead, _container(dead, session_id, ContainerStatus.EXITED)),
        ])

        await _sweep(agent)

        assert agent.container_counts == [1]


class TestTheObserverItself:
    """The counters as Prometheus actually publishes them.

    The sweep tests above talk to a stub observer, so they pin what the agent *reports* and not
    what a dashboard *reads* — the per-kernel/per-sweep mix-up lived entirely on the metric side
    and survives a stub (verified by mutation). These go through the real observer and read the
    registry back.
    """

    @pytest.fixture
    def observer(self) -> Any:
        return SyncContainerLifecycleObserver.instance()

    @pytest.fixture
    def agent_id(self) -> str:
        """A label nothing else in the process has used, so the samples start absent."""
        return f"i-test-{uuid.uuid4()}"

    def _sample(self, name: str, agent_id: str) -> float | None:
        return REGISTRY.get_sample_value(name, {"agent_id": agent_id})

    def test_a_sweep_that_synced_nothing_still_counts_as_one_success(
        self, observer: Any, agent_id: str
    ) -> None:
        """The reading that used to be impossible: an idle agent had trigger climbing and success
        frozen at zero, which looks exactly like an agent whose sweeps all fail."""
        observer.observe_container_lifecycle_triggered(agent_id=agent_id)
        observer.observe_container_lifecycle_success(agent_id=agent_id, num_synced_kernels=0)

        assert (
            self._sample("backendai_sync_container_lifecycle_trigger_count_total", agent_id) == 1.0
        )
        assert (
            self._sample("backendai_sync_container_lifecycle_success_count_total", agent_id) == 1.0
        )

    def test_trigger_and_success_stay_comparable_over_many_sweeps(
        self, observer: Any, agent_id: str
    ) -> None:
        """They are named as a pair and read as a pair; `success` incremented by a kernel count
        made "1024 triggered, 292 succeeded" mean "1024 sweeps, 292 kernels"."""
        for kernels in (0, 5, 0, 2):
            observer.observe_container_lifecycle_triggered(agent_id=agent_id)
            observer.observe_container_lifecycle_success(
                agent_id=agent_id, num_synced_kernels=kernels
            )

        assert (
            self._sample("backendai_sync_container_lifecycle_trigger_count_total", agent_id) == 4.0
        )
        assert (
            self._sample("backendai_sync_container_lifecycle_success_count_total", agent_id) == 4.0
        )

    def test_the_kernel_count_is_published_under_its_own_name(
        self, observer: Any, agent_id: str
    ) -> None:
        """It is still worth having — just not under a name that reads like a sweep count."""
        for kernels in (0, 5, 0, 2):
            observer.observe_container_lifecycle_success(
                agent_id=agent_id, num_synced_kernels=kernels
            )

        assert (
            self._sample("backendai_sync_container_lifecycle_synced_kernel_count_total", agent_id)
            == 7.0
        )

    def test_the_unreclaimed_gauge_tracks_the_latest_sweep(
        self, observer: Any, agent_id: str
    ) -> None:
        """A gauge, not a counter: it answers "how many are stuck right now", and it must fall back
        to zero when they are finally reclaimed."""
        observer.observe_unreclaimed_containers(agent_id=agent_id, count=2)
        assert (
            self._sample("backendai_sync_container_lifecycle_unreclaimed_containers", agent_id)
            == 2.0
        )

        observer.observe_unreclaimed_containers(agent_id=agent_id, count=0)
        assert (
            self._sample("backendai_sync_container_lifecycle_unreclaimed_containers", agent_id)
            == 0.0
        )

    def test_a_failure_is_labelled_with_what_went_wrong(self, observer: Any, agent_id: str) -> None:
        observer.observe_container_lifecycle_failure(
            agent_id=agent_id, exception=TimeoutError("slow")
        )

        assert (
            REGISTRY.get_sample_value(
                "backendai_sync_container_lifecycle_failure_count_total",
                {"agent_id": agent_id, "exception": "TimeoutError"},
            )
            == 1.0
        )
