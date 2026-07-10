"""Per-session cluster-network coordinator (BEP-1058).

Owns the membership lifecycle for a session network: reads the session meta, drives
the backend's host-level setup, publishes this agent's membership, and reconciles
peers from the etcd ``members/`` prefix (driving the backend's idempotent
``add_peer``/``del_peer``). The v2 backend is a stateless data-plane executor and
never watches etcd itself — that ownership lives here (see Decision Log, BEP-1058).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
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

    async def stop(self, session_id: str) -> None:
        """Stop watching, remove this node's membership, and tear down the data plane."""
        if task := self._watch_tasks.pop(session_id, None):
            # Await the cancellation so a trailing reconcile can't run after teardown and the
            # task's CancelledError is retrieved (no "task exception was never retrieved" warning).
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await self._etcd.delete(member_key(session_id, self._agent_id))
        await self._backend.teardown_session_network(session_id)
        self._applied.pop(session_id, None)
        self._applied_endpoints.pop(session_id, None)

    async def reconcile_peers(self, session_id: str) -> None:
        """Diff the published members against what has been applied and drive the
        backend's add_peer/del_peer accordingly. Idempotent; safe to call repeatedly."""
        members = await self._read_members(session_id)
        applied = self._applied.setdefault(session_id, {})
        current = {aid: m for aid, m in members.items() if aid != self._agent_id}

        for agent_id, member in current.items():
            if agent_id not in applied:
                await self._backend.add_peer(session_id, member)
                applied[agent_id] = member
        for agent_id in list(applied.keys()):
            if agent_id not in current:
                await self._backend.del_peer(session_id, applied.pop(agent_id))

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
            if container_id not in applied:
                await self._backend.add_endpoint(
                    session_id, ip=endpoint.ip, mac=endpoint.mac, vtep_ip=vtep_ip
                )
                applied[container_id] = (endpoint, vtep_ip)
        for container_id in list(applied.keys()):
            if container_id not in current:
                endpoint, vtep_ip = applied.pop(container_id)
                await self._backend.del_endpoint(
                    session_id, ip=endpoint.ip, mac=endpoint.mac, vtep_ip=vtep_ip
                )

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
        try:
            async for _ in self._etcd.watch_prefix(session_prefix(session_id)):
                await self.reconcile_peers(session_id)
                await self.reconcile_endpoints(session_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("session network watch for session {} failed", session_id)
