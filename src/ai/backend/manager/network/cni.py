"""Runtime-neutral cluster-network manager plugin (CNI/etcd control plane).

Replaces the Swarm-based `OverlayNetworkPlugin` for containerd and other host-native
runtimes. This plugin owns the *control plane*: it allocates a per-session subnet
(and a VNI for the vxlan backend), selects the data-plane backend (the portable vxlan
overlay unless the operator pins one), and writes the session network descriptor to etcd.
The data plane itself is realized by the agent-side v2 plugins (see BEP-1078, agent plugin).
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import time
import uuid
from collections.abc import Callable, Mapping
from typing import Any, Final, override

from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.network.keys import (
    agent_vtep_key,
    endpoint_key,
    endpoints_prefix,
    member_key,
    members_prefix,
    session_ipam_key,
    session_ipam_prefix,
    session_meta_key,
)
from ai.backend.common.network.types import (
    DEFAULT_VXLAN_PORT,
    ESP_OVERHEAD,
    SESSION_META_GENERATION,
    SESSION_META_READY,
    SESSION_META_STATE,
    VXLAN_OVERHEAD,
    Member,
    NetworkBackendKind,
    OverlayEncryptionPolicy,
    of_generation,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.network import (
    EndpointSuperseded,
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
#: Which incarnation of the session id this record, and everything it caused to be written, is.
#: Minted once when the record is built out of nothing; inherited by every takeover, because a
#: takeover changes who is building the session and not what is allocated to it. See
#: `SESSION_META_GENERATION`.
_GENERATION: Final = SESSION_META_GENERATION

#: How long a second manager waits for the one that claimed a session to finish before taking it
#: over. Long enough to cover a slow create, short enough that a manager killed mid-create does
#: not hold the session up until somebody notices.
_CREATE_HANDOVER_SEC: Final = 60.0
_CREATE_POLL_SEC: Final = 0.5

#: Where a cleanup that has no record left to hang off writes down what it still owes.
#:
#: A cleanup normally keeps the session's own record as its tombstone, and the retry finds it
#: there. The one that cannot is the orphan sweep: by the time it runs, the record already names
#: the incarnation that REPLACED the one being given back, so there is nothing under the session
#: to mark. Its debt goes here instead, keyed by the incarnation, and stays until a sweep gets to
#: the end -- otherwise one transient etcd error leaks a VNI, a subnet and their keys for the life
#: of the cluster.
_CLEANUP_DEBT_PREFIX: Final = "network/cleanup-debt"


def _published(meta: Mapping[str, Any]) -> dict[str, Any]:
    """The session meta as its callers see it, without the create's own bookkeeping.

    ``generation`` stays: an agent is handed it with the rest of the descriptor and fences its
    join on it, which is what stops a launch request that arrived late from joining the session
    that replaced the one it was issued for.
    """
    return {key: value for key, value in meta.items() if key not in (_OWNER, _STATE, _CLAIMED_AT)}


def _debt_key(session_id: str, generation: str) -> str:
    return f"{_CLEANUP_DEBT_PREFIX}/{session_id}/{generation}"


def _generation_stamp_of(raw: str) -> str | None:
    """The incarnation a claim payload carries, or None where it carries none."""
    try:
        stamped = json.loads(raw).get(_GENERATION)
    except ValueError:
        return None
    return str(stamped) if stamped is not None else None


def _generation_of(raw: str | None) -> str | None:
    """The incarnation a session record names, or None when it names none."""
    if not raw:
        return None
    try:
        generation = json.loads(raw).get(_GENERATION)
    except ValueError:
        return None
    return str(generation) if generation is not None else None


def _record_names(meta_raw: str, raw: str, is_vni: bool, key: str | int) -> bool:
    """Whether the session's record names THIS claim.

    Identity, not compatibility. Compatibility (`of_generation`) says whether a claim COULD belong
    to an incarnation, and that is a different question from whether the session is using it --
    wrong in both directions. A claim carrying no incarnation is compatible with every one of
    them, so a second, older claim under a live id looks live and is kept for the life of the
    cluster. A claim carrying a superseded one is compatible with none, so a unit of the very
    block the record names looks dead and is handed to another tenant while the session runs on
    it. The record is what settles both: it names one subnet and one VNI.

    A unit block must also lie inside the block the record names. The payload is what identifies
    the claim, and a payload naming a block the unit is not part of identifies nothing.
    """
    try:
        meta = json.loads(meta_raw)
    except ValueError:
        return False
    if is_vni:
        named_vni = meta.get("vni")
        return named_vni is not None and int(named_vni) == int(key)
    named_subnet = meta.get("subnet")
    if named_subnet is None:
        return False
    try:
        if json.loads(raw).get("subnet") != named_subnet:
            return False
        unit = ipaddress.ip_network(str(key))
        block = ipaddress.ip_network(str(named_subnet))
    except ValueError:
        return False
    # `subnet_of` is typed per address family and refuses a mixed pair, so the families are
    # narrowed rather than the comparison asserted -- the same shape `ipam._acquire_requested`
    # uses.
    return (
        isinstance(unit, ipaddress.IPv4Network)
        and isinstance(block, ipaddress.IPv4Network)
        and unit.subnet_of(block)
    ) or (
        isinstance(unit, ipaddress.IPv6Network)
        and isinstance(block, ipaddress.IPv6Network)
        and unit.subnet_of(block)
    )


def _names_an_allocation(meta_raw: str, is_vni: bool) -> bool:
    """Whether the record has got as far as naming an allocation of this kind.

    A record claims the session id before anything is allocated for it, so it carries no
    ``subnet`` and no ``vni`` key at all until the create publishes. From that point on it names
    exactly one of each -- ``vni`` as null for a backend that uses none -- and it goes on naming
    them under a DELETING tombstone. So the presence of the key, not its value, is what says
    whether the record can answer for a claim of this kind.
    """
    try:
        meta = json.loads(meta_raw)
    except ValueError:
        return False
    return ("vni" if is_vni else "subnet") in meta


def _claim_is_live(meta_raw: str | None, raw: str, is_vni: bool, key: str | int) -> bool:
    """Whether a pool claim is one the session is using.

    Two ways to be live, and a sweep that knows only one of them is wrong in one direction:

    - Stamped with the incarnation the record names. This is what a create still building holds:
      its record names no subnet or VNI yet -- it gets them at publish -- so identity cannot
      answer for it, and a sweep that asked only that reclaimed the pool claims of every create
      in flight.
    - Named by the record, whatever it is stamped with. This is what a session carried over an
      upgrade holds (no stamp at all), and what a block whose units ended up on two incarnations
      holds (a stale stamp). A sweep that asked only about stamps kept every stray unstamped
      claim under a live id forever, and gave away half of a live session's block.

    Neither is `of_generation`, which asks whether a claim COULD belong to an incarnation. A
    claim carrying no incarnation could belong to any, and that says nothing about use.

    A record from before the incarnation field cannot be judged either way: it exists, so
    something made it, and nothing under it is called garbage.
    """
    if meta_raw is None:
        return False  # no record: nothing under this id is in use
    live = _generation_of(meta_raw)
    if live is None:
        return True
    if _names_an_allocation(meta_raw, is_vni):
        # The record names one allocation of this kind, so identity settles it and the stamp adds
        # nothing. Asking the stamp as well kept a stray claim that happens to carry the live
        # incarnation -- a block a create walked away from when it could not take the one it
        # already held, say -- for as long as the session lived: promotion follows the record, so
        # nothing ever moved it, and it looked live, so nothing reclaimed it.
        return _record_names(meta_raw, raw, is_vni, key)
    # Still building: it names nothing yet, and the stamp is the only thing that can say. This is
    # what a create in flight holds, and a sweep that asked identity here reclaimed the pool
    # claims of every create running at the time.
    return _generation_stamp_of(raw) == live


def _tombstone(subnet: str | None, vni: Any, owner: str | None, generation: str | None) -> str:
    """A DELETING record naming what is still allocated, and which cleanup is clearing it.

    ``_cleaner`` is a fresh value on every take. Without it two managers that read the same
    DELETING record both run the cleanup from those same bytes, and the slower one carries on
    deleting after the faster one finished and a new session was built under the same id -- taking
    the new session's endpoint and member keys and giving its subnet and VNI back to the pool. With
    it, only one of the two can hold the record, and the other finds out at its next check.

    ``generation`` is the incarnation being torn down, carried over from the record this tombstone
    replaces. Holding the record is a check the cleanup makes and then acts on, so on its own it
    only narrows the window in which the slower cleaner can reach a new session's keys; the
    generation closes it, because every key and claim that new session writes is stamped with a
    different one and each delete names the incarnation it is for. See `_finish_cleanup`.
    """
    return json.dumps({
        "subnet": subnet,
        "vni": vni,
        _OWNER: owner,
        _STATE: _DELETING,
        _CLEANER: uuid.uuid4().hex,
        _GENERATION: generation,
    })


class CNINetworkPlugin(AbstractNetworkManagerPlugin):
    """Control-plane plugin for the runtime-neutral cluster network (BEP-1078)."""

    _etcd: AsyncEtcd | None
    _subnet_allocator: SubnetAllocator
    _vni_allocator: VNIAllocator
    _endpoint_allocator: EndpointAllocator
    _forced_backend: NetworkBackendKind | None
    #: ``session_id -> generation`` this manager could neither give back nor record a debt for.
    #: Read by health reporting: it is the one leak no retry finds on its own, and the pool
    #: reconciler is what eventually reaches it.
    _unrecoverable: dict[str, str]
    #: Whether a reconciliation pass this manager owes has not yet succeeded. The pool is the only
    #: evidence an orphan claim exists, so a pass that could not run leaves nothing else to find
    #: it: it is retried where a session id comes round, and reported until it goes through.
    _reconciliation_owed: bool

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._etcd = None
        self._forced_backend = None
        self._unrecoverable = {}
        self._reconciliation_owed = False

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
        # What a previous manager life could neither release nor write down. Started from the
        # POOL rather than from a list of what is owed, because the case this exists for is the
        # one where nothing was written down. A manager that cannot reconcile still serves
        # sessions -- refusing to start over a transient etcd error would be worse -- but it does
        # not carry on as if it had: the pass stays owed, it is retried the next time a session id
        # comes round, and `backendai_network_pool_reconcile_pending` says so until it succeeds.
        await self._reconcile_pool_reporting()

    async def _reconcile_pool_reporting(self) -> None:
        """Run a reconciliation pass, and leave behind what its outcome means.

        Not fail-open: a pass that raises used to be a log line and nothing else, so a single
        etcd blip left orphan claims until the next restart while every health surface read
        clean. What it reclaims and what it could not reach are both numbers now.
        """
        metrics = CommonMetricRegistry.instance().network_pool
        try:
            reclaimed = await self.reconcile_pool()
        except Exception:
            self._reconciliation_owed = True
            metrics.observe_reconcile_failed()
            log.exception(
                "could not reconcile the overlay pool; the pass stays owed and is retried the"
                " next time one of this cluster's session ids is used"
            )
            return
        self._reconciliation_owed = False
        metrics.observe_reconcile_succeeded(
            reclaimed=reclaimed, unrecoverable=len(self._unrecoverable)
        )
        if reclaimed:
            log.warning("reclaimed {} pool claim(s) no live session names", reclaimed)

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
        # Anything an earlier incarnation of this id could not give back, before this one claims
        # from the same pools.
        await self.drain_cleanup_debt(session_id)
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
        # The incarnation this create is building. Everything below is stamped with it -- the pool
        # claims, the endpoint records, the address reservations, the pre-seeded members and the
        # descriptor the agents are handed -- so that a cleanup of a PREVIOUS incarnation of this
        # same session id cannot reach any of it, and a launch request issued for that previous one
        # cannot be mistaken for a member of this.
        generation = _generation_of(held)
        subnet: str | None = None
        vni: int | None = None
        try:
            backend = self._select_backend(forced_backend)
            # Size the session subnet to hold every endpoint (removes the fixed-/24 254 cap).
            # Guarded on the record this create holds, exactly as the endpoint writes below are.
            # A pool claim made on behalf of a session that has moved on is named by no meta and
            # released by no cleanup -- it is the one leak nothing can find afterwards.
            pool_guards = {session_meta_key(session_id): held}
            subnet = await self._subnet_allocator.acquire(
                session_id,
                host_count=max(len(endpoints), 1),
                subnet=str(requested_subnet) if requested_subnet else None,
                generation=generation,
                guards=pool_guards,
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
                vni = await self._vni_allocator.acquire(session_id, generation, pool_guards)
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
                _GENERATION: generation,
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
                    generation=generation,
                    # Every address and endpoint key is written in the same store operation that
                    # checks this create still holds the session's record. The stamp says whose a
                    # key is; the guard is what stops one being made at all.
                    guards={session_meta_key(session_id): held},
                )
                endpoint_ips[container_id] = ip
            # Pre-seed the membership table so each agent's reconcile-at-start finds every
            # peer's VTEP already present, instead of racing the etcd watch that delivers a
            # peer's self-published member (which can lag a fast worker's cross-node startup).
            # VXLAN only: the member's tunnel endpoint is the agent's published VTEP. Agents
            # whose VTEP is not yet published are skipped — they fall back to self-publish +
            # watch convergence (no regression).
            if backend is NetworkBackendKind.VXLAN:
                await self._preseed_members(session_id, member_agents, generation, held)
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

        The record is read once at the start and checked again at the end, over the same bytes.
        Between the two a teardown can turn it into a tombstone and give the subnet and the VNI
        back to the pool, and what this would otherwise hand its caller is a data plane built on an
        allocation somebody else now holds -- with the endpoint and address keys it wrote on the
        way there left behind under a session that no longer exists.
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
        # Take the allocation onto this record's incarnation before handing it back. A session
        # carried over an upgrade holds it unstamped, and unstamped is compatible with EVERY
        # incarnation -- so a cleanup for any earlier one would give this running session's subnet
        # and VNI back to the pool. Preserving such a claim is not enough; it has to be taken.
        # Under the record read above, so a promotion on behalf of a session that has moved on
        # does not land.
        if not await self._take_allocation(session_id, meta, raw):
            # The record names an allocation this incarnation does not wholly hold. Handing it
            # back builds a data plane on a subnet or VNI somebody else may own, or on one an
            # earlier cleanup of this id can still give away. Reported as no allocation at all --
            # what `_still_ours` above says in the same situation -- so the caller takes the
            # record and builds again.
            log.warning(
                "session {}'s recorded allocation could not be taken by the incarnation its"
                " record names; treating it as no allocation at all",
                session_id,
            )
            return None
        endpoint_ips: dict[str, str] = {}
        try:
            for endpoint in endpoints:
                container_id = str(endpoint["container_id"])
                hostname = endpoint.get("cluster_hostname")
                ip, _mac = await self._endpoint_allocator.assign(
                    session_id,
                    container_id,
                    subnet,
                    agent_id=str(endpoint["agent_id"]),
                    cluster_hostname=str(hostname) if hostname is not None else None,
                    generation=meta.get(_GENERATION),
                    guards={session_meta_key(session_id): raw},
                )
                endpoint_ips[container_id] = ip
        except EndpointSuperseded:
            # The record moved on under the reuse. To this caller that is not an error but an
            # answer: there is no allocation here to hand back, and the caller re-reads and takes
            # the session again. Reported as such rather than raised out of a converge path.
            log.warning(
                "session {}'s record moved on while its existing allocation was being reused;"
                " treating it as no allocation at all",
                session_id,
            )
            return None
        # The last word, over the exact record the pool was checked against. A destroy that ran
        # while the endpoints above were being written has replaced it, and what this holds is an
        # allocation that has already gone back to the pool.
        # The pool as well as the record. A claim can move between the promotion above and here,
        # and the record alone does not say who holds the block.
        if not await self._still_ours(session_id, subnet, meta.get("vni")):
            log.warning(
                "session {}'s allocation stopped being its own while its endpoints were being"
                " written; not handing it back",
                session_id,
            )
            return None
        if await etcd.get(session_meta_key(session_id), scope=ConfigScopes.GLOBAL) != raw:
            log.warning(
                "session {}'s network record changed while its existing allocation was being"
                " reused; not handing back a subnet and a vni it may no longer hold",
                session_id,
            )
            return None
        log.info(
            "reusing the existing overlay allocation for session {} (subnet {}, vni {})",
            session_id,
            subnet,
            meta.get("vni"),
        )
        return NetworkInfo(
            network_id=session_id, options={**_published(meta), "endpoint_ips": endpoint_ips}
        )

    async def _take_allocation(
        self,
        session_id: str,
        meta: Mapping[str, Any],
        held: str,
        allocated: Mapping[str, str] | None = None,
    ) -> bool:
        """Stamp the subnet and VNI this record names with the incarnation it names.

        Idempotent: a claim already carrying this incarnation is left alone, and one that is not
        this session's is not touched at all.

        Says whether the allocation is now wholly this incarnation's, and the caller has to act on
        it. A failure is not cosmetic: either the claim has moved to somebody else -- so the record
        names an allocation this session does not hold -- or it is still unstamped and an earlier
        incarnation's cleanup can take it. Neither is an allocation to hand to a caller that will
        build a data plane on it.

        :return: ``True`` if nothing was left unpromoted.
        """
        generation = meta.get(_GENERATION)
        if not generation:
            return True  # nothing to promote to
        guards = {session_meta_key(session_id): held}
        taken = True
        subnet = meta.get("subnet")
        if subnet and not await self._subnet_allocator.promote(
            str(subnet), session_id, str(generation), guards, allocated
        ):
            log.warning(
                "session {}'s record names subnet {}, which this incarnation could not take",
                session_id,
                subnet,
            )
            taken = False
        vni = meta.get("vni")
        if vni is not None and not await self._vni_allocator.promote(
            int(vni), session_id, str(generation), guards
        ):
            log.warning(
                "session {}'s record names vni {}, which this incarnation could not take",
                session_id,
                vni,
            )
            taken = False
        return taken

    async def _claim_session(
        self, etcd: AsyncEtcd, session_id: str, token: str, endpoints: list[Any]
    ) -> tuple[str, NetworkInfo | None]:
        """Own the session's record, or hand back what a finished create published.

        Returns ``(the record this call now holds, what somebody else built)``; exactly one of
        the two is meaningful. Ownership is the record's exact bytes, not the token inside them:
        every later write is a compare-and-swap against those bytes, so a call that has been
        superseded finds out when it tries to write rather than overwriting whoever succeeded it.

        The record's generation is minted only where the session is built out of nothing, and
        inherited by every takeover. A takeover changes which manager is finishing the session, not
        what is allocated to it: the subnet and the VNI the previous owner claimed are still
        claimed, still stamped with the generation it used, and a new one here would leave them
        named by nothing this session's cleanup ever releases.

        Raises:
            SessionRecordContested: nobody could be established as the owner within the bound --
                a stream of managers taking the session from each other. Retryable, and reported
                rather than looped on forever.
        """

        def claim(generation: str | None) -> str:
            return json.dumps({
                _OWNER: token,
                _STATE: _CREATING,
                _CLAIMED_AT: time.time(),
                _GENERATION: generation or uuid.uuid4().hex,
            })

        key = session_meta_key(session_id)
        handover = time.monotonic() + _CREATE_HANDOVER_SEC
        give_up = handover + _CREATE_HANDOVER_SEC
        # Every way round this loop ends in a return, a raise, or the poll below. A `continue`
        # that skipped it spun on the CPU without ever yielding to the event loop -- and the
        # record it was waiting on (a READY one whose allocation is gone) is one nothing else was
        # ever going to change, so the manager hung there rather than polling.
        while True:
            # A record built out of nothing is a new incarnation, whatever stood here before: a
            # cleanup that deleted the old one may still be running, and inheriting the generation
            # it holds would put this session's keys within its reach.
            fresh = claim(None)
            if await etcd.put_if_absent(key, fresh):
                return fresh, None
            raw = await etcd.get(key, scope=ConfigScopes.GLOBAL)
            if raw is not None:
                state = json.loads(raw).get(_STATE)
                # Anything taken over is taken over WITH its incarnation; only the put_if_absent
                # paths (above, and after a cleanup that finished) mint a new one.
                ours = claim(_generation_of(raw))
                if state == _DELETING:
                    # A cleanup that did not get to the end. Never taken over as a create: the
                    # tombstone names a subnet and a VNI that are still allocated, and building
                    # over it would run a session on keys somebody else is still deleting. Finish
                    # it instead -- and take it first, into bytes only this call holds, so two
                    # managers that read this same record do not both delete from it. Losing that
                    # take is not an error: fall through to the poll and come back to whatever is
                    # there now.
                    record = json.loads(raw)
                    mine = _tombstone(
                        record.get("subnet"),
                        record.get("vni"),
                        record.get(_OWNER),
                        record.get(_GENERATION),
                    )
                    if await etcd.replace(key, raw, mine):
                        if not await self._finish_cleanup(etcd, session_id, mine):
                            raise SessionCleanupPending(
                                f"session {session_id}'s previous network could not be cleaned"
                                " up; retrying rather than building over what it still holds"
                            )
                        # Nothing of the old incarnation is left, so what goes in here is a new
                        # one -- and a cleanup of the old one that is still running holds a
                        # generation none of this session's keys will carry.
                        again = claim(None)
                        if await etcd.put_if_absent(key, again):
                            return again, None
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
        generation = _generation_of(held)
        tombstone = _tombstone(subnet, vni, owner, generation)
        if not held or not await etcd.replace(session_meta_key(session_id), held, tombstone):
            # The record is not this create's any more. It was either taken over -- in which case
            # the new owner inherited this incarnation and everything claimed for it is still the
            # session's -- or the session was destroyed and built again, and this create is the
            # only thing that still names what ITS incarnation holds. Nobody else will: a cleanup
            # is scoped to the generation on the record, and that is no longer this one.
            await self._release_orphaned_incarnation(etcd, session_id, generation)
            return
        await self._finish_cleanup(etcd, session_id, tombstone)

    async def _release_orphaned_incarnation(
        self, etcd: AsyncEtcd, session_id: str, generation: str | None
    ) -> None:
        """Give back what this create claimed, once the session has moved on without it.

        Only when the record names a DIFFERENT incarnation. The same one means a takeover: another
        manager is finishing this very allocation, and everything here is its to keep. A record
        that has moved on means the session was destroyed and rebuilt, and what this create holds
        -- its pool claims, and any endpoint or address key it wrote before finding out -- is named
        by nothing else. Left alone it leaked for the cluster's lifetime; released without a fence
        it would take the live session's with it.

        The record itself is not touched: it is the new incarnation's.
        """
        if generation is None:
            return  # nothing to scope a release to; a wildcard here would reach the live session
        current = await etcd.get(session_meta_key(session_id), scope=ConfigScopes.GLOBAL)
        if _generation_of(current) == generation:
            log.info(
                "not rolling back session {}: its record is no longer this create's, but still"
                " names the incarnation this create was building",
                session_id,
            )
            return
        log.warning(
            "session {} was rebuilt while a create of an earlier incarnation was still running;"
            " giving back what that create still holds",
            session_id,
        )
        # Written down BEFORE anything is given back, and cleared only when it all was. This
        # sweep has no tombstone to work from -- the record already names the incarnation that
        # replaced this one -- so without a note of its own, a single failed delete leaks a VNI, a
        # subnet and their keys with nothing left anywhere that names them.
        owed = await self._owe_cleanup(etcd, session_id, generation)
        if not await self._sweep_incarnation(etcd, session_id, generation) and not owed:
            # Both halves failed: the state is still there and nothing anywhere names it. Said at
            # the level it deserves, because no retry will find this on its own -- the record
            # already belongs to the incarnation that replaced this one, and the debt that would
            # have pointed at it was never written.
            # Nothing names this any more: not the record (it belongs to the successor), not a
            # tombstone, not a debt note. The pool reconciler is what reaches it -- at the next
            # manager start, or whenever health reporting acts on this.
            self._unrecoverable[session_id] = generation
            log.error(
                "session {}'s incarnation {} could not be given back AND its debt could not be"
                " recorded; nothing names its subnet and VNI now, and only the pool reconciler"
                " will reach them",
                session_id,
                generation,
            )

    async def _owe_cleanup(self, etcd: AsyncEtcd, session_id: str, generation: str) -> bool:
        """Record that an incarnation still has state to give back.

        :return: ``True`` if the note landed; the caller needs to know, because a sweep that fails
            with no note behind it is a leak nothing can find.
        """
        try:
            await etcd.put(
                _debt_key(session_id, generation),
                json.dumps({
                    "session_id": session_id,
                    _GENERATION: generation,
                    "recorded_at": time.time(),
                }),
                scope=ConfigScopes.GLOBAL,
            )
        except Exception:
            # Not fatal to the sweep that follows -- it may well succeed. Fatal to the RETRY.
            log.exception(
                "could not record what session {}'s incarnation {} still owes; if the sweep below"
                " does not finish, nothing will come back for it",
                session_id,
                generation,
            )
            return False
        return True

    async def _sweep_incarnation(self, etcd: AsyncEtcd, session_id: str, generation: str) -> bool:
        """Give back everything one incarnation of a session still holds, and say whether it all
        went.

        The session's own record is never touched: by the time this runs it belongs to whatever
        replaced this incarnation. Clears the debt when there is nothing left.
        """
        complete = True
        for prefix, key_of in (
            (endpoints_prefix, endpoint_key),
            (members_prefix, member_key),
            (session_ipam_prefix, session_ipam_key),
        ):
            if not await self._delete_incarnation(etcd, session_id, prefix, key_of, generation):
                complete = False
        # What the record names NOW, and what it names it WITH. This sweep is for an incarnation
        # the record has moved on from, so a claim under this id may be the live session's: one
        # carrying no incarnation (compatible with the one the record names) or one the record
        # names outright. Neither is this sweep's to give back.
        live_raw = await etcd.get(session_meta_key(session_id), scope=ConfigScopes.GLOBAL)
        live = _generation_of(live_raw)
        live_meta: Mapping[str, Any] = {}
        if live_raw is not None:
            try:
                live_meta = json.loads(live_raw)
            except ValueError:
                live_meta = {}
        live_vni = live_meta.get("vni")
        live_subnet = live_meta.get("subnet")
        try:
            stuck_vnis = await self._vni_allocator.release_all(
                session_id, generation, live, int(live_vni) if live_vni is not None else None
            )
            stuck_blocks = await self._subnet_allocator.release_all(
                session_id, generation, live, str(live_subnet) if live_subnet else None
            )
        except Exception:
            log.exception(
                "could not give back what session {}'s superseded create held", session_id
            )
            return False
        if stuck_vnis or stuck_blocks:
            complete = False
        if complete:
            await etcd.delete(_debt_key(session_id, generation), scope=ConfigScopes.GLOBAL)
        return complete

    def unrecoverable_leaks(self) -> Mapping[str, str]:
        """Incarnations this manager could neither release nor write a debt for, as
        ``session_id -> generation``.

        Empty is the healthy answer. Anything here is pool space that no retry will find on its
        own; `reconcile_pool` is what gives it back.
        """
        return dict(self._unrecoverable)

    async def _reconcile_claims_of(self, etcd: AsyncEtcd, session_id: str) -> int:
        """Give back this session's pool claims that its record does not name.

        The scoped form of `reconcile_pool`, for the moment a session id comes back round. It
        still reads the pool -- a claim nothing names cannot be found any other way -- so it is
        called only where a debt says something is owed under this id.

        It judges a claim by the same rule `reconcile_pool` does, through the same helper. Two
        judgements of one question is how the two paths came to disagree: this one asked
        `of_generation` alone and so kept every stray unstamped claim under a live id forever,
        while the sweep that runs at manager start reclaimed them.
        """
        released = 0
        meta_raw = await etcd.get(session_meta_key(session_id), scope=ConfigScopes.GLOBAL)
        live = _generation_of(meta_raw)
        if meta_raw is not None and live is None:
            return 0  # a record from before the field; not this sweep's to judge
        guard: Mapping[str, str | None] = {session_meta_key(session_id): meta_raw}

        for unit, (owner, _stamp, raw) in (await self._subnet_allocator.claims()).items():
            if owner != session_id or _claim_is_live(meta_raw, raw, False, unit):
                continue
            if await self._subnet_allocator.release_unit(unit, raw, guard):
                released += 1
        for vni, (owner, _stamp, raw) in (await self._vni_allocator.claims()).items():
            if owner != session_id or _claim_is_live(meta_raw, raw, True, vni):
                continue
            if await self._vni_allocator.release_one(vni, raw, guard):
                released += 1
        return released

    async def reconcile_pool(self) -> int:
        """Give back every pool claim whose session no longer names its incarnation.

        The safety net under the debt note, and the only one that does not depend on a note
        surviving. A sweep whose debt could not be written AND whose release failed leaves a
        subnet and a VNI that no session record, tombstone or debt key mentions -- the pool is
        then the sole remaining evidence that they exist, so a reconciler has to start there and
        ask the session, rather than start from a list of what is owed.

        A claim is orphaned when the session's record is gone, or names a DIFFERENT incarnation.
        A claim of the incarnation the record names is live, whatever state that record is in: a
        create still building its session holds its claims legitimately, and its own record is
        what says so.

        Released over the exact bytes read, so a claim rewritten under the sweep is left alone.

        :return: how many claims were given back.
        """
        etcd = self._require_etcd()
        released = 0
        #: Sessions whose live allocation is not stamped with the incarnation their record names,
        #: with the record that says so. Keyed by session, not by claim: a wide block is many
        #: units and each would otherwise queue a promotion of its own, and every promotion
        #: re-reads the whole pool.
        to_take: dict[str, tuple[str, str]] = {}

        # One read of each session's record per sweep, not one per claim. Safe to cache only
        # because the guard is re-checked inside every delete: a record that changed after it was
        # cached makes the delete fail, never succeed wrongly.
        seen: dict[str, str | None] = {}

        async def live_meta(session_id: str) -> str | None:
            if session_id not in seen:
                seen[session_id] = await etcd.get(
                    session_meta_key(session_id), scope=ConfigScopes.GLOBAL
                )
            return seen[session_id]

        async def orphan_guard(
            session_id: str, raw: str, *, is_vni: bool, key: str | int
        ) -> Mapping[str, str | None] | None:
            """The condition under which this claim is garbage, or None if it is live.

            Returned as a CONDITION rather than a yes/no, because the answer stops being true the
            moment it is given: the record can appear, or change, and the claim be released and
            taken by the session it then names. The delete carries this back and the store checks
            it again as one operation with the delete -- so a sweep that judged on a record that
            has since moved on takes nothing.

            Judged by `of_generation`, the same rule everything else uses, and NOT by comparing
            the two generations directly. A claim carrying none is compatible with any incarnation
            by that rule -- it is what a manager from before the field wrote, and what an
            allocator will promote when it next adopts it. Read as a mismatch instead, this sweep
            deleted the live subnet and VNI of every session carried over an upgrade, at the first
            start of the manager that upgraded them.
            """
            key_of_meta = session_meta_key(session_id)
            meta_raw = await live_meta(session_id)
            if meta_raw is None:
                # No record: garbage only while there is still none.
                return {key_of_meta: None}
            if not _claim_is_live(meta_raw, raw, is_vni, key):
                # Garbage while the record still says so.
                return {key_of_meta: meta_raw}
            live = _generation_of(meta_raw)
            if live is not None and _generation_stamp_of(raw) != live:
                # In use, but not on the face of it this incarnation's -- unstamped, or stamped
                # with one the record has moved on from. Taken onto the one the record names,
                # because while the two disagree a cleanup of the other reads it as its own.
                to_take[session_id] = (str(live), meta_raw)
            return None

        for unit, (session_id, generation, raw) in (await self._subnet_allocator.claims()).items():
            guard = await orphan_guard(session_id, raw, is_vni=False, key=unit)
            if guard is None:
                continue
            if await self._subnet_allocator.release_unit(unit, raw, guard):
                released += 1
                log.warning(
                    "reclaimed unit block {}: session {} does not name incarnation {}",
                    unit,
                    session_id,
                    generation,
                )
        for vni, (session_id, generation, raw) in (await self._vni_allocator.claims()).items():
            guard = await orphan_guard(session_id, raw, is_vni=True, key=vni)
            if guard is None:
                continue
            if await self._vni_allocator.release_one(vni, raw, guard):
                released += 1
                log.warning(
                    "reclaimed vni {}: session {} does not name incarnation {}",
                    vni,
                    session_id,
                    generation,
                )
        # Everything the sweep found live but not stamped with the incarnation its record names,
        # taken onto it. Done after the walk so the pool is not being read and rewritten at once.
        #
        # One read of the pool for all of them. Each promotion used to read it again, so the first
        # start of a cluster after the incarnation field -- where EVERY session needs promoting --
        # cost one full scan per session. The listing goes stale as the promotions land, and that
        # is safe: every rewrite is a compare-and-swap over the bytes the listing gave, so a unit
        # that moved fails the swap instead of being written over blind.
        allocated = await self._subnet_allocator.pool_listing() if to_take else {}
        for session_id, (_live, meta_raw) in to_take.items():
            if not await self._take_allocation(
                session_id, json.loads(meta_raw), meta_raw, allocated
            ):
                log.warning(
                    "session {}'s allocation could not be taken onto the incarnation its record"
                    " names; an earlier cleanup of this id can still give it away",
                    session_id,
                )
        released += await self._reclaim_session_keys(etcd)
        # Whatever the sweep gave back is no longer owed. Kept per session rather than cleared
        # wholesale: a leak this pass could not reach is still a leak.
        for session_id in list(self._unrecoverable):
            if not await self._still_owed(etcd, session_id, self._unrecoverable[session_id]):
                del self._unrecoverable[session_id]
        return released

    async def _reclaim_session_keys(self, etcd: AsyncEtcd, only: str | None = None) -> int:
        """Delete the endpoint, member and address keys of incarnations no session names.

        The pool is not the whole of what a cleanup owes. A sweep that could neither release nor
        record leaves these too, and while a member key stands the manager holds the session's VNI
        back from reuse for a node that is not in the session -- so the id itself becomes unusable.

        Judged and deleted as one operation, the same as the pool claims: the record the key is
        garbage by is named as the guard.

        Two different questions, depending on what the record says. Where a record EXISTS and
        names an incarnation, a key compatible with it (`of_generation`, so its own or unstamped)
        is live and stays. Where there is no record at all, nothing under the id is live and every
        key goes -- INCLUDING the unstamped ones, which are otherwise compatible with everything
        and so would be skipped forever: an endpoint or member key written before the incarnation
        field, whose session is long gone, is exactly what nothing else reaches.
        """
        reclaimed = 0
        if only is not None:
            session_ids = [only]
        else:
            try:
                listing = await etcd.get_prefix("network/session", scope=ConfigScopes.GLOBAL)
            except Exception:
                log.exception("could not list the session subtree while reconciling")
                return 0
            # The first path segment of whatever the listing returns. `get_prefix` gives a nested
            # mapping whose top level is already the session id, but taking the segment works on a
            # flat listing too, and this sweep must not depend on which shape it is handed.
            session_ids = sorted({str(key).split("/", 1)[0] for key in dict(listing) if key})
        for session_id in session_ids:
            if not session_id:
                continue
            meta_key = session_meta_key(str(session_id))
            meta_raw = await etcd.get(meta_key, scope=ConfigScopes.GLOBAL)
            live = _generation_of(meta_raw)
            if meta_raw is not None and live is None:
                continue  # a record from before the field; not this sweep's to judge
            guard: Mapping[str, str | None] = {meta_key: meta_raw}
            for prefix, key_of in (
                (endpoints_prefix, endpoint_key),
                (members_prefix, member_key),
                (session_ipam_prefix, session_ipam_key),
            ):
                found = await etcd.get_prefix(
                    prefix(str(session_id)).rstrip("/"), scope=ConfigScopes.GLOBAL
                )
                for name, payload in dict(found).items():
                    if not name or not isinstance(payload, str):
                        continue
                    if meta_raw is not None and of_generation(payload, live):
                        continue  # this incarnation's, or unstamped and so compatible with it
                    if await etcd.compare_and_delete(
                        key_of(str(session_id), str(name)), payload, guards=dict(guard)
                    ):
                        reclaimed += 1
                        log.warning(
                            "reclaimed {}: session {} does not name the incarnation that wrote it",
                            key_of(str(session_id), str(name)),
                            session_id,
                        )
        return reclaimed

    async def _still_owed(self, etcd: AsyncEtcd, session_id: str, generation: str) -> bool:
        """Whether anything of this incarnation is still held anywhere."""
        for unit, (owner, stamped, _raw) in (await self._subnet_allocator.claims()).items():
            if owner == session_id and stamped == generation:
                return True
        for vni, (owner, stamped, _raw) in (await self._vni_allocator.claims()).items():
            if owner == session_id and stamped == generation:
                return True
        for prefix in (endpoints_prefix, members_prefix, session_ipam_prefix):
            found = await etcd.get_prefix(prefix(session_id).rstrip("/"), scope=ConfigScopes.GLOBAL)
            for _name, payload in dict(found).items():
                if isinstance(payload, str) and _generation_of(payload) == generation:
                    return True
        return False

    async def drain_cleanup_debt(self, session_id: str) -> None:
        """Retry every unfinished sweep recorded for this session id.

        Called where a session id is about to be used again -- a create, a teardown -- because
        that is both the moment the leak matters and the moment somebody is already here to pay
        it. A debt that will not clear stays written down for the next one.

        A failure to READ the debt is not "nothing is owed": what is owed may be the very subnet
        or VNI the caller is about to claim. It is raised, so the create or teardown retries
        rather than building over state it could not ask about.

        Raises:
            SessionCleanupPending: this session's outstanding debt could not be read.
        """
        etcd = self._require_etcd()
        try:
            owed = await etcd.get_prefix(
                f"{_CLEANUP_DEBT_PREFIX}/{session_id}", scope=ConfigScopes.GLOBAL
            )
        except Exception as e:
            raise SessionCleanupPending(
                f"could not read what session {session_id}'s earlier incarnations still owe"
                f" ({e}); retrying rather than reusing the id over state nothing has looked at"
            ) from e
        for generation, payload in dict(owed).items():
            if not generation or not isinstance(payload, str):
                continue
            log.warning(
                "retrying the cleanup session {}'s incarnation {} did not finish",
                session_id,
                generation,
            )
            await self._sweep_incarnation(etcd, session_id, str(generation))
        # And what no debt names: a sweep whose note could not be written leaves keys under this
        # id that nothing else will look for. Scoped to this session -- three prefix reads, not a
        # walk of the pool -- because the id is about to be used again either way, and a member
        # key that outlived its incarnation is what holds this session's VNI back from reuse.
        try:
            if reclaimed := await self._reclaim_session_keys(etcd, only=session_id):
                log.warning(
                    "reclaimed {} key(s) of session {} that no incarnation of it names",
                    reclaimed,
                    session_id,
                )
        except Exception as e:
            # Fail closed. A member key that outlived its incarnation holds this session's VNI
            # back from reuse for a node that is not in it, and a stale address reservation
            # refuses the next kernel an address: carrying on here builds a session over state
            # nobody has been able to look at. The caller retries.
            raise SessionCleanupPending(
                f"could not reconcile what earlier incarnations of session {session_id} left"
                f" ({e}); retrying rather than reusing the id over keys nothing has looked at"
            ) from e
        # A reconciliation pass this manager owes -- one that raised at startup -- retried here.
        # Not on a timer, which would need a leader lock this plugin does not hold and would have
        # every manager in an HA set scanning at once; here it is paid once, by whoever is next to
        # use a session id, and stops being owed as soon as it goes through.
        if self._reconciliation_owed:
            await self._reconcile_pool_reporting()
        # The pool half of the same debt, and only where something is actually owed: a claim whose
        # note could not be written is named by nothing, so the id coming back round is the one
        # chance to reach it before a manager restart does. Reading the whole pool is not a cost
        # to pay on every create, so it is paid where a debt or an unrecorded leak says to.
        if owed or session_id in self._unrecoverable:
            if reclaimed := await self._reconcile_claims_of(etcd, session_id):
                log.warning(
                    "reclaimed {} pool claim(s) of session {} that its record does not name",
                    reclaimed,
                    session_id,
                )

    async def _finish_cleanup(self, etcd: AsyncEtcd, session_id: str, tombstone: str) -> bool:
        """Carry a session under a DELETING tombstone through to nothing left, and say whether it
        got there.

        Every destructive step names the INCARNATION the tombstone carries, because this call can
        be resumed late -- a slow etcd, a manager that swapped out -- and by then another cleanup
        may have finished the job and a new session may have been built under the same id. Its
        endpoints, its members and its pool claim are indistinguishable by key from the ones this
        call came to delete: the claim names the session, not the attempt that made it
        (`ipam._claim`). Holding the tombstone is checked first and cheaply ends a cleanup that has
        been superseded, but it is a check followed by a separate delete, so on its own it only
        narrows the window: between the two, the record can be taken, the cleanup finished by
        somebody else and a new session built, and this call's deletes would land on the new
        session's keys. So no key is deleted except over the exact bytes read for it, and only when
        those bytes carry this cleanup's generation -- everything the new session wrote carries a
        different one.

        Returns False when anything was left behind; the caller retries and re-reads.
        """
        generation = _generation_of(tombstone)

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
        for prefix, key_of in (
            (endpoints_prefix, endpoint_key),
            (members_prefix, member_key),
            (session_ipam_prefix, session_ipam_key),
        ):
            if not await still_ours():
                return False
            if not await self._delete_incarnation(etcd, session_id, prefix, key_of, generation):
                return False
        # Everything the POOL says is this session's AND this incarnation's, not only what the
        # tombstone names. A create cancelled between claiming a block and publishing the record
        # that would have named it leaves one no meta mentions, and this is the only thing that
        # reaches it.
        if not await still_ours():
            return False
        try:
            # The record this cleanup holds IS the live one -- it is the tombstone -- so an
            # unstamped claim under this id is this cleanup's to take.
            stuck_vnis = await self._vni_allocator.release_all(session_id, generation, generation)
            stuck_blocks = await self._subnet_allocator.release_all(
                session_id, generation, generation
            )
        except Exception:
            log.exception("cleanup of session {} could not reach the pool", session_id)
            return False
        if stuck_vnis or stuck_blocks:
            return False
        # Last, and only over the tombstone this call is working from.
        await etcd.delete_if_value(session_meta_key(session_id), tombstone)
        return True

    async def _delete_incarnation(
        self,
        etcd: AsyncEtcd,
        session_id: str,
        prefix: Callable[[str], str],
        key_of: Callable[[str, str], str],
        generation: str | None,
    ) -> bool:
        """Delete one of the session's key subtrees, a key at a time and never another
        incarnation's.

        A prefix delete cannot say which session built what it removes: the keys of a session
        started again under this same id sit under the same prefix, and a cleanup resumed late took
        them. Each key is instead deleted over the exact bytes it was read with, and only when
        those bytes name this cleanup's incarnation -- a compare-and-delete a rewrite loses rather
        than one it slips through.

        Returns False when anything was left behind, so the caller keeps the tombstone and retries.
        """
        try:
            found = await etcd.get_prefix(prefix(session_id).rstrip("/"), scope=ConfigScopes.GLOBAL)
        except Exception:
            log.exception(
                "cleanup of session {} could not read its {} keys; its record stays as a"
                " tombstone so this can be finished later",
                session_id,
                prefix(session_id),
            )
            return False
        complete = True
        for name, payload in found.items():
            if not name or not isinstance(payload, str):
                continue  # these keys hold one JSON value each and have no children
            if not of_generation(payload, generation):
                log.info(
                    "leaving {} alone: it belongs to another incarnation of session {}",
                    key_of(session_id, str(name)),
                    session_id,
                )
                continue
            try:
                if not await etcd.delete_if_value(key_of(session_id, str(name)), payload):
                    # Rewritten under this call. Whoever wrote it owns it now.
                    complete = False
            except Exception:
                log.exception(
                    "cleanup of session {} could not delete {}",
                    session_id,
                    key_of(session_id, str(name)),
                )
                complete = False
        return complete

    async def _preseed_members(
        self,
        session_id: str,
        member_agents: list[str],
        generation: str | None = None,
        held: str | None = None,
    ) -> None:
        """Publish each member agent's VTEP, but only where no record stands already.

        Never over one: the agent's own record carries ``joined=true``, the teardown
        acknowledgement `destroy_network` reads before it hands the VNI back to the pool.

        Written under the session's own record when the caller holds one. A member key is what
        holds a session's VNI back from reuse, so one CREATED on behalf of a session that has
        since been torn down blocks the teardown of the session that replaced it -- and nothing
        would ever come for it. A stamp says whose a key is; it cannot stop the key being made.
        """
        etcd = self._require_etcd()
        guards = {session_meta_key(session_id): held} if held else {}
        for agent_id in member_agents:
            vtep = await etcd.get(agent_vtep_key(agent_id), scope=ConfigScopes.GLOBAL)
            if not vtep:
                continue
            member = Member(agent_id=agent_id, host_ip=vtep, vtep_ip=vtep, generation=generation)
            await etcd.compare_and_put(
                member_key(session_id, agent_id),
                json.dumps(member.to_etcd_payload()),
                expected=None,
                guards=guards,
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

        The membership is read TWICE, and the second read is the one that decides: once here as a
        cheap way out, and again after the record has been turned into a tombstone. A node builds
        its data plane only after publishing its membership and re-reading the record (see
        `SessionNetworkCoordinator.start`), so between the tombstone and the second read there is
        no order in which a node can both be missed here and go on to build: either its member
        record is already published, and this read finds it, or its own re-read finds the tombstone
        and it never builds. One read before the tombstone could see neither.
        """
        etcd = self._require_etcd()
        await self.drain_cleanup_debt(network_id)
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
            # A generation of its own, not none: this cleanup must be able to say which
            # incarnation's keys it is entitled to delete, and "any of them" would make it a
            # threat to the session that follows it under this id.
            tombstone = _tombstone(None, None, None, uuid.uuid4().hex)
            if not await etcd.put_if_absent(session_meta_key(network_id), tombstone):
                raise OverlayTeardownPending(
                    f"session {network_id}'s network record appeared while this teardown was"
                    " reading it; retrying against what is there now"
                )
            await self._require_nobody_holding(network_id)
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
        tombstone = _tombstone(
            meta.get("subnet"), meta.get("vni"), meta.get(_OWNER), meta.get(_GENERATION)
        )
        if not await etcd.replace(session_meta_key(network_id), raw, tombstone):
            raise OverlayTeardownPending(
                f"session {network_id}'s network record changed while this teardown was reading"
                " it; retrying against what is there now"
            )
        await self._require_nobody_holding(network_id)
        if not await self._finish_cleanup(etcd, network_id, tombstone):
            raise OverlayTeardownPending(
                f"session {network_id}'s network could not be given back in full; its record"
                " stays as a tombstone naming what is left, and this retries"
            )

    async def _require_nobody_holding(self, session_id: str) -> None:
        """Refuse the teardown while any node's membership stands, with the tombstone already in.

        The read that matters: a node that published its membership before this point is found
        here, and one that publishes after it finds the tombstone on its own re-read and withdraws
        rather than building. The tombstone stays -- it names what is still allocated -- and the
        retry comes back to it.

        Raises:
            OverlayTeardownPending: a node has not let go of the session.
        """
        pending = await self._members_still_holding(session_id)
        if not pending:
            return
        raise OverlayTeardownPending(
            f"session {session_id}'s overlay allocation was taken up by {len(pending)} node(s)"
            f" ({', '.join(sorted(pending))}) as this teardown fenced the record; retrying rather"
            " than reusing the VNI over their live state"
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
