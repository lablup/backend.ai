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
        spec = replace(session_spec, agent_list=(primary_agent_id,))
        async with (
            session_driver.session(spec, "dp-a10-a") as a,
            session_driver.session(spec, "dp-a10-b") as b,
        ):
            ((pid_a, _ip_a),) = await probe.local_endpoints(node, a.name)
            ((_pid_b, ip_b),) = await probe.local_endpoints(node, b.name)
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
            ((pid_a_after, _),) = await probe.local_endpoints(node, a.name)
            gateway_after = await probe.default_gateway(node, pid_a_after)
            assert await probe.reaches(node, pid_a_after, gateway_after), (
                f"session A cannot reach its gateway {gateway_after} after the agent restarted -- "
                "recovery brought the agent back but left the kernel's networking broken"
            )
            assert not await probe.reaches(node, pid_a_after, ip_b), (
                f"session A reached neighbour {ip_b} after the restart -- recovery did not restore "
                "the cross-session FORWARD isolation (or restored it too broadly)"
            )
