"""A11. An orphan whose session vanished while the agent was down must be reaped on recovery.

A node taken down for maintenance can have its sessions terminated in the manager while it is gone;
when it returns, its recovery re-adopts the still-running containers. A container whose session no
longer exists is an orphan holding resources -- until it is reaped, the agent's allocation map
disagrees with the manager, and a new session the manager schedules onto that node (believing the
capacity free) fails with InsufficientResource.

This was observed live on this branch: a kernel from a session terminated during a node outage kept
its cpu after the agent came back, and a later multi-node session hung PREPARED on that node because
the agent could not allocate what the manager thought was free.

xfail: recovery re-adopts the container but does not reconcile it against the manager's session
state, so the orphan (and its allocation) survives. Remove the xfail when recovery reaps it.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace

import pytest

from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.agent_control import AgentController
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec


class TestOrphanReap:
    @pytest.mark.xfail(
        reason=(
            "agent recovery re-adopts a container whose session was terminated while the agent was "
            "down, holding its resources (observed live: a later session hung PREPARED with "
            "InsufficientResource). Recovery should reconcile recovered kernels against the "
            "manager's session state and reap the orphans."
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
        (container_id,) = await probe.session_container_ids(node, handle.name)
        try:
            # Down for maintenance; the manager terminates the session while the node is gone
            # (forced -- there is no agent to confirm the teardown); then the node comes back.
            await agent_control.stop()
            await session_driver.destroy(handle.session_id, forced=True)
            await agent_control.start()

            assert await _container_gone(node, container_id), (
                f"the container {container_id} of a session terminated during the outage survived "
                "recovery -- the agent re-adopted an orphan and is still holding its resources, so "
                "the node's advertised capacity is a lie the next session will trip over"
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
