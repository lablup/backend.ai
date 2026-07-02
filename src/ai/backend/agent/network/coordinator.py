"""Per-session cluster-network coordinator (BEP-1055).

Owns the membership lifecycle for a session network: reads the session meta, drives
the backend's host-level setup, publishes this agent's membership, and reconciles
peers from the etcd ``members/`` prefix (driving the backend's idempotent
``add_peer``/``del_peer``). The v2 backend is a stateless data-plane executor and
never watches etcd itself — that ownership lives here (see Decision Log, BEP-1055).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from ai.backend.common.network.types import Member, SessionNetMeta
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
    from ai.backend.common.etcd import AbstractKVStore

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def members_prefix(session_id: str) -> str:
    return f"network/session/{session_id}/members/"


def member_key(session_id: str, agent_id: str) -> str:
    return f"{members_prefix(session_id)}{agent_id}"


def _decode_member(agent_id: str, raw: str) -> Member:
    data = json.loads(raw)
    return Member(
        agent_id=agent_id,
        host_ip=data["host_ip"],
        vtep_ip=data.get("vtep_ip"),
        ip_range=data.get("ip_range"),
    )


class SessionNetworkCoordinator:
    _etcd: AbstractKVStore
    _backend: AbstractNetworkAgentPluginV2[Any]
    _agent_id: str
    _applied: dict[str, dict[str, Member]]
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
        self._watch_tasks = {}

    async def start(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Bring up this node's data plane for the session, publish membership, apply
        existing peers, and begin watching for membership changes."""
        await self._backend.setup_session_network(meta, self_member)
        await self._write_member(meta.session_id, self_member)
        self._applied[meta.session_id] = {}
        await self.reconcile_peers(meta.session_id)
        self._watch_tasks[meta.session_id] = asyncio.create_task(
            self._watch(meta.session_id)
        )

    async def stop(self, session_id: str) -> None:
        """Stop watching, remove this node's membership, and tear down the data plane."""
        if task := self._watch_tasks.pop(session_id, None):
            task.cancel()
        await self._etcd.delete(member_key(session_id, self._agent_id))
        await self._backend.teardown_session_network(session_id)
        self._applied.pop(session_id, None)

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

    async def _write_member(self, session_id: str, member: Member) -> None:
        payload = {
            "host_ip": member.host_ip,
            "vtep_ip": member.vtep_ip,
            "ip_range": member.ip_range,
        }
        await self._etcd.put(member_key(session_id, member.agent_id), json.dumps(payload))

    async def _read_members(self, session_id: str) -> dict[str, Member]:
        raw = await self._etcd.get_prefix(members_prefix(session_id))
        members: dict[str, Member] = {}
        for agent_id, value in dict(raw).items():
            if isinstance(value, str):
                members[str(agent_id)] = _decode_member(str(agent_id), value)
        return members

    async def _watch(self, session_id: str) -> None:
        try:
            async for _ in self._etcd.watch_prefix(members_prefix(session_id)):
                await self.reconcile_peers(session_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("membership watch for session {} failed", session_id)
