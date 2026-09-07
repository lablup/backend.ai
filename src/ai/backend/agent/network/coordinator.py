"""Per-session cluster-network coordinator (BEP-1078).

Owns the membership lifecycle for a session network: reads the session meta, drives
the backend's host-level setup, publishes this agent's membership, and reconciles
peers from the etcd ``members/`` prefix (driving the backend's idempotent
``add_peer``/``del_peer``). The v2 backend is a stateless data-plane executor and
never watches etcd itself — that ownership lives here (see Decision Log, BEP-1078).
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Mapping
from contextlib import aclosing
from typing import TYPE_CHECKING, Any

from ai.backend.agent.errors.network import SessionNetworkGone
from ai.backend.common.network.keys import (
    endpoints_prefix,
    member_key,
    members_prefix,
    session_meta_key,
    session_prefix,
)
from ai.backend.common.network.types import (
    DEFAULT_VXLAN_PORT,
    SESSION_META_GENERATION,
    SESSION_META_READY,
    SESSION_META_STATE,
    EndpointAddr,
    Member,
    NetworkBackendKind,
    SessionNetMeta,
    of_generation,
)
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

# How many times a join re-reads a member record that changed under its compare-and-swap before it
# gives up. More than one because this node's own earlier record is replaced here and a co-located
# retry writes the same bytes; bounded because a key that will not settle is a refused join, not a
# loop to spin in.
_MEMBER_PUBLISH_ATTEMPTS = 3


def _decode_member(agent_id: str, raw: str) -> Member:
    return Member.from_etcd_payload(agent_id, json.loads(raw))


def _identity_of(record: Mapping[str, Any]) -> tuple[Any, ...]:
    """What a session network record says it IS -- the incarnation, and what that incarnation
    allocated. Everything a late request could be carrying a stale copy of.

    The encryption key is part of the identity and never part of what is said about it: see
    `_describe`.
    """
    vni = record.get("vni")
    return (
        record.get(SESSION_META_GENERATION),
        record.get("subnet"),
        int(vni) if vni is not None else None,
        int(record.get("vxlan_port") or DEFAULT_VXLAN_PORT),
        record.get("encryption_key"),
    )


def _asked_identity(meta: SessionNetMeta) -> tuple[Any, ...]:
    """The same tuple, as the descriptor this request was issued with names it."""
    return (meta.generation, meta.subnet, meta.vni, meta.vxlan_port, meta.encryption_key)


def _describe(identity: tuple[Any, ...]) -> str:
    """An identity as it may be reported. The cluster overlay key is one of its members and is
    named, never printed -- an exception message crosses into logs and telemetry."""
    generation, subnet, vni, port, key = identity
    return (
        f"generation {generation}, subnet {subnet}, vni {vni}, udp/{port},"
        f" {'encrypted' if key else 'plaintext'}"
    )


def _decode_endpoint(container_id: str, raw: str) -> EndpointAddr:
    return EndpointAddr.from_etcd_payload(container_id, json.loads(raw))


class SessionNetworkCoordinator:
    _etcd: AbstractKVStore
    _backend: AbstractNetworkAgentPluginV2[Any]
    _agent_id: str
    _applied: dict[str, dict[str, Member]]
    _applied_endpoints: dict[str, dict[str, tuple[EndpointAddr, str]]]
    _watch_tasks: dict[str, asyncio.Task[None]]
    # The periodic re-converge task per session (see _reconcile_periodically).
    _sweep_tasks: dict[str, asyncio.Task[None]]
    _reconcile_locks: dict[str, asyncio.Lock]
    # session_id -> {cluster_hostname: ip} for the whole session (every node's endpoints, not the
    # remote-only FDB view). Maintained by the same watch/reconcile that programs the data plane, so
    # the per-session cluster name resolver reads a live map. See cluster-name-resolution.md.
    _names: dict[str, dict[str, str]]
    # session_id -> {cluster_hostname: ip} supplied by the agent, not etcd. Single-node sessions
    # have no central endpoints/ table (the agent lays peers out locally with cluster_host_ips), so
    # their names are registered here instead. Consulted as a fallback after the etcd-backed _names.
    _static_names: dict[str, dict[str, str]]
    # session_id -> the incarnation this node joined, so the withdrawal at teardown can tell its
    # own membership from one a later join published under the same session id (see `stop`).
    _joined: dict[str, str | None]

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
        self._reconcile_locks = {}
        self._names = {}
        self._static_names = {}
        self._joined = {}

    async def start(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Join the session, bring up this node's data plane for it, apply existing peers, and
        begin watching for membership changes.

        The join comes FIRST, before a single device exists. The manager decides whether a
        session's nodes have let go of its VNI by reading the membership table, and it re-reads
        that table after fencing the record (`CNINetworkPlugin.destroy_network`): publishing
        before building is what leaves no order in which this node both escapes that read and goes
        on to build. Building first and publishing after -- which is what this did -- left the
        manager free to see an empty table, hand the VNI to the next session, and only then have
        this node create a tunnel on it."""
        await self._join(meta, self_member)
        await self._backend.setup_session_network(meta, self_member)
        await self._begin(meta.session_id)

    async def resume(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Re-attach to a session whose data plane survived an agent restart.

        Identical to `start` except the backend adopts the running devices instead of rebuilding
        them. The membership republish and the reconciles are what make this necessary rather than
        optional: without them the restarted node stops reacting to peers joining or leaving, and
        cross-node overlay traffic silently stops following the cluster."""
        await self._join(meta, self_member)
        await self._backend.adopt_session_network(meta, self_member)
        await self._begin(meta.session_id)

    async def _join(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Take this node into the session's membership, or refuse the session.

        Read the record BEFORE publishing, and check it again after. A join that was in flight
        while the session was torn down would otherwise stand for a node holding a VNI the manager
        has already given back, and nothing would ever come for it. Publish-then-verify closes
        that -- see `_require_session_current`.

        Raises:
            SessionNetworkGone: the record is not one this node may act on, or it moved on under
                the join.
        """
        fence = await self._session_fence(meta)
        published = Member(
            agent_id=self_member.agent_id,
            host_ip=self_member.host_ip,
            vtep_ip=self_member.vtep_ip,
            joined=self_member.joined,
            # The membership says which incarnation of the session id this node joined, so a
            # cleanup of an earlier one cannot take it back and a later one is not mistaken for it.
            generation=meta.generation,
        )
        await self._publish_member(meta.session_id, published, fence)
        if fence is not None:
            await self._require_session_current(meta.session_id, fence, published)
        self._joined[meta.session_id] = meta.generation

    async def _begin(self, session_id: str) -> None:
        """Apply what is already published, and start watching."""
        self._applied[session_id] = {}
        self._applied_endpoints[session_id] = {}
        self._names[session_id] = {}
        await self._reconcile_all(session_id)
        self._watch_tasks[session_id] = asyncio.create_task(self._watch(session_id))
        self._sweep_tasks[session_id] = asyncio.create_task(
            self._reconcile_periodically(session_id)
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
                await self._reconcile_all(session_id)
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
        # The member record is this node's teardown acknowledgement: the manager reads it to
        # decide whether the session's VNI may be handed to somebody else. Removing it before
        # the data plane is actually gone is what lets a VNI be reused over live devices, so it
        # goes only once teardown has returned without leaving state behind.
        if teardown_data_plane:
            await self._backend.teardown_session_network(session_id)
        await self._withdraw_member(session_id)
        self._applied.pop(session_id, None)
        self._applied_endpoints.pop(session_id, None)
        self._names.pop(session_id, None)
        self._static_names.pop(session_id, None)
        self._reconcile_locks.pop(session_id, None)
        self._joined.pop(session_id, None)

    async def _withdraw_member(self, session_id: str) -> None:
        """Take this node's membership back, now that its data plane is gone.

        Left alone if the record names a DIFFERENT incarnation of the session id: that is a later
        join's acknowledgement, and removing it tells the manager a node that is in the session is
        not -- which is what lets the session's VNI be handed out over live devices.
        """
        key = member_key(session_id, self._agent_id)
        joined = self._joined.pop(session_id, None)
        raw = await self._etcd.get(key)
        if raw is None:
            return
        if joined is not None and not of_generation(raw, joined):
            log.info(
                "leaving this node's membership of session {} in place: it was published for a"
                " later incarnation than the one being torn down",
                session_id,
            )
            return
        # Over the exact bytes just read, not the key. Between the read and an unconditional
        # delete a later join can publish its own membership, and deleting THAT tells the manager
        # a node which is in the session is not -- the same hole the check above exists to close,
        # reopened by the delete that follows it.
        if not await self._etcd.delete_if_value(key, raw):
            log.info(
                "not taking back this node's membership of session {}: it changed while this"
                " teardown was reading it",
                session_id,
            )

    async def _reconcile_all(self, session_id: str) -> None:
        """Converge forwarding in fail-closed order under one per-session lock.

        Endpoint removals close every known unicast path first. Peer removal may then close the
        broadcast path and withdraw XFRM. A second endpoint pass installs additions after their
        peer's XFRM exists.
        """
        async with self._reconcile_locks.setdefault(session_id, asyncio.Lock()):
            blocked_vteps = await self.reconcile_endpoints(session_id)
            await self.reconcile_peers(session_id, blocked_vteps=blocked_vteps)
            await self.reconcile_endpoints(session_id)

    async def reconcile_peers(
        self, session_id: str, *, blocked_vteps: set[str] | None = None
    ) -> None:
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
        blocked_vteps = blocked_vteps or set()
        # Only when this pass has something new to say. Drift -- an `iptables -F`, a firewall
        # reload, an `ip xfrm state flush` -- is the backend's own node-wide watchdog to notice,
        # and it does so from one read for the whole node; calling this unconditionally every
        # fifteen seconds put the per-session reprogramming cost straight back, roughly 21
        # iptables and 13 XFRM commands per session per pass.
        #
        # "Something new" is a changed membership OR nothing applied yet: a backend that restarted
        # under a running session remembers none of what it programmed and would never be told
        # again, because `applied` still holds every peer whose record has not changed.
        if not applied or current != applied:
            # Failing is not fatal to the pass: the backend closes what it cannot protect, and
            # add_peer refuses each peer in turn, which keeps them out of `applied` and retried.
            await self._try(
                session_id,
                "ensure_session_security",
                self._backend.ensure_session_security(session_id, list(current.values())),
            )

        for agent_id, member in current.items():
            if applied.get(agent_id) == member:
                continue
            # A peer whose record CHANGED (the manager pre-seeds a member from the agent's published
            # VTEP key, and the agent itself publishes one when it joins -- they can differ) needs
            # its old FDB entry withdrawn, or this node keeps unicasting to the stale endpoint.
            if (stale := applied.get(agent_id)) is not None:
                if stale.vtep_ip in blocked_vteps:
                    continue
                if not await self._try(
                    session_id, "del_peer", self._backend.del_peer(session_id, stale)
                ):
                    continue
            try:
                await self._backend.add_peer(session_id, member)
            except Exception:
                log.exception("add_peer failed for {} in session {}", agent_id, session_id)
                applied.pop(agent_id, None)  # unapplied: the next reconcile retries this peer
                continue
            applied[agent_id] = member
        for agent_id in list(applied.keys()):
            if agent_id not in current:
                if applied[agent_id].vtep_ip in blocked_vteps:
                    continue
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

    async def reconcile_endpoints(self, session_id: str) -> set[str]:
        """Program FDB + ARP for every remote endpoint in the ``endpoints/`` table
        (proactive; no BUM flood), and remove entries for departed endpoints. Skips this
        node's own endpoints, and skips remotes whose VTEP is not yet published (a later
        watch tick retries). Idempotent; safe to call repeatedly."""
        endpoints = await self._read_endpoints(session_id)
        members = await self._read_members(session_id)
        applied = self._applied_endpoints.setdefault(session_id, {})
        blocked_vteps: set[str] = set()
        # Name map first, from the FULL table (own + remote): a resolver must answer every peer in
        # the session, including a kernel co-located on this node, which the remote-only FDB loop
        # below skips. Rebuilt each pass so a departed/renamed kernel drops out.
        self._names[session_id] = {
            endpoint.cluster_hostname.lower(): endpoint.ip
            for endpoint in endpoints.values()
            if endpoint.cluster_hostname
        }

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
                if not await self._try(
                    session_id,
                    "del_endpoint",
                    self._backend.del_endpoint(
                        session_id, ip=stale[0].ip, mac=stale[0].mac, vtep_ip=stale[1]
                    ),
                ):
                    blocked_vteps.add(stale[1])
                    continue
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
                else:
                    blocked_vteps.add(vtep_ip)
        return blocked_vteps

    def resolve_cluster_name(self, session_id: str, hostname: str) -> str | None:
        """The session-scoped ``hostname -> ip`` lookup the per-session cluster name resolver reads
        (BEP-1078). Case-insensitive, as DNS names are. ``None`` when this session is not set up
        here or the name is not one it owns — the resolver then forwards the query upstream.

        Scoped by ``session_id``: identical cluster hostnames (every session names kernels
        ``main1``/``sub1``/…) never collide because each session's names live under its own key.

        The etcd-backed dynamic map wins; agent-registered static names (single-node sessions, which
        have no ``endpoints/`` table) are the fallback."""
        key = hostname.lower()
        if (ip := (self._names.get(session_id) or {}).get(key)) is not None:
            return ip
        return (self._static_names.get(session_id) or {}).get(key)

    def resolve_cluster_ip(self, session_id: str, ip: str) -> str | None:
        """The reverse of ``resolve_cluster_name``: the cluster hostname assigned to ``ip`` in this
        session, or ``None``. Answers PTR queries. The etcd-backed map wins over static names, as in
        the forward direction. Linear over a session's few peers — no reverse index to keep in sync."""
        for table in (self._names.get(session_id) or {}, self._static_names.get(session_id) or {}):
            for hostname, host_ip in table.items():
                if host_ip == ip:
                    return hostname
        return None

    def register_static_names(self, session_id: str, names: Mapping[str, str]) -> None:
        """Register agent-computed ``hostname -> ip`` names for a session (single-node
        ``cluster_host_ips``), so the resolver can answer them even though nothing is written to
        etcd. Merged (not replaced) and lower-cased for case-insensitive lookup."""
        self._static_names.setdefault(session_id, {}).update({
            hostname.lower(): ip for hostname, ip in names.items()
        })

    async def _read_endpoints(self, session_id: str) -> dict[str, EndpointAddr]:
        """The session's endpoint table, as far as it belongs to the incarnation this node joined.

        A record of another incarnation is data about a session this node is not in. Programmed,
        it points this node's FDB and ARP at an address the live session's kernels do not hold --
        which is silent: the frames leave and nothing answers.
        """
        raw = await self._etcd.get_prefix(endpoints_prefix(session_id))
        endpoints: dict[str, EndpointAddr] = {}
        for container_id, value in dict(raw).items():
            if not isinstance(value, str):
                continue
            if not self._is_ours(session_id, value, f"endpoint {container_id}"):
                continue
            endpoints[str(container_id)] = _decode_endpoint(str(container_id), value)
        return endpoints

    async def _session_fence(self, meta: SessionNetMeta) -> str | None:
        """The manager's record for this session, as the bytes this node is joining.

        None where there is no manager record to be fenced against: a node-local BRIDGE session is
        this agent's own, and its meta is written by us AFTER the data plane is up.

        The record must be READY *and* describe the session this request was issued for. A session
        id is reused, and a launch RPC that was delayed -- a slow link, a retried dispatch --
        arrives naming an incarnation that has since been torn down and rebuilt. READY on its own
        says nothing about which of the two it is: acting on it builds a data plane on the old
        VNI and subnet and publishes this node as an ordinary member of the NEW session, whose
        peers then program a tunnel that carries nothing. So the descriptor is compared against the
        record, generation first and the identity the generation stands for as well, since a
        manager from before the field publishes no generation at all.

        Raises:
            SessionNetworkGone: the record is not one this node may act on.
        """
        if meta.backend is not NetworkBackendKind.VXLAN:
            return None
        raw = await self._etcd.get(session_meta_key(meta.session_id))
        if raw is None or json.loads(raw).get(SESSION_META_STATE) != SESSION_META_READY:
            raise SessionNetworkGone(
                f"session {meta.session_id}'s network record is gone or no longer one this node"
                " may act on; not joining a session the manager has stopped standing behind"
            )
        record = json.loads(raw)
        if (current := _identity_of(record)) != (asked := _asked_identity(meta)):
            raise SessionNetworkGone(
                f"session {meta.session_id}'s network record describes {_describe(current)}, and"
                f" this request was issued for {_describe(asked)}; not joining a session under a"
                " descriptor the manager no longer stands behind"
            )
        return raw

    async def _require_session_current(
        self, session_id: str, fence: str, published: Member
    ) -> None:
        """Refuse the session, and take this node's membership back, if the record has moved on.

        Compared byte for byte against what was read before the publish: a takeover, a tombstone
        and a deletion all change it, and any of the three means the manager is no longer treating
        this node as part of the session. The member record goes first, because while it stands the
        manager holds the session's VNI back from reuse for a node that is not in the session.

        Taken back over the exact bytes this join wrote, and no others. An unconditional delete
        here removes whatever holds the key NOW, which after a rebuild under the same session id is
        the record a LATER join published for the session that replaced this one -- the manager
        would then read an empty table for a node that is in the session and hand its VNI away.

        Raises:
            SessionNetworkGone: the record is no longer the one this node joined.
        """
        if await self._etcd.get(session_meta_key(session_id)) == fence:
            return
        try:
            await self._etcd.delete_if_value(
                member_key(session_id, published.agent_id),
                json.dumps(published.to_etcd_payload()),
            )
        except Exception:
            log.exception(
                "could not take back this node's membership of session {} after its record"
                " changed under the join",
                session_id,
            )
        raise SessionNetworkGone(
            f"session {session_id}'s network record changed while this node was joining it; the"
            " manager owns what happens to the session now"
        )

    async def _publish_member(self, session_id: str, member: Member, fence: str | None) -> None:
        """Put this node into the session's membership, under the manager's record and over
        nothing but this node's own incarnation.

        Two things are wrong with writing the key on its own. An unconditional write let an agent
        instance still running for an earlier incarnation clobber the membership a later one had
        published -- and then, on finding the record moved on, delete exactly those bytes again
        (`_require_session_current`), leaving the live data plane with no membership and the
        manager free to hand its VNI away. And a compare-and-swap on this key alone still CREATES
        it when it is absent: absent is what the manager's cleanup just made it, so the stale join
        puts a member back under a session that no longer exists, where it blocks the teardown of
        whatever replaces it and nothing ever comes for it.

        So the manager's record is named as a guard and the write is one store operation with the
        check: it lands whole under the session this node is actually joining, or not at all.

        Raises:
            SessionNetworkGone: the key belongs to another incarnation, or the record moved on.
        """
        payload = json.dumps(member.to_etcd_payload())
        key = member_key(session_id, member.agent_id)
        guards = {session_meta_key(session_id): fence} if fence is not None else {}
        for _ in range(_MEMBER_PUBLISH_ATTEMPTS):
            standing = await self._etcd.get(key)
            if standing == payload:
                return
            if standing is not None and not of_generation(standing, member.generation):
                raise SessionNetworkGone(
                    f"this node's membership of session {session_id} is published for a later"
                    " incarnation than the one this request was issued for; not joining under a"
                    " descriptor the manager has moved on from"
                )
            if await self._etcd.compare_and_put(key, payload, expected=standing, guards=guards):
                return
        raise SessionNetworkGone(
            f"this node's membership of session {session_id} could not be published under the"
            f" record this join read ({_MEMBER_PUBLISH_ATTEMPTS} attempts); the session has moved"
            " on, or the key kept changing"
        )

    async def _read_members(self, session_id: str) -> dict[str, Member]:
        """The session's membership, as far as it belongs to the incarnation this node joined.

        Same reasoning as `_read_endpoints`: a member of another incarnation is a node that is not
        this session's peer, and programming its VTEP builds a tunnel to somebody else's overlay.
        """
        raw = await self._etcd.get_prefix(members_prefix(session_id))
        members: dict[str, Member] = {}
        for agent_id, value in dict(raw).items():
            if not isinstance(value, str):
                continue
            if not self._is_ours(session_id, value, f"member {agent_id}"):
                continue
            members[str(agent_id)] = _decode_member(str(agent_id), value)
        return members

    def _is_ours(self, session_id: str, payload: str, what: str) -> bool:
        """Whether a record under this session belongs to the incarnation this node joined.

        Everything is ours where this node joined no incarnation at all -- a node-local BRIDGE
        session, or a manager from before the field. There is nothing to tell apart there, and
        filtering on a generation nobody publishes would empty the table.
        """
        joined = self._joined.get(session_id)
        if joined is None or of_generation(payload, joined):
            return True
        log.debug("ignoring {} of session {}: it belongs to another incarnation", what, session_id)
        return False

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
                    await self._reconcile_all(session_id)
                # Closed explicitly: a reconcile raising out of the loop body would otherwise leave
                # the generator suspended at its yield, holding the etcd watch stream open until the
                # asyncgen finalizer got to it — one leaked stream per retry.
                async with aclosing(self._etcd.watch_prefix(session_prefix(session_id))) as events:
                    async for _ in events:
                        await self._reconcile_all(session_id)
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


class SessionClusterNames:
    """A per-session ``ClusterNameSource`` view over a coordinator (BEP-1078).

    The cluster DNS resolver sees only bare hostnames (``sub1``), but names are unique only within
    a session — every session names kernels ``main1``/``sub1``/…. Binding a ``session_id`` here is
    what keeps resolution session-scoped: two sessions' identical names resolve through two of these,
    each pinned to its own session, so they never collide.
    """

    _coordinator: SessionNetworkCoordinator
    _session_id: str

    def __init__(self, coordinator: SessionNetworkCoordinator, session_id: str) -> None:
        self._coordinator = coordinator
        self._session_id = session_id

    def resolve_name(self, hostname: str) -> str | None:
        return self._coordinator.resolve_cluster_name(self._session_id, hostname)

    def resolve_ip(self, ip: str) -> str | None:
        return self._coordinator.resolve_cluster_ip(self._session_id, ip)
