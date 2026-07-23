"""A. Agent restart, single node.

Docker never had this problem: dockerd owns its own data plane and restores it itself, so an
agent restart cost it nothing. The containerd backend took that job over, which is why the
expectations here come from the code's invariants and not from Docker parity -- and why every
destructive defect this branch has shipped landed on exactly this path.

**Not yet run against a live agent.** These were written while the reference host's privnet was
down, so no session could be created at all. The bodies encode the invariants and the fixtures
are exercised by the harness self-checks, but the scenarios themselves are unverified until they
run somewhere the data plane works. Do not read a green CI here as evidence: with the environment
variables unset every test below skips.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ai.backend.testutils.dataplane.agent_control import AgentController
from ai.backend.testutils.dataplane.collectors.base import Resource
from ai.backend.testutils.dataplane.guard import LeakGuard, compare
from ai.backend.testutils.dataplane.session import RUNNING, SessionDriver, SessionSpec


async def _stable(guard: LeakGuard) -> frozenset[Resource]:
    snapshot, quiesced = await guard.stable_snapshot()
    assert quiesced, (
        "the host never stopped changing, so a before/after comparison would report the "
        "settling as a change; something else is creating or destroying sessions"
    )
    return snapshot


class TestAgentRestart:
    """A1-A3: a restart must be invisible to the data plane, and must not cost the ability to
    tear it down afterwards."""

    @pytest.fixture
    def two_kernel_spec(self, session_spec: SessionSpec) -> SessionSpec:
        return replace(session_spec, cluster_size=2)

    async def test_a1_graceful_restart_leaves_the_data_plane_identical(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        agent_control: AgentController,
        two_kernel_spec: SessionSpec,
    ) -> None:
        """The whole of `recover()` in one assertion: the host is where it was.

        Comparing snapshots rather than listing what should exist is deliberate. A restart that
        rebuilt the bridge with a different name, or dropped one FDB entry, is a difference --
        and enumerating everything a session should own by hand would go stale the first time the
        backend gained a resource.
        """
        async with session_driver.session(two_kernel_spec, "dp-a1") as handle:
            before = await _stable(leak_guard)
            await agent_control.restart(graceful=True)
            after = await _stable(leak_guard)

            report = compare(before, after)
            assert report.clean, "the restart changed the data plane\n" + report.format()
            assert await session_driver.status(handle.session_id) == RUNNING

    async def test_a2_ungraceful_restart_leaves_the_data_plane_identical(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        agent_control: AgentController,
        two_kernel_spec: SessionSpec,
    ) -> None:
        """SIGKILL, so nothing runs on the way out. A1 could pass on a graceful path that
        persisted state during shutdown; this one can only pass if recovery reads ground truth.
        """
        async with session_driver.session(two_kernel_spec, "dp-a2") as handle:
            before = await _stable(leak_guard)
            await agent_control.restart(graceful=False)
            after = await _stable(leak_guard)

            report = compare(before, after)
            assert report.clean, "the SIGKILL restart changed the data plane\n" + report.format()
            assert await session_driver.status(handle.session_id) == RUNNING

    async def test_a3_teardown_after_a_restart_returns_everything(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        agent_control: AgentController,
        two_kernel_spec: SessionSpec,
    ) -> None:
        """The half A1 cannot see. A restart can leave the host looking right while the agent has
        lost the attachment records it needs to detach with -- and the cost only shows at
        teardown, as a host veth and an IPAM lease held for the life of the node.

        The assertion lives in the `leak_guard` fixture: it fails the test if the host has not
        returned to the baseline it took before the session existed.
        """
        async with session_driver.session(two_kernel_spec, "dp-a3"):
            await agent_control.restart(graceful=False)


class TestScratchLifecycle:
    """A8: does a scratch directory survive a normal teardown?

    BUG3 reproduced a scratch surviving an *aborted* creation. BUG4 is a scratch that survived a
    kernel that terminated normally, seen on the reference host twelve days after the fact. This
    scenario is what separates them: if it passes, BUG3 is specific to the rollback path; if it
    fails, both have the same root and the fix is one.
    """

    async def test_a8_a_normal_lifecycle_returns_its_scratch(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
    ) -> None:
        async with session_driver.session(session_spec, "dp-a8"):
            pass
        report = await leak_guard.settle()
        leaked_scratch = [r for r in report.leaked if r.kind == "scratch-dir"]
        assert not leaked_scratch, (
            "a kernel that terminated normally left its scratch behind (BUG4)\n" + report.format()
        )


class TestPublishedPorts:
    """A9: the port pool has no journal of its own.

    `port_forward.py` states the invariant outright -- "iptables itself is the record", so a
    restarted agent enumerates published ports from the rules' `bai:<container_id>` comments. The
    reference host proved the failure mode is real: with the privnet down the agent logged
    "could not read published ports; the port pool may leak" every thirty seconds for two days.
    """

    async def test_a9_published_ports_survive_a_restart(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        agent_control: AgentController,
        session_spec: SessionSpec,
    ) -> None:
        async with session_driver.session(session_spec, "dp-a9"):
            before = await _stable(leak_guard)
            rules_before = frozenset(r for r in before if r.kind == "iptables")
            assert rules_before, (
                "the session published no port-forward rules, so this scenario would pass "
                "vacuously; give the spec a service to publish"
            )

            await agent_control.restart(graceful=False)

            after = await _stable(leak_guard)
            rules_after = frozenset(r for r in after if r.kind == "iptables")
            assert rules_after == rules_before, (
                "the restart changed the published-port rules\n"
                + compare(rules_before, rules_after).format()
            )
