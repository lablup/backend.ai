"""A11. An orphan whose session vanished while the agent was down must be reaped on recovery.

A node taken down for maintenance can have its sessions terminated in the manager while it is gone;
when it returns, its recovery re-adopts the still-running containers. A container whose session no
longer exists is an orphan holding resources -- until it is reaped, the agent's allocation map
disagrees with the manager, and a new session the manager schedules onto that node (believing the
capacity free) fails with InsufficientResource.

This was observed live on this branch: a kernel from a session terminated during a node outage kept
its cpu after the agent came back, and a later multi-node session hung PREPARED on that node because
the agent could not allocate what the manager thought was free.

The reap is the orphan-kernel observer's, not recovery's. Recovery cannot safely decide this: the
only signal it has is the session's network meta, and that reads as absent both when the session is
gone and when etcd is briefly unreadable or the manager is rebuilding the session -- destroying live
kernels on either would be worse than the leak. So the observer decides instead, on a signal that
cannot be transient: the manager is checking this agent and has never checked this kernel, and that
has stayed true for ORPHAN_KERNEL_THRESHOLD_SEC.

That puts the reap one debounce plus one observe interval after recovery, which is what this test
waits for. Before, no path reaped it at all: after a restart the presence key's TTL had passed and
the agent's own presence observer recreated it with no last_check, so every kernel hit a `continue`.

xfail(strict=False): the wait above has never been run on real nodes.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace

import pytest

from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    ORPHAN_KERNEL_THRESHOLD_SEC,
)
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.agent_control import AgentController
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

#: How long the reap can take: the observer has to see the kernel unknown for a whole threshold,
#: and it only looks once per `observe_interval`. Plus one interval of slack for where in the cycle
#: recovery happened to land.
_REAP_BOUND_SEC = ORPHAN_KERNEL_THRESHOLD_SEC + 300.0 * 2


class TestOrphanReap:
    @pytest.mark.xfail(
        reason=(
            "the orphan-kernel observer now reaps this, but on a debounce that has never been "
            "waited out on real nodes: the manager must be checking this agent throughout, and "
            "the reap lands one threshold plus one observe interval after recovery."
        ),
        strict=False,
    )
    async def test_a11_a_session_terminated_during_an_outage_is_reaped_on_recovery(
        self,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        primary_agent_id: str,
        node: Node,
        agent_control: AgentController,
    ) -> None:
        spec = replace(session_spec, agent_list=(primary_agent_id,))
        handle = await session_driver.create(spec, "dp-a11")
        (container_id,) = await probe.session_container_ids(node, handle)
        try:
            # Down for maintenance; the manager terminates the session while the node is gone
            # (forced -- there is no agent to confirm the teardown); then the node comes back.
            await agent_control.stop()
            await session_driver.destroy(handle.session_id, forced=True)
            await agent_control.start()

            assert await _container_gone(node, container_id, timeout=_REAP_BOUND_SEC), (
                f"the container {container_id} of a session terminated during the outage survived "
                f"{_REAP_BOUND_SEC}s after recovery -- the agent re-adopted an orphan and is still "
                "holding its resources, so the node's advertised capacity is a lie the next "
                "session will trip over"
            )
        finally:
            # The session is gone from the manager, so nothing else will reap this container; kill
            # its task and let the agent's own lifecycle sync release the allocation.
            for argv in (
                ["ctr", "-n", "backend-ai", "tasks", "kill", "-s", "SIGKILL", container_id],
                ["ctr", "-n", "backend-ai", "tasks", "delete", container_id],
                ["ctr", "-n", "backend-ai", "containers", "delete", container_id],
            ):
                await node.run(argv, check=False)


async def _container_gone(node: Node, container_id: str, *, timeout: float = 30.0) -> bool:
    """Poll until the node's containerd no longer lists ``container_id`` (bounded)."""
    deadline = time.monotonic() + timeout
    while True:
        listing = await node.run(["ctr", "-n", "backend-ai", "containers", "ls", "-q"])
        if container_id not in listing.lines:
            return True
        if time.monotonic() >= deadline:
            return False
        await asyncio.sleep(1.0)
