"""Runtime-neutral cluster-network manager plugin (CNI/etcd control plane).

Replaces the Swarm-based `OverlayNetworkPlugin` for containerd and other host-native
runtimes. This plugin owns the *control plane*: it allocates a per-session subnet
(and a VNI for the vxlan backend), selects the data-plane backend (the portable vxlan
overlay unless the operator pins one), and writes the session network descriptor to etcd.
The data plane itself is realized by the agent-side v2 plugins (see BEP-1078, agent plugin).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections.abc import Mapping
from typing import Any, Final, override

from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.network.keys import (
    agent_vtep_key,
    endpoints_prefix,
    member_key,
    members_prefix,
    session_ipam_prefix,
    session_meta_key,
)
from ai.backend.common.network.types import (
    DEFAULT_VXLAN_PORT,
    ESP_OVERHEAD,
    SESSION_META_READY,
    SESSION_META_STATE,
    VXLAN_OVERHEAD,
    Member,
    NetworkBackendKind,
    OverlayEncryptionPolicy,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.network import (
    ForcedBackendUnsupported,
    NetworkBackendMismatch,
    OverlayTeardownPending,
    SessionCleanupPending,
    SessionRecordContested,
)
from ai.backend.manager.network.ipam import (
    DEFAULT_BLOCK_PREFIXLEN,
    DEFAULT_IPAM_POOL,
    EndpointAllocator,
    SubnetAllocator,
    VNIAllocator,
    overlay_encryption_key,
)
from ai.backend.manager.network.pairing import (
    members_can_encrypt,
    require_members_can_serve_driver,
    require_members_overlay_ready,
)
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin, NetworkInfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# The underlay (uplink) MTU. The overlay MTU handed to every kernel is this minus the VXLAN
# encapsulation overhead, so a full-size inner frame still fits the tunnel — the same 1450 default
# Docker Swarm's overlay uses. Setting the container NIC to the underlay 1500 (as this used to) lets
# a 1500-byte frame reach a 1450-MTU VXLAN port, where it is silently dropped with no ICMP (L2
# bridging), i.e. a PMTUD black hole: handshakes pass, bulk transfers (NCCL/mpirun) hang.
_DEFAULT_UNDERLAY_MTU = 1500
# The encapsulation overheads live in common/network/types.py: the agent subtracts the same two
# numbers from the underlay it *measures*, and refuses the session if this computation came out
# larger than the path can carry, so both sides must read one definition.
_VXLAN_OVERHEAD = VXLAN_OVERHEAD
_ESP_OVERHEAD = ESP_OVERHEAD


#: Bookkeeping the session meta carries for the create itself, stripped from what callers see.
_OWNER: Final = "_owner"
#: When the record was claimed, as wall-clock seconds -- the one clock two managers share. Read
#: only to tell a create that is still running from one nobody is coming back for, at the same
#: coarse bound `_claim_session` hands the session over at, so clock skew of a few seconds is
#: not a factor.
_CLAIMED_AT: Final = "_claimed_at"
#: Both halves of the contract an agent reads too -- see `SESSION_META_STATE`.
_STATE: Final = SESSION_META_STATE
_READY: Final = SESSION_META_READY
_CREATING: Final = "creating"
#: A create that is undoing itself. The record stays under this state until its keys are deleted
#: and its subnet and VNI are back in the pool, because it is the only thing that names them.
_DELETING: Final = "deleting"
#: Which cleanup is working from this tombstone. Fresh on every take, so two managers that read
#: the same DELETING record do not both run the cleanup from it -- see `_tombstone`.
_CLEANER: Final = "_cleaner"

#: How long a second manager waits for the one that claimed a session to finish before taking it
#: over. Long enough to cover a slow create, short enough that a manager killed mid-create does
#: not hold the session up until somebody notices.
_CREATE_HANDOVER_SEC: Final = 60.0
_CREATE_POLL_SEC: Final = 0.5


def _published(meta: Mapping[str, Any]) -> dict[str, Any]:
    """The session meta as its callers see it, without the create's own bookkeeping."""
    return {key: value for key, value in meta.items() if key not in (_OWNER, _STATE, _CLAIMED_AT)}


