"""Per-session cluster-network coordinator (BEP-1062).

Owns the membership lifecycle for a session network: reads the session meta, drives
the backend's host-level setup, publishes this agent's membership, and reconciles
peers from the etcd ``members/`` prefix (driving the backend's idempotent
``add_peer``/``del_peer``). The v2 backend is a stateless data-plane executor and
never watches etcd itself — that ownership lives here (see Decision Log, BEP-1062).
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable
from contextlib import aclosing
from typing import TYPE_CHECKING, Any

from ai.backend.common.network.keys import (
    endpoints_prefix,
    member_key,
    members_prefix,
    session_prefix,
)
from ai.backend.common.network.types import EndpointAddr, Member, SessionNetMeta
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
    from ai.backend.common.etcd import AbstractKVStore

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# The watch loop re-subscribes after any failure, backing off so a persistent error (a broken etcd,
# a device op that always fails) does not spin, while a transient one recovers within a second.
_WATCH_RETRY_BACKOFF = 1.0
_WATCH_RETRY_BACKOFF_MAX = 30.0

# How often each session re-converges from etcd regardless of the watch. The watch cannot see a
# change published in the window between a reconcile's read and its own subscribe, and if nothing
# else in the subtree ever changes, no event will ever correct it — so convergence cannot rest on
# the watch alone. Two etcd reads per session per tick; device ops only on an actual difference.
_RECONCILE_INTERVAL = 15.0


def _decode_member(agent_id: str, raw: str) -> Member:
    return Member.from_etcd_payload(agent_id, json.loads(raw))


def _decode_endpoint(container_id: str, raw: str) -> EndpointAddr:
    data = json.loads(raw)
    return EndpointAddr(
        container_id=container_id,
        ip=data["ip"],
        mac=data["mac"],
        agent_id=data["agent_id"],
    )


class SessionNetworkCoordinator:
    _etcd: AbstractKVStore
    _backend: AbstractNetworkAgentPluginV2[Any]
    _agent_id: str
    _applied: dict[str, dict[str, Member]]
    _applied_endpoints: dict[str, dict[str, tuple[EndpointAddr, str]]]
    _watch_tasks: dict[str, asyncio.Task[None]]
    # The periodic re-converge task per session (see _reconcile_periodically).
    _sweep_tasks: dict[str, asyncio.Task[None]]

    def __init__(
        self,
        etcd: AbstractKVStore,
        backend: AbstractNetworkAgentPluginV2[Any],
        agent_id: str,
    ) -> None:
        self._etcd = etcd
        self._backend = backend
        self._agent_id = agent_id
        self._applied = {}
        self._applied_endpoints = {}
        self._watch_tasks = {}
        self._sweep_tasks = {}

    async def start(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Bring up this node's data plane for the session, publish membership, apply
        existing peers, and begin watching for membership changes."""
        await self._backend.setup_session_network(meta, self_member)
        await self._begin(meta, self_member)

    async def resume(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Re-attach to a session whose data plane survived an agent restart.

        Identical to `start` except the backend adopts the running devices instead of rebuilding
        them. The membership republish and the reconciles are what make this necessary rather than
        optional: without them the restarted node stops reacting to peers joining or leaving, and
        cross-node overlay traffic silently stops following the cluster."""
        await self._backend.adopt_session_network(meta, self_member)
        await self._begin(meta, self_member)

    async def _begin(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Publish membership, apply what is already published, and start watching."""
        await self._write_member(meta.session_id, self_member)
        self._applied[meta.session_id] = {}
        self._applied_endpoints[meta.session_id] = {}
        await self.reconcile_peers(meta.session_id)
        await self.reconcile_endpoints(meta.session_id)
        self._watch_tasks[meta.session_id] = asyncio.create_task(self._watch(meta.session_id))
        self._sweep_tasks[meta.session_id] = asyncio.create_task(
            self._reconcile_periodically(meta.session_id)
        )

    async def _reconcile_periodically(self, session_id: str) -> None:
        """Re-converge from etcd on a timer, whatever the watch is doing.

        The watch cannot be the only path to convergence. It streams from the revision current when
        it subscribes, so anything published between a reconcile's read and the (re)subscribe that
        follows it appears in neither — and if nothing else in the subtree ever changes, no event
        ever arrives to correct it. That is exactly the case this whole class exists to serve: a
        late worker publishes its member and endpoint keys, and nothing changes afterwards. It would
        wait forever at rendezvous over a gap of milliseconds.

        A periodic diff makes that gap self-healing instead of fatal. It is cheap: two etcd reads,
        and a device op only when something actually differs.
        """
        while True:
            await asyncio.sleep(_RECONCILE_INTERVAL)
            try:
                await self.reconcile_peers(session_id)
                await self.reconcile_endpoints(session_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("periodic reconcile failed for session {}", session_id)

    async def stop(self, session_id: str, *, teardown_data_plane: bool = True) -> None:
        """Stop watching, remove this node's membership, and tear down the data plane.

        `teardown_data_plane=False` withdraws from the session without touching the devices — for
        the case where they are not this agent's alone to delete: two agents on one host share the
        session's bridge and its LOCAL block (both keyed on the node's shared journal), so the one
        whose kernels leave first must leave them standing for the other.
        """
        for tasks in (self._watch_tasks, self._sweep_tasks):
            if task := tasks.pop(session_id, None):
                # Await the cancellation so a trailing reconcile can't run after teardown and the
                # task's exception is retrieved (no "never retrieved" warning).
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    # It already died of something else. Log it and carry on: re-raising here would
                    # skip the teardown below and leak this node's membership key and its devices.
                    log.exception("session network task for {} ended in error", session_id)
        await self._etcd.delete(member_key(session_id, self._agent_id))
        if teardown_data_plane:
            await self._backend.teardown_session_network(session_id)
        self._applied.pop(session_id, None)
        self._applied_endpoints.pop(session_id, None)

    async def reconcile_peers(self, session_id: str) -> None:
        """Diff the published members against what has been applied and drive the
        backend's add_peer/del_peer accordingly. Idempotent; safe to call repeatedly.

        A device op that fails is isolated to its own peer: the record is left as it was, so the
        next reconcile retries exactly that peer, and the remaining peers -- and the endpoint
        reconcile that follows -- still get applied. One unroutable member used to abort the whole
        pass, leaving this node with no FDB/ARP for anybody.
        """
        members = await self._read_members(session_id)
        applied = self._applied.setdefault(session_id, {})
        current = {aid: m for aid, m in members.items() if aid != self._agent_id}

        for agent_id, member in current.items():
            if applied.get(agent_id) == member:
                continue
            # A peer whose record CHANGED (the manager pre-seeds a member from the agent's published
            # VTEP key, and the agent itself publishes one when it joins -- they can differ) needs
            # its old FDB entry withdrawn, or this node keeps unicasting to the stale endpoint.
            if (stale := applied.get(agent_id)) is not None:
                await self._try(session_id, "del_peer", self._backend.del_peer(session_id, stale))
            try:
                await self._backend.add_peer(session_id, member)
            except Exception:
                log.exception("add_peer failed for {} in session {}", agent_id, session_id)
                applied.pop(agent_id, None)  # unapplied: the next reconcile retries this peer
                continue
            applied[agent_id] = member
        for agent_id in list(applied.keys()):
            if agent_id not in current:
                # Drop the record only once the device op has landed, so a failed withdrawal is
                # retried instead of being forgotten (a stale FDB entry unicasts to a dead VTEP).
                if await self._try(
                    session_id, "del_peer", self._backend.del_peer(session_id, applied[agent_id])
                ):
                    applied.pop(agent_id, None)

    async def _try(self, session_id: str, op: str, coro: Awaitable[None]) -> bool:
        """Run one device op, logging and swallowing its failure. True when it landed."""
        try:
            await coro
        except Exception:
            log.exception("{} failed in session {}", op, session_id)
            return False
        return True

    async def reconcile_endpoints(self, session_id: str) -> None:
        """Program FDB + ARP for every remote endpoint in the ``endpoints/`` table
        (proactive; no BUM flood), and remove entries for departed endpoints. Skips this
        node's own endpoints, and skips remotes whose VTEP is not yet published (a later
        watch tick retries). Idempotent; safe to call repeatedly."""
        endpoints = await self._read_endpoints(session_id)
        members = await self._read_members(session_id)
        applied = self._applied_endpoints.setdefault(session_id, {})

        current: dict[str, tuple[EndpointAddr, str]] = {}
        for container_id, endpoint in endpoints.items():
            if endpoint.agent_id == self._agent_id:
                continue
            member = members.get(endpoint.agent_id)
            if member is None or member.vtep_ip is None:
                continue
            current[container_id] = (endpoint, member.vtep_ip)

        for container_id, (endpoint, vtep_ip) in current.items():
            if applied.get(container_id) == (endpoint, vtep_ip):
                continue
            # Same reasoning as reconcile_peers: an endpoint that moved (a kernel re-created on
            # another node, so its MAC or VTEP changed) must have the old entry withdrawn first,
            # and one failing op must not take the rest of the table with it.
            if (stale := applied.get(container_id)) is not None:
                await self._try(
                    session_id,
                    "del_endpoint",
                    self._backend.del_endpoint(
                        session_id, ip=stale[0].ip, mac=stale[0].mac, vtep_ip=stale[1]
                    ),
                )
            if await self._try(
                session_id,
                "add_endpoint",
                self._backend.add_endpoint(
                    session_id, ip=endpoint.ip, mac=endpoint.mac, vtep_ip=vtep_ip
                ),
            ):
                applied[container_id] = (endpoint, vtep_ip)
            else:
                applied.pop(container_id, None)  # retried by the next reconcile
        for container_id in list(applied.keys()):
            if container_id not in current:
                endpoint, vtep_ip = applied[container_id]
                if await self._try(
                    session_id,
                    "del_endpoint",
                    self._backend.del_endpoint(
                        session_id, ip=endpoint.ip, mac=endpoint.mac, vtep_ip=vtep_ip
                    ),
                ):
                    applied.pop(container_id, None)

    async def _read_endpoints(self, session_id: str) -> dict[str, EndpointAddr]:
        raw = await self._etcd.get_prefix(endpoints_prefix(session_id))
        endpoints: dict[str, EndpointAddr] = {}
        for container_id, value in dict(raw).items():
            if isinstance(value, str):
                endpoints[str(container_id)] = _decode_endpoint(str(container_id), value)
        return endpoints

    async def _write_member(self, session_id: str, member: Member) -> None:
        await self._etcd.put(
            member_key(session_id, member.agent_id), json.dumps(member.to_etcd_payload())
        )

    async def _read_members(self, session_id: str) -> dict[str, Member]:
        raw = await self._etcd.get_prefix(members_prefix(session_id))
        members: dict[str, Member] = {}
        for agent_id, value in dict(raw).items():
            if isinstance(value, str):
                members[str(agent_id)] = _decode_member(str(agent_id), value)
        return members

    async def _watch(self, session_id: str) -> None:
        # Watch the whole session subtree so both membership (peers/VTEPs) and endpoint
        # (IP/MAC) changes drive reconciliation.
        #
        # Re-established after any failure. A single `ip`/`bridge` error or a transient etcd hiccup
        # used to end the loop for good, and the node would never learn about another peer for the
        # rest of the session's life — a worker that started late (slow image pull) was silently
        # left out of the mesh and torchrun hung at rendezvous. The stop() path cancels this task,
        # so CancelledError still ends it cleanly. reconcile_* replay from etcd and every device op
        # is idempotent, so re-running after a hiccup re-converges rather than double-programming.
        backoff = _WATCH_RETRY_BACKOFF
        resubscribing = False
        while True:
            try:
                if resubscribing:
                    # watch_prefix streams from the current revision, so a peer that joined or left
                    # while we were not watching shows up in nothing but a fresh read. Catch up
                    # before waiting on the new stream. (This still leaves the window between the
                    # read and the subscribe, which is what _reconcile_periodically covers.)
                    await self.reconcile_peers(session_id)
                    await self.reconcile_endpoints(session_id)
                # Closed explicitly: a reconcile raising out of the loop body would otherwise leave
                # the generator suspended at its yield, holding the etcd watch stream open until the
                # asyncgen finalizer got to it — one leaked stream per retry.
                async with aclosing(self._etcd.watch_prefix(session_prefix(session_id))) as events:
                    async for _ in events:
                        await self.reconcile_peers(session_id)
                        await self.reconcile_endpoints(session_id)
                        backoff = _WATCH_RETRY_BACKOFF  # events are flowing: the watch is healthy
                log.warning(
                    "session network watch for {} ended; re-subscribing in {}s", session_id, backoff
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception(
                    "session network watch for {} failed; retrying in {}s", session_id, backoff
                )
            resubscribing = True
            # Wait before re-subscribing on BOTH paths, not just the error one: a watch_prefix that
            # hands back an already-exhausted stream (a closed/mocked etcd) would otherwise spin
            # this task at full CPU and starve the event loop.
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, _WATCH_RETRY_BACKOFF_MAX)
