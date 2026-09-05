"""Runtime-neutral cluster-network manager plugin (CNI/etcd control plane).

Replaces the Swarm-based `OverlayNetworkPlugin` for containerd and other host-native
runtimes. This plugin owns the *control plane*: it allocates a per-session subnet
(and a VNI for the vxlan backend), selects the data-plane backend (the portable vxlan
overlay unless the operator pins one), and writes the session network descriptor to etcd.
The data plane itself is realized by the agent-side v2 plugins (see BEP-1062/agent-plugin-v2.md).
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Mapping
from typing import Any, override

from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.network.keys import (
    agent_vtep_key,
    member_key,
    members_prefix,
    session_meta_key,
    session_prefix,
)
from ai.backend.common.network.types import (
    DEFAULT_VXLAN_PORT,
    ESP_OVERHEAD,
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


class CNINetworkPlugin(AbstractNetworkManagerPlugin):
    """Control-plane plugin for the runtime-neutral cluster network (BEP-1062)."""

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
        # its overlay IP centrally (BEP-1062) so per-node IPs are disjoint.
        endpoints = list(options.get("endpoints", []))
        # Optional explicit subnet (like `docker network create --subnet`): when set, the
        # allocator claims exactly this block and fails on overlap instead of auto-sizing.
        requested_subnet = options.get("subnet")

        await self._require_members_cni_capable(member_agents)
        # A session start that failed downstream is retried with the same id, so this can be a
        # second call for a session that already has an allocation. Allocating again would give
        # it a second subnet and VNI and leave the first ones claimed by nobody: destroy_network
        # releases only what the meta records. Converge on what is already there instead.
        if (existing := await self._existing_allocation(etcd, session_id, endpoints)) is not None:
            return existing
        backend = self._select_backend(forced_backend)
        # Size the session subnet to hold every endpoint (removes the fixed-/24 254 cap).
        # A failure to acquire the subnet claims nothing, so it needs no rollback; every
        # subsequent claim (VNI, endpoint IPs, meta/member keys) is undone on any failure so a
        # partial create never leaks a block/VNI or lets a retry consume fresh ones.
        subnet = await self._subnet_allocator.acquire(
            session_id,
            host_count=max(len(endpoints), 1),
            subnet=str(requested_subnet) if requested_subnet else None,
        )
        vni: int | None = None
        try:
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
            }
            await etcd.put(
                session_meta_key(session_id), json.dumps(meta), scope=ConfigScopes.GLOBAL
            )
            # Assign each endpoint a disjoint overlay IP and record it under endpoints/ (the
            # coordinator programs FDB/ARP from there). Returned map is threaded per-kernel by
            # the launcher into KernelCreationConfig["cluster_network_ip"].
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
            return NetworkInfo(
                network_id=session_id, options={**meta, "endpoint_ips": endpoint_ips}
            )
        except BaseException:
            # BaseException, not Exception: a cancelled create -- the launcher's timeout, a
            # manager shutdown -- otherwise walks away holding the subnet and the VNI. Shielded
            # so the rollback's own awaits are not cancelled in turn and leave it half done.
            await asyncio.shield(
                asyncio.ensure_future(self._rollback_create(session_id, subnet, vni))
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
        subnet = str(meta["subnet"])
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
        return NetworkInfo(network_id=session_id, options={**meta, "endpoint_ips": endpoint_ips})

    async def _rollback_create(self, session_id: str, subnet: str, vni: int | None) -> None:
        """Undo a partially-created session network: release the VNI and subnet blocks and
        delete every key written under the session (meta / endpoints / ipam / members). Each
        step is best-effort and idempotent (deletes of absent keys are no-ops) so cleanup runs
        to completion regardless of how far create_network got before failing."""
        etcd = self._require_etcd()
        try:
            await etcd.delete_prefix(
                session_prefix(session_id).rstrip("/"), scope=ConfigScopes.GLOBAL
            )
        except Exception:
            log.exception("rollback: failed to delete session keys for {}", session_id)
        if vni is not None:
            try:
                await self._vni_allocator.release(vni, session_id)
            except Exception:
                log.exception("rollback: failed to release VNI {} for {}", vni, session_id)
        try:
            await self._subnet_allocator.release(subnet, session_id)
        except Exception:
            log.exception("rollback: failed to release subnet {} for {}", subnet, session_id)

    async def _preseed_members(self, session_id: str, member_agents: list[str]) -> None:
        etcd = self._require_etcd()
        for agent_id in member_agents:
            vtep = await etcd.get(agent_vtep_key(agent_id), scope=ConfigScopes.GLOBAL)
            if not vtep:
                continue
            member = Member(agent_id=agent_id, host_ip=vtep, vtep_ip=vtep)
            await etcd.put(
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
        if raw is not None:
            meta = json.loads(raw)
            if subnet := meta.get("subnet"):
                await self._subnet_allocator.release(subnet, network_id)
            if (vni := meta.get("vni")) is not None:
                await self._vni_allocator.release(int(vni), network_id)
        await etcd.delete_prefix(session_prefix(network_id).rstrip("/"), scope=ConfigScopes.GLOBAL)

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
