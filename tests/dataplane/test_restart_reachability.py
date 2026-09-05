"""A10. Reachability and isolation survive an agent restart.

A1/A2 assert the host state is byte-identical after a restart -- same devices, same rules. This
asserts the functional consequence a snapshot cannot: once the agent has recovered its kernels, they
still reach their gateway and remain isolated from a co-located neighbour. A recovery that rebuilt
the FORWARD rules subtly wrong could pass the byte-for-byte snapshot (right rule text) and still
misbehave here (wrong effect), or detach and reattach a kernel so its rules read identical but its
veth no longer carries traffic. The kernels themselves survive the restart on containerd -- this is
about whether the agent's recovery leaves their networking working, not whether they are alive.

Gated on ``agent_control`` (BAI_DATAPLANE_AGENT_START_CMD), like the other restart scenarios.
"""

from __future__ import annotations

from dataclasses import replace

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.agent_control import AgentController
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec


class TestReachabilitySurvivesRestart:
    async def test_a10_reachability_and_isolation_survive_an_agent_restart(
        self,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        primary_agent_id: str,
        node: Node,
        agent_control: AgentController,
    ) -> None:
        # Two kernels: a SINGLE_NODE session gets a LOCAL bridge of its own only when it has more
        # than one, and the isolation half of this scenario is about two such bridges. With one
        # kernel apiece both sessions sit on Docker's default bridge and reach each other, which
        # is not a regression -- it is what a session with no network of its own has always done.
        spec = replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.SINGLE_NODE,
            agent_list=(primary_agent_id,),
        )
        async with (
            session_driver.session(spec, "dp-a10-a") as a,
            session_driver.session(spec, "dp-a10-b") as b,
        ):
            (pid_a, _ip_a), *_ = await probe.local_endpoints(node, a)
            (_pid_b, ip_b), *_ = await probe.local_endpoints(node, b)
            gateway = await probe.default_gateway(node, pid_a)

            # Baseline before the restart: A reaches its own gateway, and not its neighbour.
            assert await probe.reaches(node, pid_a, gateway), (
                f"session A could not reach its gateway {gateway} before the restart; the scenario "
                "would be testing a kernel that never worked"
            )
            assert not await probe.reaches(node, pid_a, ip_b), (
                f"session A reached neighbour {ip_b} before the restart -- the cross-session block "
                "was already broken, so the after-restart check would prove nothing"
            )

            await agent_control.restart()

            # After recovery: re-resolve A's pid (the task survives, but recovery is what we test),
            # then assert the same two facts still hold.
            (pid_a_after, _), *_ = await probe.local_endpoints(node, a)
            gateway_after = await probe.default_gateway(node, pid_a_after)
            assert await probe.reaches(node, pid_a_after, gateway_after), (
                f"session A cannot reach its gateway {gateway_after} after the agent restarted -- "
                "recovery brought the agent back but left the kernel's networking broken"
            )
            assert not await probe.reaches(node, pid_a_after, ip_b), (
                f"session A reached neighbour {ip_b} after the restart -- recovery did not restore "
                "the cross-session FORWARD isolation (or restored it too broadly)"
            )
