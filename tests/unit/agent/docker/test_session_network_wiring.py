"""How a Docker kernel reaches, and gives back, its session network (BEP-1062).

Every case here is one that leaks or hangs rather than erroring, which is why they are pinned:

* attaching after the command has started races the runner's own init and shows up as a hang at
  rendezvous, not as a failure here — so the attach must happen while the container is gated;
* a gate never released parks the container forever, with nothing to time it out;
* a container removed without a detach leaves its host veth, its IPAM address and its MASQ rule
  behind until the agent restarts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent.docker.gate import GATE_READY_TIMEOUT_SEC, stage_gate, wait_gated_pid
from ai.backend.agent.docker.session_network import make_docker_locator
from ai.backend.agent.gate import READY_MARKER
from ai.backend.agent.network.session_network import SessionNetwork


class _FakeContainer:
    """A container that is running and parked, unless told otherwise."""

    def __init__(self, pid: int = 4242, running: bool = True) -> None:
        self.pid = pid
        self.running = running

    async def show(self) -> dict[str, Any]:
        return {
            "State": {
                "Running": self.running,
                "Pid": self.pid if self.running else 0,
                "Status": "running" if self.running else "exited",
                "ExitCode": 0 if self.running else 1,
            }
        }


class TestWaitingForTheGate:
    async def test_it_returns_the_parked_pid(self, tmp_path: Path) -> None:
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        (gate_dir / READY_MARKER).touch()
        assert await wait_gated_pid(_FakeContainer(pid=777), gate_dir) == 777

    async def test_a_container_that_died_first_is_reported_not_waited_on(
        self, tmp_path: Path
    ) -> None:
        # A broken image or a bad command; without this it would be waited on for the whole
        # timeout and then reported as slow rather than as broken.
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        with pytest.raises(RuntimeError, match="exited before reaching the gate"):
            await wait_gated_pid(_FakeContainer(running=False), gate_dir)

    async def test_a_gate_that_never_opens_times_out(self, tmp_path: Path) -> None:
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        with pytest.raises(TimeoutError):
            await wait_gated_pid(_FakeContainer(), gate_dir, timeout_sec=0.3)

    async def test_a_parked_container_with_no_pid_is_refused(self, tmp_path: Path) -> None:
        # Docker reports 0 rather than null; attaching to PID 0 would target the host.
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        (gate_dir / READY_MARKER).touch()
        container = _FakeContainer(pid=0)
        with pytest.raises(RuntimeError, match="no PID"):
            await wait_gated_pid(container, gate_dir)

    def test_the_default_timeout_is_finite(self) -> None:
        # An unbounded wait here is a kernel creation that never returns and never errors.
        assert 0 < GATE_READY_TIMEOUT_SEC < 300


class TestGivingTheNetworkBack:
    async def test_detach_releases_the_recorded_attachment(self) -> None:
        detached: list[tuple[str, int]] = []

        class _Orchestrator:
            async def detach(self, container_id: str, *, plan: Any, task_pid: int) -> None:
                detached.append((container_id, task_pid))

        net = SessionNetwork(
            cast(Any, object()),
            agent_id="i-docker",
            host_ip="127.0.0.1",
            runtime=None,
            locator=make_docker_locator(),
            cni_runner=cast(Any, object()),
            backends={},
            local_subnets=cast(Any, object()),
            ipam=cast(Any, object()),
        )
        net._attachments["c1"] = ("s1", cast(Any, object()), 4242)
        net._orchestrators["s1"] = cast(Any, _Orchestrator())

        await net.detach_container("c1")

        assert detached == [("c1", 4242)]
        # Popped, so a second clean (the agent retries nothing, but a restart re-walks) cannot
        # detach a veth some other container has since been given.
        assert "c1" not in net._attachments

    async def test_detaching_a_container_we_never_attached_is_a_noop(self) -> None:
        # Every Docker kernel reaches clean_kernel, including the ones whose session network was
        # Docker's own; this must not raise for them.

        net = SessionNetwork(
            cast(Any, object()),
            agent_id="i-docker",
            host_ip="127.0.0.1",
            runtime=None,
            locator=make_docker_locator(),
            cni_runner=cast(Any, object()),
            backends={},
            local_subnets=cast(Any, object()),
            ipam=cast(Any, object()),
        )
        await net.detach_container("never-attached")

    async def test_a_failing_detach_does_not_block_removal(self) -> None:
        # The container is going either way; a detach hiccup that propagated would leave the
        # kernel in the registry with no container behind it.

        class _Orchestrator:
            async def detach(self, container_id: str, *, plan: Any, task_pid: int) -> None:
                raise RuntimeError("iproute2 said no")

        net = SessionNetwork(
            cast(Any, object()),
            agent_id="i-docker",
            host_ip="127.0.0.1",
            runtime=None,
            locator=make_docker_locator(),
            cni_runner=cast(Any, object()),
            backends={},
            local_subnets=cast(Any, object()),
            ipam=cast(Any, object()),
        )
        net._attachments["c1"] = ("s1", cast(Any, object()), 4242)
        net._orchestrators["s1"] = cast(Any, _Orchestrator())

        await net.detach_container("c1")
