"""A second create_kernel for a kernel this agent already has running.

The manager re-sends create_kernel for a kernel whose creation it never heard the end of. On a
multi-node session that is routine: the kernels are created in parallel, and if the *peer* misses
its readiness window the manager retries the whole start — including the node whose kernel came up
in a second and has been serving ever since.

Measured before this guard existed: the retry ran the whole creation again against a live
container, containerd answered `ALREADY_EXISTS: task "<kernel-id>": already exists`, and
create_kernel's failure path injected a DESTROY for the kernel that was up and answering. A
transient failure on one node took down the healthy kernel on the other.

The answer we already gave is the right answer to give again.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, cast

import pytest

from ai.backend.agent.agent import AbstractAgent

# The one the kernel object's `state` actually is -- `ai.backend.common.types` carries a
# duplicate of this enum, and the two are not the same object.
from ai.backend.agent.types import KernelLifecycleStatus
from ai.backend.common.types import KernelCreationResult, KernelId, SessionId


class _Kernel:
    def __init__(
        self,
        state: KernelLifecycleStatus,
        creation_result: KernelCreationResult | None,
    ) -> None:
        self.state = state
        self.creation_result = creation_result


class _WentPastTheGuard(Exception):
    """Raised from the first thing create_kernel does after the guard."""


class _Agent:
    """Only what the guard touches; everything below it raises."""

    def __init__(self) -> None:
        self.kernel_registry: dict[KernelId, _Kernel] = {}
        self.restarting_kernels: set[KernelId] = set()

    def track_create(self, kernel_id: KernelId, session_id: SessionId) -> Any:
        raise _WentPastTheGuard


def _result(kernel_id: KernelId) -> KernelCreationResult:
    return cast(
        KernelCreationResult,
        {
            "id": kernel_id,
            "kernel_host": "172.30.0.66",
            "repl_in_port": 2000,
            "repl_out_port": 2001,
            "stdin_port": 0,
            "stdout_port": 0,
            "service_ports": [],
            "container_id": str(kernel_id),
            "resource_spec": {},
            "scaling_group": "default",
            "agent_addr": "tcp://127.0.0.1:6011",
            "attached_devices": {},
        },
    )


async def _create(agent: _Agent, kernel_id: KernelId, *, restarting: bool = False) -> Any:
    ownership = cast(Any, _Ownership(kernel_id))
    return await AbstractAgent.create_kernel(
        cast(Any, agent),
        ownership,
        cast(Any, None),
        cast(Any, {}),
        cast(Any, {}),
        restarting=restarting,
        throttle_sema=asyncio.Semaphore(1),
    )


class _Ownership:
    def __init__(self, kernel_id: KernelId) -> None:
        self.kernel_id = kernel_id
        self.session_id = SessionId(uuid.uuid4())


class TestAKernelThatIsAlreadyRunningHere:
    async def test_the_previous_answer_is_replayed(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        expected = _result(kernel_id)
        agent.kernel_registry[kernel_id] = _Kernel(KernelLifecycleStatus.RUNNING, expected)

        assert await _create(agent, kernel_id) is expected

    async def test_nothing_below_the_guard_runs(self) -> None:
        """The point is not the return value but what it prevents: no second container is built
        over the live one, and no failure path fires a DESTROY at it."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel(
            KernelLifecycleStatus.RUNNING, _result(kernel_id)
        )

        await _create(agent, kernel_id)  # would raise _WentPastTheGuard otherwise


class TestWhatMustStillBeCreated:
    """The guard has to be narrow: every one of these is a create that must really happen."""

    async def test_a_kernel_this_agent_has_never_seen(self) -> None:
        agent = _Agent()

        with pytest.raises(_WentPastTheGuard):
            await _create(agent, KernelId(uuid.uuid4()))

    @pytest.mark.parametrize(
        "state",
        [
            KernelLifecycleStatus.PREPARING,
            KernelLifecycleStatus.TERMINATING,
        ],
    )
    async def test_a_kernel_that_is_not_running(self, state: KernelLifecycleStatus) -> None:
        """Still coming up, or on its way out — neither is a container that can be handed back."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel(state, _result(kernel_id))

        with pytest.raises(_WentPastTheGuard):
            await _create(agent, kernel_id)

    async def test_a_running_kernel_with_no_answer_to_replay(self) -> None:
        """A kernel restored by the agent's own recovery has no creation result of its own; there
        is nothing to reply with, so the create proceeds as it did before."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel(KernelLifecycleStatus.RUNNING, None)

        with pytest.raises(_WentPastTheGuard):
            await _create(agent, kernel_id)

    async def test_a_restart_recreates_the_container_on_purpose(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel(
            KernelLifecycleStatus.RUNNING, _result(kernel_id)
        )

        with pytest.raises(_WentPastTheGuard):
            await _create(agent, kernel_id, restarting=True)

    async def test_a_kernel_the_agent_is_restarting_is_left_to_the_restart(self) -> None:
        """`restarting=False` on the RPC but the agent is mid-restart: the restart owns the
        container, and its own create must not be short-circuited."""
        kernel_id = KernelId(uuid.uuid4())
        agent = _Agent()
        agent.kernel_registry[kernel_id] = _Kernel(
            KernelLifecycleStatus.RUNNING, _result(kernel_id)
        )
        agent.restarting_kernels.add(kernel_id)

        with pytest.raises(_WentPastTheGuard):
            await _create(agent, kernel_id)
