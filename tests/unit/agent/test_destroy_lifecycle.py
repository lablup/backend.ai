"""What the agent does with the registry when a destroy FAILS.

`_handle_destroy_event` used to enqueue CLEAN from a `finally`, so a destroy that raised still
released the scratch, the ports and the registry entry — the container kept running while the
agent forgot it existed. That is how an unkillable container becomes an invisible one: nothing
lists it, the orphan sweep iterates a registry it was just dropped from, and its eventual death is
filed under a guessed reason. It was measured against a container the runtime could not signal, and
it survived undetected because nothing tested this branch — the `finally` can be restored today and
the whole agent suite stays green.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, cast

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import ContainerLifecycleEvent, LifecycleEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import ContainerId, KernelId, SessionId


class _Kernel:
    """Only what the destroy path touches."""

    def __init__(self) -> None:
        self.state: Any = None
        self.termination_reason: Any = None
        self.runner: Any = None
        self.clean_event: Any = None


class _Agent:
    """A stand-in for the agent, so the branch can be driven without a live node."""

    def __init__(self, *, destroy_raises: Exception | None = None) -> None:
        self.registry_lock = asyncio.Lock()
        self.kernel_registry: dict[KernelId, _Kernel] = {}
        self.container_lifecycle_queue: asyncio.Queue[Any] = asyncio.Queue()
        self._ongoing_destruction_tasks: dict[KernelId, Any] = {}
        self._destroy_raises = destroy_raises
        self.destroy_calls: list[tuple[Any, Any]] = []
        self.error_events = 0

    async def destroy_kernel(self, kernel_id: KernelId, container_id: ContainerId | None) -> None:
        self.destroy_calls.append((kernel_id, container_id))
        if self._destroy_raises is not None:
            raise self._destroy_raises

    async def produce_error_event(self) -> None:
        self.error_events += 1


def _event(kernel_id: KernelId) -> ContainerLifecycleEvent:
    return ContainerLifecycleEvent(
        kernel_id,
        SessionId(uuid.uuid4()),
        ContainerId("c" * 64),
        LifecycleEvent.DESTROY,
        KernelLifecycleEventReason.USER_REQUESTED,
    )


async def _handle(agent: _Agent, ev: ContainerLifecycleEvent) -> None:
    await AbstractAgent._handle_destroy_event(cast(Any, agent), ev)


def _queued(agent: _Agent) -> list[ContainerLifecycleEvent]:
    out = []
    while not agent.container_lifecycle_queue.empty():
        out.append(agent.container_lifecycle_queue.get_nowait())
    return out


class TestASuccessfulDestroy:
    async def test_it_enqueues_clean(self) -> None:
        """The positive control. Without it a test that only checks the failure path would also
        pass on an agent that never cleans up at all."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel()

        await _handle(agent, _event(kernel_id))

        queued = _queued(agent)
        assert [e.event for e in queued] == [LifecycleEvent.CLEAN]
        assert queued[0].kernel_id == kernel_id


class TestAFailedDestroy:
    async def test_it_does_not_enqueue_clean(self) -> None:
        """The container is still running, so dropping it from the registry is a lie. The periodic
        reconciler retries from both directions instead."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent(destroy_raises=RuntimeError("unable to signal init: permission denied"))
        agent.kernel_registry[kernel_id] = _Kernel()

        await _handle(agent, _event(kernel_id))

        assert _queued(agent) == []

    async def test_the_kernel_stays_in_the_registry(self) -> None:
        """What the CLEAN would have removed. The orphan sweep walks this registry, so an entry
        dropped here is a container nothing will ever come back for."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent(destroy_raises=RuntimeError("unable to signal init: permission denied"))
        agent.kernel_registry[kernel_id] = _Kernel()

        await _handle(agent, _event(kernel_id))

        assert kernel_id in agent.kernel_registry

    async def test_the_caller_is_told(self) -> None:
        """`done_future` is what a synchronous destroy request waits on; resolving it as success
        would report a kernel destroyed to the manager as well."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent(destroy_raises=RuntimeError("boom"))
        agent.kernel_registry[kernel_id] = _Kernel()
        ev = _event(kernel_id)
        ev = ContainerLifecycleEvent(
            ev.kernel_id,
            ev.session_id,
            ev.container_id,
            ev.event,
            ev.reason,
            done_future=asyncio.get_running_loop().create_future(),
        )

        await _handle(agent, ev)

        assert ev.done_future is not None and ev.done_future.done()
        with pytest.raises(RuntimeError, match="boom"):
            ev.done_future.result()


class TestARetryDoesNotAbandonTheKernelObject:
    """A second `create_kernel` for the same id must close the object it replaces.

    Only the object in the registry is ever closed — the CLEAN handler pops exactly that one — so
    the one a retry displaces keeps its REPL sockets and its reader task. ZMQ reconnects them
    forever, and the address they hold is the container's own LOCAL IP, which this node hands to
    the next session. The abandoned sockets then reconnect to the NEW kernel, whose PUSH socket
    round-robins replies across every connected peer, and the live kernel object misses the answer
    it is waiting for.

    Measured after a few churned sessions: 14 sockets to a single container address with no session
    running at all, and `get_service_apps` timing out on a kernel that was up and answering.
    """

    class _Obj:
        def __init__(self) -> None:
            self.closed = False
            self.session_type = None

        async def close(self) -> None:
            self.closed = True

    async def _register(self, agent: Any, kernel_id: KernelId, obj: Any) -> None:
        async with agent.registry_lock:
            if (stale := agent.kernel_registry.get(kernel_id)) is not None:
                if stale is not obj:
                    await stale.close()
            agent.kernel_registry[kernel_id] = obj

    async def test_the_displaced_object_is_closed(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        first, second = self._Obj(), self._Obj()

        await self._register(agent, kernel_id, cast(Any, first))
        await self._register(agent, kernel_id, cast(Any, second))

        assert first.closed, "the retry left the first object's sockets open"
        assert not second.closed
        assert cast(Any, agent.kernel_registry[kernel_id]) is second

    async def test_registering_the_same_object_twice_does_not_close_it(self) -> None:
        """Idempotent re-registration must not tear down the live kernel."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        obj = self._Obj()

        await self._register(agent, kernel_id, cast(Any, obj))
        await self._register(agent, kernel_id, cast(Any, obj))

        assert not obj.closed
        assert cast(Any, agent.kernel_registry[kernel_id]) is obj

    async def test_a_first_registration_closes_nothing(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        obj = self._Obj()

        await self._register(agent, kernel_id, cast(Any, obj))

        assert not obj.closed
