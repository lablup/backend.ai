"""B10-B17. A session killed while it is still being built.

The create path claims overlay state in stages -- VNI, a /24 block, per-container IPs, the devices
themselves, the firewall rules that carry them -- and a kill lands between two of those stages.
What must hold is that the stage reached is the stage rolled back: a session aborted at PENDING
never had a VNI to return, and one aborted inside CREATING did, and both end with the host and
etcd exactly where they were.

The injection point is a *status*, not a delay. Creation on this rig takes ten seconds end to end
and CREATING lasts under two of them, so a scenario that slept a fixed number of seconds would
inject at a different stage on every run -- and pass without ever reaching the one it names.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import replace
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.testutils.dataplane.agent_control import AgentController
from ai.backend.testutils.dataplane.collectors.base import Resource
from ai.backend.testutils.dataplane.collectors.etcd_keys import flatten
from ai.backend.testutils.dataplane.guard import LeakGuard, compare
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.privnet_control import PrivnetController
from ai.backend.testutils.dataplane.probe import overlay_endpoints, reaches
from ai.backend.testutils.dataplane.session import (
    RUNNING,
    SessionDriver,
    SessionHandle,
    SessionSpec,
)

#: The statuses a session passes through on its way to running, in order. An abort scenario names
#: one of them as its injection point, and the order is what lets the helper tell "not there yet"
#: from "already past it" -- the second is a scenario that tested nothing and must say so.
_CREATE_PATH: tuple[str, ...] = (
    "PENDING",
    "SCHEDULED",
    "PREPARING",
    "PULLING",
    "PREPARED",
    "CREATING",
    RUNNING,
)

#: Fast enough to land inside CREATING, which lasts about two seconds here. The manager is polled,
#: so this is also the floor on how precisely any injection point can be hit.
_POLL = 0.1

#: How many times a scenario re-enqueues after the poll missed its stage. The window is real but
#: short, and a warm image can close it between two polls; retrying is what keeps that from
#: reading as a product failure, while the bound keeps a stage that is never observable from
#: looping forever.
_ABORT_ATTEMPTS = 4

#: A killed create must still reach a terminal status. Generous, because the point of the bound is
#: to name a session that hung -- the failure this catches sat in TERMINATING for 48 minutes.
_TERMINAL_BOUND = 240.0


class AbortOvershot(AssertionError):
    """The session passed the injection point before the poll saw it."""


async def _abort_at(
    driver: SessionDriver,
    handle: SessionHandle,
    target: str,
    *,
    linger: float = 0.0,
) -> str:
    """Force-terminate the session the moment it first shows `target`.

    `linger` pushes the kill deeper into the target status -- the agent builds the whole data
    plane inside CREATING, so where in that window the kill lands decides which half-built state
    the rollback has to deal with.

    Raises rather than killing late: a kill that arrives after RUNNING is a teardown, and a
    teardown passing under the name of an abort scenario is how a suite comes to report on a path
    it never took.
    """
    wanted = _CREATE_PATH.index(target)
    while True:
        status = await driver.status(handle.session_id)
        if status in _CREATE_PATH and _CREATE_PATH.index(status) >= wanted:
            if _CREATE_PATH.index(status) > wanted:
                raise AbortOvershot(
                    f"session {handle.name} was already {status} when the poll looked for "
                    f"{target}; this rig creates faster than {_POLL}s and the scenario would "
                    f"have injected at the wrong stage"
                )
            break
        if status in ("TERMINATED", "CANCELLED", "ERROR"):
            raise AbortOvershot(
                f"session {handle.name} ended {status} before reaching {target}, so no fault "
                f"was injected"
            )
        await asyncio.sleep(_POLL)
    if linger:
        await asyncio.sleep(linger)
    await driver.destroy(handle.session_id, wait=False, forced=True)
    return status


async def _enqueue_and_abort(
    driver: SessionDriver,
    spec: SessionSpec,
    name: str,
    target: str,
    *,
    linger: float = 0.0,
) -> SessionHandle:
    """Enqueue and kill at `target`, re-enqueueing when the poll missed the window.

    A missed window leaves a session that reached RUNNING, and it is torn down the ordinary way
    before the next attempt -- it is not the scenario's subject, and leaving it up would put its
    resources in the leak guard's delta.
    """
    overshot: AbortOvershot | None = None
    for attempt in range(_ABORT_ATTEMPTS):
        handle = await driver.enqueue(spec, name if attempt == 0 else f"{name}-r{attempt}")
        try:
            await _abort_at(driver, handle, target, linger=linger)
            return handle
        except AbortOvershot as error:
            overshot = error
            await driver.destroy(handle.session_id, wait=False)
            await driver.wait_terminal(handle.session_id, max_wait=_TERMINAL_BOUND)
    assert overshot is not None
    raise overshot


async def _members_holding(
    etcd: AsyncEtcd, session_id: UUID, *, at_least: int, max_wait: float = 30.0
) -> frozenset[str]:
    """The agents whose member record the session carries, once `at_least` of them are there.

    A cross-node scenario that a packed placement turned into a single-node one still tears down
    cleanly, so it passes -- having tested nothing. The member records are what say the overlay
    was genuinely held by more than one node, and they are written while the session is being
    built, which is exactly when this is called.
    """
    prefix = f"network/session/{session_id}/members/"
    deadline = asyncio.get_running_loop().time() + max_wait
    while True:
        found = frozenset(
            key.rsplit("/", 1)[-1] for key in flatten(prefix, await etcd.get_prefix(prefix) or {})
        )
        if len(found) >= at_least:
            return found
        if asyncio.get_running_loop().time() >= deadline:
            raise AssertionError(
                f"the session was held by {sorted(found)} after {max_wait}s, not by {at_least} "
                f"nodes; the scheduler packed it and this scenario would test nothing"
            )
        await asyncio.sleep(0.5)


async def _assert_no_session_keys(
    etcd: AsyncEtcd, session_id: UUID, *, max_wait: float = 90.0
) -> None:
    """The control-plane subtree of a session that is over must be gone.

    Polled, not read once: the allocation is given back by a retrying cleanup pass rather than by
    the call that terminated the session, and that pass declines until every node that held the
    VNI has withdrawn. The bound separates "a few seconds behind" from "kept for good".

    The leak guard would catch this as a delta too; this says which session and which key, which
    is the difference between a report someone can act on and one they have to re-derive.
    """
    prefix = f"network/session/{session_id}/"
    deadline = asyncio.get_running_loop().time() + max_wait
    while True:
        left = flatten(prefix, await etcd.get_prefix(prefix) or {})
        if not left:
            return
        if asyncio.get_running_loop().time() >= deadline:
            raise AssertionError(
                f"the aborted session still held its control-plane state {max_wait}s later:\n"
                + "\n".join(f"  {k}={v}" for k, v in sorted(left.items()))
            )
        await asyncio.sleep(2.0)


async def _settled_terminal(driver: SessionDriver, handle: SessionHandle) -> str:
    return await driver.wait_terminal(handle.session_id, max_wait=_TERMINAL_BOUND)


class TestForcedTerminationDuringCreate:
    """B10-B13. The manager is told to kill a session that is still being created.

    Every stage of the create path gets its own scenario, because each one has a different amount
    of overlay state to give back and they are undone by different code.
    """

    @pytest.fixture
    def pinned(self, session_spec: SessionSpec, primary_agent_id: str) -> SessionSpec:
        return replace(session_spec, agent_list=(primary_agent_id,))

    @pytest.mark.parametrize(
        ("scenario", "target"),
        [
            ("b10", "PENDING"),
            ("b11", "PREPARING"),
            ("b12", "CREATING"),
        ],
    )
    async def test_an_abort_gives_back_exactly_what_the_stage_claimed(
        self,
        scenario: str,
        target: str,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        etcd: AsyncEtcd,
        pinned: SessionSpec,
    ) -> None:
        """B10-B12: killed at PENDING, at PREPARING, and inside CREATING.

        The leak-guard fixture carries the assertion that matters -- the host and etcd are back
        where they started -- so the body's job is to make sure the kill actually landed at the
        stage the scenario names, and that the session then stopped.
        """
        handle = await _enqueue_and_abort(session_driver, pinned, f"dp-{scenario}", target)
        await _settled_terminal(session_driver, handle)
        await _assert_no_session_keys(etcd, handle.session_id)

    async def test_b13_a_cross_node_abort_releases_both_nodes(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        pair_agent_ids: tuple[str, ...],
        etcd: AsyncEtcd,
    ) -> None:
        """B13: the same kill while two nodes are still exchanging endpoints.

        A single-node abort is undone by one agent. Here the allocation is held jointly, and the
        manager refuses to release it until every node that took it confirms teardown -- the
        failure this guards against is one node never confirming, which leaves the session in
        TERMINATING holding its VNI and its /24 for as long as the agent stays up.
        """
        spec = replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=pair_agent_ids,
        )
        handle = await _enqueue_and_reach(session_driver, spec, "dp-b13", "CREATING")
        held_by = await _members_holding(etcd, handle.session_id, at_least=2)
        await session_driver.destroy(handle.session_id, wait=False, forced=True)
        await _settled_terminal(session_driver, handle)
        await _assert_no_session_keys(etcd, handle.session_id)
        assert len(held_by) >= 2, held_by


class TestAbortNextToALiveSession:
    """B14. The node the abort happens on is already carrying a session.

    Teardown works off node-global objects -- the vxlan device name is the VNI, the firewall
    chains are one per node, the block journal is one file -- so the interesting question is not
    whether the aborted session's state goes away but whether only its state goes away.
    """

    async def test_b14_a_neighbour_keeps_its_overlay(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        primary_agent_id: str,
        node: Node,
    ) -> None:
        # MULTI_NODE pinned to one agent, as in the isolation scenarios: that is what gives the
        # neighbour a VNI and an overlay bridge to have collateral damage done to.
        neighbour_spec = replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=(primary_agent_id,),
        )
        live_name = "dp-b14-live"
        async with session_driver.session(neighbour_spec, live_name) as neighbour:
            before, quiesced = await leak_guard.stable_snapshot()
            assert quiesced, "the host never settled with the neighbour up"
            endpoints_before = await overlay_endpoints(node, neighbour)
            assert len(endpoints_before) >= 2, (
                "the neighbour did not get two overlay endpoints on this node, so the "
                "collateral check would have nothing to protect"
            )

            victim = await _enqueue_and_abort(
                session_driver,
                replace(session_spec, agent_list=(primary_agent_id,)),
                "dp-b14-victim",
                "CREATING",
            )
            await _settled_terminal(session_driver, victim)

            after = await _wait_for_snapshot_to_include(leak_guard, before)
            report = compare(before, after)
            assert not report.collateral, (
                "aborting the neighbouring session destroyed state that belonged to the live "
                "one\n" + report.format()
            )
            assert await session_driver.status(neighbour.session_id) == RUNNING
            assert await overlay_endpoints(node, neighbour) == endpoints_before
            (pid, _), (_, peer_address) = endpoints_before[0], endpoints_before[1]
            assert await reaches(node, pid, peer_address), (
                "the live session's kernels stopped reaching each other over the overlay after "
                "a neighbouring create was aborted"
            )


async def _wait_for_snapshot_to_include(
    guard: LeakGuard, wanted: frozenset[Resource], *, max_wait: float = 60.0
) -> frozenset[Resource]:
    """Poll until nothing from `wanted` is missing, or the bound expires.

    The aborted session's own debris disappears on its own schedule, so comparing at a fixed
    moment reports whatever had not finished yet. What the scenario asserts on is the other
    direction -- state that vanished and should not have -- and that one is answered as soon as
    the snapshot contains everything it did before.
    """
    deadline = asyncio.get_running_loop().time() + max_wait
    while True:
        current = await guard.snapshot()
        if wanted <= current or asyncio.get_running_loop().time() >= deadline:
            return current
        await asyncio.sleep(1.0)


class TestProcessDeathDuringCreate:
    """B15-B16. Nothing tells the manager: the process doing the work simply dies.

    A forced terminate still runs the rollback. These do not -- the agent, or the privilege helper
    it drives the host through, is gone mid-build, and what is left has to be picked up by the
    recovery path on the way back in.
    """

    @pytest.fixture
    def pinned(self, session_spec: SessionSpec, primary_agent_id: str) -> SessionSpec:
        # The node `agent_control` restarts is the first one; an unpinned session that landed
        # elsewhere would have its create killed by a signal sent to a node holding none of it.
        return replace(session_spec, agent_list=(primary_agent_id,))

    async def test_b15_an_agent_killed_mid_create_reclaims_on_restart(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        agent_control: AgentController,
        etcd: AsyncEtcd,
        pinned: SessionSpec,
    ) -> None:
        """B15: SIGKILL while the agent is inside create, then bring it back.

        Half the data plane can exist with nothing left to remember it -- the kill takes the
        in-memory attachment records with it -- so the reclaim on the way back up is the only
        thing that can return it.
        """
        handle = await _enqueue_and_reach(session_driver, pinned, "dp-b15", "CREATING")
        await agent_control.stop(graceful=False)
        await agent_control.start()

        await session_driver.destroy(handle.session_id, wait=False, forced=True)
        await _settled_terminal(session_driver, handle)
        await _assert_no_session_keys(etcd, handle.session_id)

    async def test_b16_a_create_that_failed_without_its_privnet_is_given_back(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        agent_control: AgentController,
        privnet_control: PrivnetController,
        etcd: AsyncEtcd,
        session_spec: SessionSpec,
        pair_agent_ids: tuple[str, ...],
    ) -> None:
        """B16: the helper that owns the host's netlink and firewall is down when a create starts.

        The privnet is killed BEFORE the session is asked for, not during: a kill that lands after
        the node finished its setup leaves nothing half-built, and the scenario would pass without
        ever reaching what it is named for. Down from the start, the node publishes its membership,
        fails to build, and then fails to unwind -- and `stop()` withdraws that membership only
        once the data plane is actually gone, so the manager keeps refusing to give the session's
        VNI and /24 back for as long as the record stands.

        What must happen is that the node finishes the job when its helper returns. Measured before
        this was fixed: it did not -- the session held its allocation for 48 minutes, 28 of them
        after the privnet was already back, and only an agent restart ended it. Hence the privnet
        alone is restarted here, and the agent's pid is asserted unchanged: a rig that brings both
        back proves nothing.

        Cross-node on purpose. A single-node session's network is the agent's own bookkeeping; only
        an overlay session has an allocation the manager holds on this node's word.
        """
        overlay = replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=pair_agent_ids,
        )
        agent_before = await agent_control.pid()
        await privnet_control.kill()
        try:
            handle = await session_driver.enqueue(overlay, "dp-b16")
            # The create fails on the node without a helper. Which terminal status the manager
            # settles on is its business; that it settles at all is the first half of the claim.
            await session_driver.destroy(handle.session_id, wait=False, forced=True)
            await _settled_terminal(session_driver, handle)
        finally:
            await privnet_control.start()
        await _assert_no_session_keys(etcd, handle.session_id)
        assert await agent_control.pid() == agent_before, (
            "the agent restarted during this scenario, so it proves nothing about whether a "
            "half-built session is retried while the agent keeps running"
        )


async def _enqueue_and_reach(
    driver: SessionDriver,
    spec: SessionSpec,
    name: str,
    target: str,
) -> SessionHandle:
    """Enqueue and hand back the session while it is at `target`, retrying a missed window.

    The same bound as `_enqueue_and_abort`, for the scenarios whose fault is a signal rather than
    a terminate: they still have to fire it while the create is in flight.
    """
    overshot: AbortOvershot | None = None
    for attempt in range(_ABORT_ATTEMPTS):
        handle = await driver.enqueue(spec, name if attempt == 0 else f"{name}-r{attempt}")
        try:
            await _reach(driver, handle, target)
            return handle
        except AbortOvershot as error:
            overshot = error
            await driver.destroy(handle.session_id, wait=False)
            await driver.wait_terminal(handle.session_id, max_wait=_TERMINAL_BOUND)
    assert overshot is not None
    raise overshot


async def _reach(driver: SessionDriver, handle: SessionHandle, target: str) -> None:
    """Wait until the session is at `target`, without killing it."""
    wanted = _CREATE_PATH.index(target)
    while True:
        status = await driver.status(handle.session_id)
        if status in _CREATE_PATH and _CREATE_PATH.index(status) >= wanted:
            if _CREATE_PATH.index(status) > wanted:
                raise AbortOvershot(
                    f"session {handle.name} was already {status} when the poll looked for {target}"
                )
            return
        if status in ("TERMINATED", "CANCELLED", "ERROR"):
            raise AbortOvershot(f"session {handle.name} ended {status} before reaching {target}")
        await asyncio.sleep(_POLL)


class TestAbortChurn:
    """B17. The same kill, many times, landing wherever it lands.

    One scenario per stage proves each stage rolls back. This one asks the other question: whether
    anything accumulates across aborts -- a VNI not returned, a /24 never freed, an IP reserved for
    a container that was never created -- which a single pass cannot see and an exhausted pool
    reports much later as a session that will not schedule.
    """

    ROUNDS = 8

    async def test_b17_repeated_aborts_do_not_accumulate(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        primary_agent_id: str,
        etcd: AsyncEtcd,
    ) -> None:
        rng = random.Random(20260913)
        spec = replace(session_spec, agent_list=(primary_agent_id,))
        stages: list[str] = []
        for round_no in range(self.ROUNDS):
            target = rng.choice(("SCHEDULED", "PREPARED", "CREATING"))
            try:
                handle = await _enqueue_and_abort(
                    session_driver,
                    spec,
                    f"dp-b17-{round_no}",
                    target,
                    linger=rng.random(),
                )
                stages.append(target)
            except AbortOvershot:
                stages.append("missed")
                continue
            await _settled_terminal(session_driver, handle)
            await _assert_no_session_keys(etcd, handle.session_id)
        assert stages.count("missed") < self.ROUNDS, (
            f"every round missed its injection point: {stages}"
        )
