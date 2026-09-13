"""C2/C4/C5. What the allocators and the per-session locks do when work overlaps.

Every scenario before this one runs alone: one session created, used, destroyed, and only then the
next. That is not how a cluster is used, and it is not where the allocator bugs are. A VNI handed
out twice, a /24 released by one session's teardown while another is claiming it, a data plane
deleted by a teardown that was racing the setup next to it -- none of them can happen in a suite
that never lets two sessions overlap.

The numbers are the rig's, not the scenario's: a keypair may hold 40 concurrent sessions here and
the smallest node carries about five kernels, so six two-kernel sessions is the useful shape --
enough overlap for the allocators to collide, inside what the cluster can actually place.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from typing import Any

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.testutils.dataplane.collectors.etcd_keys import flatten
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.session import (
    RUNNING,
    SessionDriver,
    SessionHandle,
    SessionSpec,
)

#: Sessions started at once. Two kernels each, so the overlay allocator hands out six VNIs and six
#: /24s while six teardowns are lining up behind them.
CONCURRENT_SESSIONS = 6

#: Terminate calls fired at one session at the same moment. The block is given back once; a second
#: release would hand the next session a subnet this one is still on.
DUPLICATE_TERMINATES = 4

#: A killed create must still reach a terminal status, and a concurrent run settles slower than a
#: lone one -- the bound is here to name a session that hung, not to measure the scheduler.
_TERMINAL_BOUND = 300.0


async def _overlay_allocations(etcd: AsyncEtcd) -> dict[str, dict[str, Any]]:
    """``session_id -> its meta`` for every session the control plane currently holds one for."""
    flat = flatten("network/session/", await etcd.get_prefix("network/session/") or {})
    metas: dict[str, dict[str, Any]] = {}
    for key, raw in flat.items():
        if not key.endswith("/meta"):
            continue
        try:
            parsed = json.loads(raw)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            metas[key.split("/")[2]] = parsed
    return metas


async def _endpoint_addresses(etcd: AsyncEtcd) -> list[tuple[str, str]]:
    """``(session_id, ip)`` for every overlay endpoint the manager has assigned."""
    flat = flatten("network/session/", await etcd.get_prefix("network/session/") or {})
    found: list[tuple[str, str]] = []
    for key, raw in flat.items():
        if "/endpoints/" not in key:
            continue
        try:
            parsed = json.loads(raw)
        except ValueError:
            continue
        if isinstance(parsed, dict) and (ip := parsed.get("ip")):
            found.append((key.split("/")[2], str(ip)))
    return found


def _duplicates(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    return [v for v in values if v in seen or seen.add(v)]  # type: ignore[func-returns-value]


async def _create_all(
    driver: SessionDriver, spec: SessionSpec, names: list[str]
) -> tuple[list[SessionHandle], list[BaseException]]:
    """Create concurrently, and hand back what came up even when one of them did not.

    A bare `asyncio.gather` raises the first failure and drops the handles of everything that
    succeeded -- and a scenario whose cleanup lives in a `finally` never reaches it, because the
    exception is raised before the name is bound. The sessions that did come up then stay up,
    holding their VNIs, their subnets and their devices, until somebody goes looking. Measured
    here: five of six, running half an hour later with no terminate ever sent.
    """
    results = await asyncio.gather(
        *(driver.create(spec, name) for name in names), return_exceptions=True
    )
    handles = [r for r in results if isinstance(r, SessionHandle)]
    failures = [r for r in results if isinstance(r, BaseException)]
    return handles, failures


async def _destroy_all(driver: SessionDriver, handles: list[SessionHandle]) -> None:
    await asyncio.gather(
        *(driver.destroy(h.session_id, wait=False) for h in handles), return_exceptions=True
    )
    waited = await asyncio.gather(
        *(driver.wait_terminal(h.session_id, max_wait=_TERMINAL_BOUND) for h in handles),
        return_exceptions=True,
    )
    # Every session is waited on before any failure is raised: one that will not stop must not
    # stop the others from being cleaned up.
    for outcome in waited:
        if isinstance(outcome, BaseException):
            raise outcome


class TestConcurrentAllocation:
    """C5: many sessions allocated and released at the same time."""

    @pytest.fixture
    def overlay_spec(self, session_spec: SessionSpec) -> SessionSpec:
        """Two kernels over the overlay, placed by the scheduler.

        Unpinned on purpose: this scenario is about the allocators, and pinning would decide the
        placement that decides which allocations collide.
        """
        return replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
        )

    async def test_c5_concurrent_sessions_never_share_a_vni_subnet_or_address(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        etcd: AsyncEtcd,
        overlay_spec: SessionSpec,
    ) -> None:
        """The claim the pool exists to make, read while every claimant is still holding.

        Checked with the sessions up rather than afterwards: two sessions that were handed the same
        VNI both tear down cleanly, and the host ends at its baseline either way. The damage is
        done while they are running -- two L2 segments that are one, and a subnet routed to two
        places.
        """
        handles, failures = await _create_all(
            session_driver,
            overlay_spec,
            [f"dp-c5-{index}" for index in range(CONCURRENT_SESSIONS)],
        )
        try:
            assert not failures, (
                f"{len(failures)} of {CONCURRENT_SESSIONS} concurrent creates did not reach "
                f"RUNNING: {failures}"
            )
            live = {str(h.session_id) for h in handles}
            metas = {sid: meta for sid, meta in (await _overlay_allocations(etcd)).items()}
            ours = {sid: meta for sid, meta in metas.items() if sid in live}
            assert len(ours) == CONCURRENT_SESSIONS, (
                f"only {len(ours)} of {CONCURRENT_SESSIONS} sessions had an overlay record; "
                "the rest were placed without one and this scenario would compare nothing"
            )

            vnis = [meta.get("vni") for meta in ours.values()]
            subnets = [meta.get("subnet") for meta in ours.values()]
            addresses = [ip for sid, ip in await _endpoint_addresses(etcd) if sid in live]

            assert not _duplicates(vnis), f"two live sessions were given the same VNI: {vnis}"
            assert not _duplicates(subnets), (
                f"two live sessions were given the same subnet: {subnets}"
            )
            assert not _duplicates(addresses), (
                f"two endpoints of concurrent sessions were given the same address: {addresses}"
            )
            assert len(addresses) == 2 * CONCURRENT_SESSIONS, (
                f"expected two endpoints per session, found {len(addresses)}"
            )
        finally:
            await _destroy_all(session_driver, handles)


class TestConcurrentTeardownOfOneSession:
    """C4: the same session told to stop by several callers at once."""

    async def test_c4_a_session_torn_down_many_times_gives_its_block_back_once(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        etcd: AsyncEtcd,
        session_spec: SessionSpec,
        pair_agent_ids: tuple[str, ...],
    ) -> None:
        """A double release is invisible at the moment it happens: the block goes back to the pool
        twice, and the damage arrives with the NEXT session, which is handed a subnet the previous
        one is still tearing down. What is checkable here is that the session ends once, its
        control-plane record is gone, and the host is back at its baseline -- and, after it, that
        the pool hands out something else."""
        overlay = replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=pair_agent_ids,
        )
        handle = await session_driver.create(overlay, "dp-c4")
        before = (await _overlay_allocations(etcd)).get(str(handle.session_id), {})
        assert before.get("vni"), "the session came up without an overlay record to release"

        results = await asyncio.gather(
            *(
                session_driver.destroy(handle.session_id, wait=False, forced=False)
                for _ in range(DUPLICATE_TERMINATES)
            ),
            return_exceptions=True,
        )
        unexpected = [r for r in results if isinstance(r, BaseException)]
        assert not unexpected, f"a concurrent terminate failed outright: {unexpected}"
        await session_driver.wait_terminal(handle.session_id, max_wait=_TERMINAL_BOUND)

        deadline = asyncio.get_running_loop().time() + 120.0
        while str(handle.session_id) in await _overlay_allocations(etcd):
            assert asyncio.get_running_loop().time() < deadline, (
                "the session's overlay record outlived its concurrent teardown"
            )
            await asyncio.sleep(2.0)

        # The pool must be able to hand the same VNI out again -- and to a session that works.
        after = await session_driver.create(overlay, "dp-c4-next")
        try:
            assert await session_driver.status(after.session_id) == RUNNING
        finally:
            await session_driver.destroy(after.session_id)


class TestTeardownRacingASetup:
    """C2: a session being torn down while another is being built on the same node.

    The node's LOCAL subnet journal and its block pool are shared, and the per-session lock is what
    keeps one session's teardown from releasing a block the other just claimed. A defect here does
    not fail the teardown; it fails the session that comes after.
    """

    async def test_c2_a_session_built_during_a_teardown_comes_up_whole(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        primary_agent_id: str,
    ) -> None:
        pinned = replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=(primary_agent_id,),
        )
        leaving = await session_driver.create(pinned, "dp-c2-leaving")
        _, arriving = await asyncio.gather(
            session_driver.destroy(leaving.session_id),
            session_driver.create(pinned, "dp-c2-arriving"),
        )
        try:
            assert await session_driver.status(arriving.session_id) == RUNNING, (
                "the session built alongside a teardown did not survive it"
            )
        finally:
            await session_driver.destroy(arriving.session_id)