def _tombstone(subnet: str | None, vni: Any, owner: str | None) -> str:
    """A DELETING record naming what is still allocated, and which cleanup is clearing it.

    ``_cleaner`` is a fresh value on every take. Without it two managers that read the same
    DELETING record both run the cleanup from those same bytes, and the slower one carries on
    deleting after the faster one finished and a new session was built under the same id -- taking
    the new session's endpoint and member keys and giving its subnet and VNI back to the pool. With
    it, only one of the two can hold the record, and the other finds out at its next check.
    """
    return json.dumps({
        "subnet": subnet,
        "vni": vni,
        _OWNER: owner,
        _STATE: _DELETING,
        _CLEANER: uuid.uuid4().hex,
    })


class CNINetworkPlugin(AbstractNetworkManagerPlugin):
    """Control-plane plugin for the runtime-neutral cluster network (BEP-1078)."""

    _etcd: AsyncEtcd | None
    _subnet_allocator: SubnetAllocator
    _vni_allocator: VNIAllocator
    _endpoint_allocator: EndpointAllocator
    _forced_backend: NetworkBackendKind | None

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._etcd = None
        self._forced_backend = None

    @override
    async def init(self, context: Any = None) -> None:
        # Build a dedicated AsyncEtcd from the manager's etcd config (same pattern as
        # OverlayNetworkPlugin constructing its own Docker client). local_config is the
        # by-alias dump of ManagerUnifiedConfig, whose `etcd` section round-trips through
        # EtcdConfig. The operator's forced_backend is passed per-call via create_network
        # options by the launcher (which holds the typed config), so it is not parsed here.
        etcd_config = EtcdConfig.model_validate(self.local_config["etcd"]).to_dataclass()
        self._etcd = AsyncEtcd.create_from_config(etcd_config)
        await self._etcd.open()
        # The overlay pool is the operator's: it is stretched across the session's nodes, so it
        # must not collide with anything those nodes already route.
        inter_container = (self.local_config.get("network") or {}).get("inter-container") or {}
        self._subnet_allocator = SubnetAllocator(
            self._etcd,
            pool=str(inter_container.get("ipam-pool") or DEFAULT_IPAM_POOL),
            block_prefixlen=int(inter_container.get("ipam-block-size") or DEFAULT_BLOCK_PREFIXLEN),
        )
        self._vni_allocator = VNIAllocator(self._etcd)
        self._endpoint_allocator = EndpointAllocator(self._etcd)

    @override
    async def cleanup(self) -> None:
        if self._etcd is not None:
            await self._etcd.close()
            self._etcd = None

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        return await super().update_plugin_config(plugin_config)

    def _require_etcd(self) -> AsyncEtcd:
        if self._etcd is None:
            raise RuntimeError("CNINetworkPlugin is not initialized (call init() first)")
        return self._etcd

    @override
    async def create_network(
        self, *, identifier: str | None = None, options: dict[str, Any] | None = None
    ) -> NetworkInfo:
        etcd = self._require_etcd()
        session_id = identifier or str(uuid.uuid4())
        options = options or {}
        member_agents = list(options.get("member_agents", []))
        forced_raw = options.get("forced_backend")
        forced_backend = NetworkBackendKind(forced_raw) if forced_raw else None
        # Each endpoint = one container: {"container_id", "agent_id"}. The manager assigns
        # its overlay IP centrally (BEP-1078) so per-node IPs are disjoint.
        endpoints = list(options.get("endpoints", []))
        # Optional explicit subnet (like `docker network create --subnet`): when set, the
        # allocator claims exactly this block and fails on overlap instead of auto-sizing.
        requested_subnet = options.get("subnet")

        token = uuid.uuid4().hex
        await self._require_members_cni_capable(member_agents)
        # A session start that failed downstream is retried with the same id, so this can be a
        # second call for a session that already has an allocation. Allocating again would give
        # it a second subnet and VNI and leave the first ones claimed by nobody: destroy_network
        # releases only what the meta records. Converge on what is already there instead.
        if (existing := await self._existing_allocation(etcd, session_id, endpoints)) is not None:
            return existing
        # Claim the session before claiming anything for it. Two managers can be here at once,
        # and only one of them may hold the subnet and the VNI: the other converges on the same
        # ones, so if both were allowed to allocate, the one that failed would give back what the
        # one that succeeded is already handing to its agents. Winning this is what makes "undo
        # what I did" meaningful.
        held, published = await self._claim_session(etcd, session_id, token, endpoints)
        if published is not None:
            return published
        subnet: str | None = None
        vni: int | None = None
        try:
            backend = self._select_backend(forced_backend)
            # Size the session subnet to hold every endpoint (removes the fixed-/24 254 cap).
            subnet = await self._subnet_allocator.acquire(
                session_id,
                host_count=max(len(endpoints), 1),
                subnet=str(requested_subnet) if requested_subnet else None,
            )
            # Encrypt the overlay for the encapsulating (VXLAN) backend unless something opted
            # OUT -- see `_encryption_enabled`. The key is the CLUSTER's, not this session's: ESP
            # policies select on the outer packet, where nothing identifies a session, so sessions
            # between the same pair of nodes share one policy and a per-session key was a promise
            # the data plane could not keep (see overlay_encryption_key). It still travels in the
            # session meta, exactly like the VNI, so the agents need no second source.
            policy = self._encryption_policy(options)
            encrypt = (
                backend is NetworkBackendKind.VXLAN
                and policy is not OverlayEncryptionPolicy.DISABLED
            )
            if encrypt:
                encrypt = await self._nodes_can_encrypt(etcd, member_agents, policy=policy)
            encryption_key = await overlay_encryption_key(etcd) if encrypt else None
            if backend is NetworkBackendKind.VXLAN:
                vni = await self._vni_allocator.acquire(session_id)
            # `mtu` in plugin_config is the UNDERLAY MTU; the overlay MTU (what the kernel's NIC
            # gets) is that minus the tunnel overhead. Only the VXLAN backend encapsulates, so only
            # it pays the overhead; a non-encapsulating backend would keep the underlay MTU. When
            # encryption is on, the ESP overhead comes off the overlay MTU as well.
            underlay_mtu = int(self.plugin_config.get("mtu") or _DEFAULT_UNDERLAY_MTU)
            if backend is NetworkBackendKind.VXLAN:
                mtu = underlay_mtu - _VXLAN_OVERHEAD - (_ESP_OVERHEAD if encrypt else 0)
            else:
                mtu = underlay_mtu
            # `mtu` above is an ASSUMPTION about the underlay, not a measurement, and it is one
            # value for a possibly heterogeneous cluster. Each agent re-derives its own node's
            # real underlay and refuses the session when this number does not fit, which turns a
            # silent black hole into a named error. See agent/network/path_mtu.py.
            vxlan_port = int(self.plugin_config.get("vxlan-port") or DEFAULT_VXLAN_PORT)

            meta: dict[str, Any] = {
                "subnet": subnet,
                "vni": vni,
                "backend": str(backend),
                "mtu": mtu,
                "vxlan_port": vxlan_port,
                "encryption_key": encryption_key,
                # Who is building this session, and whether they finished. Two managers can be
                # here at once for one session; the allocation they converge on is shared, so
                # "undo what I did" is only meaningful against a record that says whose it is.
                _OWNER: token,
                _STATE: _CREATING,
                _CLAIMED_AT: time.time(),
            }
            held = await self._publish(etcd, session_id, held, meta)
            # Assign each endpoint a disjoint overlay IP and record it under endpoints/ (the
            # coordinator programs FDB/ARP from there). Returned map is threaded per-kernel by
            # the launcher into KernelCreationConfig["cluster_network_ip"].
            #
            # Written after the compare-and-swap above and outside it, which is safe only because
            # two creates of one session converge: the pool hands `acquire` the block this session
            # already holds, and `assign` returns the address a container already has. So a create
            # that has been superseded writes the values the one that superseded it writes.
            endpoint_ips: dict[str, str] = {}
            for endpoint in endpoints:
                container_id = str(endpoint["container_id"])
                hostname = endpoint.get("cluster_hostname")
                ip, _mac = await self._endpoint_allocator.assign(
                    session_id,
                    container_id,
                    subnet,
                    agent_id=str(endpoint["agent_id"]),
                    cluster_hostname=str(hostname) if hostname is not None else None,
                )
                endpoint_ips[container_id] = ip
            # Pre-seed the membership table so each agent's reconcile-at-start finds every
            # peer's VTEP already present, instead of racing the etcd watch that delivers a
            # peer's self-published member (which can lag a fast worker's cross-node startup).
            # VXLAN only: the member's tunnel endpoint is the agent's published VTEP. Agents
            # whose VTEP is not yet published are skipped — they fall back to self-publish +
            # watch convergence (no regression).
            if backend is NetworkBackendKind.VXLAN:
                await self._preseed_members(session_id, member_agents)
            # Ready only now: everything the session needs is on record. A waiter returns at
            # this point, and not before -- a create that fails after publishing undoes itself,
            # and anyone who had already been handed the half-built record would be holding a
            # subnet and a VNI the pool has since given to somebody else.
            meta[_STATE] = _READY
            held = await self._publish(etcd, session_id, held, meta)
            return NetworkInfo(
                network_id=session_id, options={**_published(meta), "endpoint_ips": endpoint_ips}
            )
        except BaseException:
            # BaseException, not Exception: a cancelled create -- the launcher's timeout, a
            # manager shutdown -- otherwise walks away holding the subnet and the VNI. Shielded
            # so the rollback's own awaits are not cancelled in turn and leave it half done.
            await asyncio.shield(
                asyncio.ensure_future(self._rollback_create(session_id, subnet, vni, held))
            )
            raise

    async def _existing_allocation(
        self, etcd: AsyncEtcd, session_id: str, endpoints: list[Any]
    ) -> NetworkInfo | None:
        """This session's allocation as it already stands, or None if it has none yet.

        Endpoints missing from the table are assigned now: a create that was interrupted partway
        through them still owes the caller an address for every kernel.
        """
        raw = await etcd.get(session_meta_key(session_id), scope=ConfigScopes.GLOBAL)
        if raw is None:
            return None
        meta = json.loads(raw)
        if meta.get(_STATE) not in (None, _READY):
            # Still being built, by us on a previous attempt or by another manager. Not something
            # to hand back: the subnet and VNI it names are not committed until whoever owns it
            # says so, and a create that fails after this point takes them away again.
            return None
        subnet = str(meta["subnet"])
        # A meta is only worth reusing while the pool still agrees it is ours. A rollback that
        # freed the allocation but could not delete the record leaves one that names a block and
        # a VNI the next session may already hold; returning it would hand this session their
        # data plane. Treat that as no allocation at all and build a fresh one.
        if not await self._still_ours(session_id, subnet, meta.get("vni")):
            log.warning(
                "session {}'s recorded overlay allocation (subnet {}, vni {}) is no longer held"
                " by it; allocating again",
                session_id,
                subnet,
                meta.get("vni"),
            )
            return None
        endpoint_ips: dict[str, str] = {}
        for endpoint in endpoints:
            container_id = str(endpoint["container_id"])
            hostname = endpoint.get("cluster_hostname")
            ip, _mac = await self._endpoint_allocator.assign(
                session_id,
                container_id,
                subnet,
                agent_id=str(endpoint["agent_id"]),
                cluster_hostname=str(hostname) if hostname is not None else None,
            )
            endpoint_ips[container_id] = ip
        log.info(
            "reusing the existing overlay allocation for session {} (subnet {}, vni {})",
            session_id,
            subnet,
            meta.get("vni"),
        )
        return NetworkInfo(
            network_id=session_id, options={**_published(meta), "endpoint_ips": endpoint_ips}
        )

    async def _claim_session(
        self, etcd: AsyncEtcd, session_id: str, token: str, endpoints: list[Any]
    ) -> tuple[str, NetworkInfo | None]:
        """Own the session's record, or hand back what a finished create published.

        Returns ``(the record this call now holds, what somebody else built)``; exactly one of
        the two is meaningful. Ownership is the record's exact bytes, not the token inside them:
        every later write is a compare-and-swap against those bytes, so a call that has been
        superseded finds out when it tries to write rather than overwriting whoever succeeded it.

        Raises:
            SessionRecordContested: nobody could be established as the owner within the bound --
                a stream of managers taking the session from each other. Retryable, and reported
                rather than looped on forever.
        """
        ours = json.dumps({_OWNER: token, _STATE: _CREATING, _CLAIMED_AT: time.time()})
        key = session_meta_key(session_id)
        handover = time.monotonic() + _CREATE_HANDOVER_SEC
        give_up = handover + _CREATE_HANDOVER_SEC
        # Every way round this loop ends in a return, a raise, or the poll below. A `continue`
        # that skipped it spun on the CPU without ever yielding to the event loop -- and the
        # record it was waiting on (a READY one whose allocation is gone) is one nothing else was
        # ever going to change, so the manager hung there rather than polling.
        while True:
            if await etcd.put_if_absent(key, ours):
                return ours, None
            raw = await etcd.get(key, scope=ConfigScopes.GLOBAL)
            if raw is not None:
                state = json.loads(raw).get(_STATE)
                if state == _DELETING:
                    # A cleanup that did not get to the end. Never taken over as a create: the
                    # tombstone names a subnet and a VNI that are still allocated, and building
                    # over it would run a session on keys somebody else is still deleting. Finish
                    # it instead -- and take it first, into bytes only this call holds, so two
                    # managers that read this same record do not both delete from it. Losing that
                    # take is not an error: fall through to the poll and come back to whatever is
                    # there now.
                    record = json.loads(raw)
                    mine = _tombstone(record.get("subnet"), record.get("vni"), record.get(_OWNER))
                    if await etcd.replace(key, raw, mine):
                        if not await self._finish_cleanup(etcd, session_id, mine):
                            raise SessionCleanupPending(
                                f"session {session_id}'s previous network could not be cleaned"
                                " up; retrying rather than building over what it still holds"
                            )
                        if await etcd.put_if_absent(key, ours):
                            return ours, None
                if state == _READY:
                    published = await self._existing_allocation(etcd, session_id, endpoints)
                    if published is not None:
                        return "", published
                    # Finished, and worth nothing: the pool no longer records the subnet and the
                    # VNI it names as this session's, so there is no owner to wait for. Take it
                    # from those exact bytes and build the session again.
                    if await etcd.replace(key, raw, ours):
                        log.warning(
                            "session {}'s network record outlived its allocation; building it"
                            " again",
                            session_id,
                        )
                        return ours, None
                elif time.monotonic() >= handover:
                    # Take it over, from the exact record just read and no other. An unconditional
                    # write here would let two waiters that timed out together each believe they
                    # own the session, and would let a create that was only slow carry on writing
                    # over whoever replaced it.
                    if await etcd.replace(key, raw, ours):
                        log.warning(
                            "taking over session {}'s network: the manager that claimed it did"
                            " not finish within {}s",
                            session_id,
                            _CREATE_HANDOVER_SEC,
                        )
                        return ours, None
            if time.monotonic() >= give_up:
                raise SessionRecordContested(
                    f"could not establish an owner for session {session_id}'s network within"
                    f" {_CREATE_HANDOVER_SEC * 2}s; another manager keeps taking it"
                )
            await asyncio.sleep(_CREATE_POLL_SEC)

    async def _publish(
        self, etcd: AsyncEtcd, session_id: str, held: str, meta: Mapping[str, Any]
    ) -> str:
        """Write the session's record, but only over the one this call still holds.

        Returns the bytes now held. Everything this create does afterwards is conditional on
        them, which is what stops a superseded create from resurrecting a session that was taken
        over, rolled back, or destroyed underneath it.

        Raises:
            SessionRecordContested: the record is no longer this call's.
        """
        raw = json.dumps(dict(meta))
        if not await etcd.replace(session_meta_key(session_id), held, raw):
            raise SessionRecordContested(
                f"session {session_id}'s network record was taken by another manager while this"
                " create was running; it owns what happens to the session now"
            )
        return raw

    async def _await_ready(
        self, etcd: AsyncEtcd, session_id: str, endpoints: list[Any]
    ) -> NetworkInfo | None:
        """What the manager that claimed this session built, once it says it is finished.

        None when it has not finished within `_CREATE_HANDOVER_SEC` -- it died, or it is so slow
        that waiting longer is worse than taking over.
        """
        deadline = time.monotonic() + _CREATE_HANDOVER_SEC
        while True:
            raw = await etcd.get(session_meta_key(session_id), scope=ConfigScopes.GLOBAL)
            if raw is None:
                return None  # they rolled back; nothing to wait for
            meta = json.loads(raw)
            if meta.get(_STATE) == _READY:
                return await self._existing_allocation(etcd, session_id, endpoints)
            if time.monotonic() >= deadline:
                return None
            await asyncio.sleep(_CREATE_POLL_SEC)

    async def _still_ours(self, session_id: str, subnet: str, vni: Any) -> bool:
        """Whether the pool still records this session as the holder of both."""
        if await self._subnet_allocator.holder(subnet) != session_id:
            return False
        if vni is None:
            return True
        return await self._vni_allocator.holder(int(vni)) == session_id

    async def _rollback_create(
        self, session_id: str, subnet: str | None, vni: int | None, held: str
    ) -> None:
        """Undo a partially-created session network, in the one order that survives failing.

        The record is turned into a tombstone naming the subnet and the VNI, and deleted last --
        see the comments below. Only when it is still this call's.
        """
        etcd = self._require_etcd()
        # Take the record over into a tombstone instead of deleting it, and do it in one step:
        # a separate read-then-delete let the record be taken between the two, and everything
        # below would then have undone the new owner's work.
        #
        # A tombstone, because the record is the only thing that names this session's subnet and
        # VNI. Deleting it first and then failing to finish left them allocated to a session no
        # key mentions: `destroy_network` reads the meta to know what to give back, so there was
        # nothing left to give it back from, and the block and the VNI leaked for the cluster's
        # lifetime. It also let a new creator in while the old rollback was still deleting, whose
        # keys the old rollback then removed.
        try:
            owner = json.loads(held).get(_OWNER) if held else None
        except ValueError:
            owner = None
        tombstone = _tombstone(subnet, vni, owner)
        if not held or not await etcd.replace(session_meta_key(session_id), held, tombstone):
            log.info(
                "not rolling back session {}: its record is no longer this create's", session_id
            )
            return
        await self._finish_cleanup(etcd, session_id, tombstone)

    async def _finish_cleanup(self, etcd: AsyncEtcd, session_id: str, tombstone: str) -> bool:
        """Carry a session under a DELETING tombstone through to nothing left, and say whether it
        got there.

        Every destructive step is fenced on the record still being these exact tombstone bytes,
        because this call can be resumed late -- a slow etcd, a manager that swapped out -- and by
        then another cleanup may have finished the job and a new session may have been built under
        the same id. Its endpoints, its members and its pool claim are indistinguishable from the
        ones this call came to delete: the claim names the session, not the attempt that made it
        (`ipam._claim`). The tombstone is the only thing that tells them apart, so nothing is
        deleted without checking it first, and losing it ends this cleanup rather than continuing
        into somebody else's session.

        Returns False when the record is no longer this call's; the caller retries and re-reads.
        """

        async def still_ours() -> bool:
            held = await etcd.get(session_meta_key(session_id), scope=ConfigScopes.GLOBAL)
            if held == tombstone:
                return True
            log.info(
                "stopping the cleanup of session {}: its record is no longer the tombstone this"
                " call was working from",
                session_id,
            )
            return False

        # Everything under the session except the tombstone. Nobody acts on a session whose
        # record is not READY, and what is left is named by the tombstone until the last line.
        for prefix in (endpoints_prefix, members_prefix, session_ipam_prefix):
            if not await still_ours():
                return False
            try:
                await etcd.delete_prefix(prefix(session_id).rstrip("/"), scope=ConfigScopes.GLOBAL)
            except Exception:
                log.exception(
                    "cleanup of session {} could not delete its {} keys; its record stays as a"
                    " tombstone so this can be finished later",
                    session_id,
                    prefix(session_id),
                )
                return False
        # Everything the POOL says is this session's, not only what the tombstone names. A create
        # cancelled between claiming a block and publishing the record that would have named it
        # leaves one no meta mentions, and this is the only thing that reaches it. Which is also
        # why it is the step that most needs the fence above: it reaches a NEW create's claim just
        # as readily.
        if not await still_ours():
            return False
        try:
            stuck_vnis = await self._vni_allocator.release_all(session_id)
            stuck_blocks = await self._subnet_allocator.release_all(session_id)
        except Exception:
            log.exception("cleanup of session {} could not reach the pool", session_id)
            return False
        if stuck_vnis or stuck_blocks:
            return False
        # Last, and only over the tombstone this call is working from.
        await etcd.delete_if_value(session_meta_key(session_id), tombstone)
        return True

    async def _preseed_members(self, session_id: str, member_agents: list[str]) -> None:
        """Publish each member agent's VTEP, but only where no record stands already.

        Never over one: the agent's own record carries ``joined=true``, the teardown
        acknowledgement `destroy_network` reads before it hands the VNI back to the pool.
        """
        etcd = self._require_etcd()
        for agent_id in member_agents:
            vtep = await etcd.get(agent_vtep_key(agent_id), scope=ConfigScopes.GLOBAL)
            if not vtep:
                continue
            member = Member(agent_id=agent_id, host_ip=vtep, vtep_ip=vtep)
            await etcd.put_if_absent(
                member_key(session_id, agent_id),
                json.dumps(member.to_etcd_payload()),
                scope=ConfigScopes.GLOBAL,
            )

    @override
    async def destroy_network(self, network_id: str) -> None:
        """Release the session's VNI and subnet, but only once its nodes have let go of them.

        A node removes its member record when its teardown has actually completed, so a record
        that is still there means that node may still hold this VNI's devices, XFRM state and
        firewall rules. Handing the VNI out then gives the next session a stranger's rules and
        lets the laggard's retry tear down the new session's data plane. So the allocation is
        kept -- it stays this session's, which is what stops the reuse -- and the session keys
        are left with it so a later destroy can finish the job.
        """
        etcd = self._require_etcd()
        pending = await self._members_still_holding(network_id)
        if pending:
            # Raise, do not return. The caller (`TerminatedTransitionHook`) retries on failure and
            # on nothing else, so returning quietly would leave the VNI, the subnet and the
            # session's keys allocated for good the moment one node was a beat slower than the
            # manager. This keeps the session in TERMINATING and the self-healing loop comes back.
            raise OverlayTeardownPending(
                f"session {network_id}'s overlay allocation is still held by"
                f" {len(pending)} node(s) ({', '.join(sorted(pending))}) that have not confirmed"
                " teardown; retrying rather than reusing the VNI over their live state"
            )
        raw = await etcd.get(session_meta_key(network_id), scope=ConfigScopes.GLOBAL)
        if raw is None:
            # No record -- but reading that is not the same as holding it. A create can claim this
            # id (`_claim_session`'s put_if_absent) between the read above and any delete below,
            # and the sweep would then take the keys it is publishing and give back the subnet and
            # VNI it is already handing to its agents; its own rollback, finding no record of its,
            # would not take them back either. So put a tombstone in through the same
            # compare-and-swap the create races for: whoever wins it goes first.
            tombstone = _tombstone(None, None, None)
            if not await etcd.put_if_absent(session_meta_key(network_id), tombstone):
                raise OverlayTeardownPending(
                    f"session {network_id}'s network record appeared while this teardown was"
                    " reading it; retrying against what is there now"
                )
            if not await self._finish_cleanup(etcd, network_id, tombstone):
                raise OverlayTeardownPending(
                    f"session {network_id}'s network could not be given back in full; its record"
                    " stays as a tombstone naming what is left, and this retries"
                )
            return
        meta = json.loads(raw)
        if meta.get(_STATE) == _CREATING and not self._create_gave_up(meta):
            # A create is building this session right now. Deleting its keys from under it takes
            # away the record its own rollback needs, and what it had already claimed from the
            # pool is then held by a session nothing mentions. Wait for it: it either publishes
            # READY or undoes itself, and the teardown retry comes back to whichever happened.
            raise OverlayTeardownPending(
                f"session {network_id}'s network is still being created; retrying rather than"
                " deleting the record its create would undo itself from"
            )
        # From READY (or from a create nobody is coming back for) into a tombstone, in one step.
        # A create still running finds out at its next write, and an agent that reads the record
        # to resume this session sees one it must not act on.
        tombstone = _tombstone(meta.get("subnet"), meta.get("vni"), meta.get(_OWNER))
        if not await etcd.replace(session_meta_key(network_id), raw, tombstone):
            raise OverlayTeardownPending(
                f"session {network_id}'s network record changed while this teardown was reading"
                " it; retrying against what is there now"
            )
        if not await self._finish_cleanup(etcd, network_id, tombstone):
            raise OverlayTeardownPending(
                f"session {network_id}'s network could not be given back in full; its record"
                " stays as a tombstone naming what is left, and this retries"
            )

    @staticmethod
    def _create_gave_up(meta: Mapping[str, Any]) -> bool:
        """Whether a CREATING record is old enough that no create is coming back for it.

        The same bound `_claim_session` hands the session over at: past it, the manager that
        claimed the record is treated as gone by every other manager, so a teardown may take it
        too rather than keeping the session in TERMINATING for good.
        """
        claimed_at = meta.get(_CLAIMED_AT)
        if not isinstance(claimed_at, (int, float)):
            return True  # a record from before this field existed; do not wait on it forever
        return (time.time() - float(claimed_at)) >= _CREATE_HANDOVER_SEC * 2

    async def _members_still_holding(self, session_id: str) -> set[str]:
        """The agents whose member record is still published for this session.

        The record IS the teardown acknowledgement: an agent writes it when it joins and removes
        it only after `teardown_session_network` returned without leaving state behind.
        """
        found = await self._require_etcd().get_prefix(
            members_prefix(session_id).rstrip("/"), scope=ConfigScopes.GLOBAL
        )
        holding: set[str] = set()
        for agent_id, payload in found.items():
            if not agent_id:
                continue
            if not isinstance(payload, str):
                continue  # a member key holds one JSON value and has no children
            # Only a record the AGENT wrote is an acknowledgement. The pre-seed this same plugin
            # writes at create time says which nodes are *expected* to take part, before any of
            # them has touched the host -- counting it would hold every session's VNI forever on
            # a node that never received a kernel.
            try:
                member = Member.from_etcd_payload(str(agent_id), json.loads(payload))
            except (ValueError, KeyError):
                # Unreadable is not "gone": something wrote it, so assume it is still holding.
                holding.add(str(agent_id))
                continue
            if member.joined:
                holding.add(str(agent_id))
        return holding

    async def _require_members_cni_capable(self, member_agents: list[str]) -> None:
        """Refuse a member agent whose backend cannot serve the 'cni' driver.

        The symmetric check for 'overlay' lives in OverlayNetworkPlugin; both call the same guard
        so the two drivers cannot drift apart on what they accept.
        """
        etcd = self._require_etcd()
        await require_members_can_serve_driver(etcd, "cni", member_agents)
        await require_members_overlay_ready(etcd, member_agents)

    def _select_backend(self, forced_backend: NetworkBackendKind | None) -> NetworkBackendKind:
        """The operator's forced backend wins; otherwise every multi-node cluster session uses
        the portable vxlan overlay.

        This control plane only ever provisions multi-node sessions — single-node sessions never
        reach it (the agent selects their node-local bridge backend directly). The bridge backend
        is node-local and ignores the manager's central IPAM, so pinning it here would provision a
        session whose /etc/hosts names overlay IPs no container holds. Reject it rather than hand
        back unusable networking; 'vxlan' (or an unset override) is the only valid choice here.
        """
        if forced_backend is NetworkBackendKind.BRIDGE:
            raise ForcedBackendUnsupported(
                "the 'bridge' data-plane backend is node-local (single-node) and cannot serve a"
                " multi-node cluster session; use 'vxlan' (the default) or leave forced-backend unset."
            )
        return forced_backend if forced_backend is not None else NetworkBackendKind.VXLAN

    def _encryption_policy(self, options: dict[str, Any]) -> OverlayEncryptionPolicy:
        """What this session's overlay must be, and what to do when a node cannot manage it.

        REQUIRED by default. A multi-node session's traffic crosses the operator's underlay as
        plain VXLAN otherwise -- readable, and injectable, by anything on the path between two
        nodes -- and a default that has to be found in the documentation is a default that is not
        set.

        Three values rather than a boolean, because "encrypt this" and "encrypt this if you can"
        are different instructions and a boolean cannot hold both. An operator who wrote `true`
        meaning "these sessions are confidential" was handed plain VXLAN and a log line when one
        agent turned out to be old, which is the shape of failure this whole design exists to
        refuse: quiet, and on the node nobody was watching.

        - ``required`` (also ``true``, and the default): encrypt, and refuse the session if any
          node it lands on cannot. What a security requirement means.
        - ``prefer``: encrypt where every node can, and fall back to plain VXLAN with the reason
          in the log where they cannot. The rolling-upgrade setting, chosen deliberately.
        - ``disabled`` (also ``false``): never encrypt.

        A per-network ``encryption`` option overrides it for one session: ``True`` is ``required``,
        ``False`` is ``disabled``. Nothing asks for ``prefer`` per session -- a caller either needs
        confidentiality or does not.
        """
        requested = options.get("encryption")
        if requested is not None:
            return (
                OverlayEncryptionPolicy.REQUIRED if requested else OverlayEncryptionPolicy.DISABLED
            )
        return OverlayEncryptionPolicy.parse(self.plugin_config.get("overlay-encryption"))

    async def _nodes_can_encrypt(
        self, etcd: AsyncEtcd, member_agents: list[str], *, policy: OverlayEncryptionPolicy
    ) -> bool:
        """Whether every node this session lands on speaks the overlay encryption profile.

        The two ends of an ESP tunnel must agree on all of it, so one node that cannot do ESN
        makes the session come up carrying nothing. Before encryption was the default that could
        not happen -- an operator turned it on once its nodes were ready. Now it is what a rolling
        upgrade produces on its own, so it is checked.

        Under ``required`` a node that cannot is an error naming the node. Only ``prefer`` falls
        back, and only because somebody asked for that.
        """
        reason = await members_can_encrypt(etcd, member_agents)
        if reason is None:
            return True
        if policy is OverlayEncryptionPolicy.REQUIRED:
            raise NetworkBackendMismatch(
                f"this session's overlay must be encrypted, and {reason}. Upgrade that agent, or"
                " set the network plugin's `overlay-encryption` to 'prefer' to allow an"
                " unencrypted overlay while the cluster is mid-upgrade."
            )
        log.warning(
            "creating this session's overlay UNENCRYPTED under the 'prefer' policy: {}", reason
        )
        return False
