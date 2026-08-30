"""What the containerd exit event records as the reason a kernel went away.

The runtime's event stream reports one thing for certain — the task ended — and nothing about the
cause. It used to fill that in with SELF_TERMINATED, which is worse than saying nothing: a destroy
that FAILED left the container running, so when it finally died (minutes later, by an operator's
hand) the agent filed it as "the kernel exited on its own". Measured: a containerd kernel the
runtime could not signal survived 40 minutes and was still recorded as `self-terminated`, and
nothing else in the system contradicted it.

The reason belongs to the kernel object, which carries what the destroy path set; only its absence
is the unknown.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.runtime.interface import TaskEvent
from ai.backend.agent.types import LifecycleEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import KernelId, SessionId


class _Kernel:
    def __init__(self, session_id: SessionId, termination_reason: Any = None) -> None:
        self.session_id = session_id
        self.termination_reason = termination_reason


class _Agent:
    """Only the collaborators the exit branch touches."""

    def __init__(self) -> None:
        self.kernel_registry: dict[KernelId, _Kernel] = {}
        self.injected: list[dict[str, Any]] = []

    async def inject_container_lifecycle_event(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event: LifecycleEvent,
        reason: KernelLifecycleEventReason,
        *,
        container_id: Any = None,
        exit_code: int | None = None,
    ) -> None:
        self.injected.append({
            "kernel_id": kernel_id,
            "event": event,
            "reason": reason,
            "exit_code": exit_code,
        })

    async def _session_id_of(self, container_id: str) -> SessionId | None:
        return None


async def _exit(agent: _Agent, kernel_id: KernelId, exit_code: int = 0) -> None:
    await ContainerdAgent._handle_task_event(
        cast(Any, agent), TaskEvent(kind="exit", container_id=str(kernel_id), exit_code=exit_code)
    )


class TestTheReasonOnExit:
    async def test_a_kernel_with_no_reason_is_recorded_as_unknown(self) -> None:
        """The container ended and nobody in this process asked for it. That is not the same as
        the kernel deciding to stop, and claiming so is a record that reads as the opposite of
        what happened."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel(SessionId(uuid.uuid4()))

        await _exit(agent, kernel_id)

        assert [e["reason"] for e in agent.injected] == [KernelLifecycleEventReason.UNKNOWN]

    async def test_the_reason_the_destroy_path_set_wins(self) -> None:
        """The positive control: when someone DID ask, that is what must be recorded — otherwise a
        test for the line above would also pass on a handler that always says UNKNOWN."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel(
            SessionId(uuid.uuid4()),
            termination_reason=KernelLifecycleEventReason.USER_REQUESTED,
        )

        await _exit(agent, kernel_id)

        assert [e["reason"] for e in agent.injected] == [KernelLifecycleEventReason.USER_REQUESTED]

    async def test_a_kernel_the_registry_lost_is_also_unknown(self) -> None:
        """The case the wrong default was measured on: the destroy failed, the kernel was dropped
        from the registry, and the container died much later. There is no reason to read."""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())
        agent = _Agent()

        async def _from_the_label(container_id: str) -> SessionId:
            return session_id

        agent._session_id_of = _from_the_label  # type: ignore[method-assign]

        await _exit(agent, kernel_id)

        assert [(e["event"], e["reason"]) for e in agent.injected] == [
            (LifecycleEvent.CLEAN, KernelLifecycleEventReason.UNKNOWN)
        ]

    async def test_the_exit_code_is_carried_through(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel(SessionId(uuid.uuid4()))

        await _exit(agent, kernel_id, exit_code=137)

        assert agent.injected[0]["exit_code"] == 137

    async def test_a_container_that_is_not_ours_is_ignored(self) -> None:
        """The event stream carries every task on the node; a non-UUID id is not a kernel."""
        agent = _Agent()

        await ContainerdAgent._handle_task_event(
            cast(Any, agent), TaskEvent(kind="exit", container_id="not-a-uuid")
        )

        assert agent.injected == []
