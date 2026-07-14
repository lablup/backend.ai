"""Agent-facing composition of session network + container runtime (BEP-1062).

`ContainerdAgent` holds one of these. It bridges the data the manager sends
(``cluster_info["network_config"]`` = the CNINetworkPlugin's ``{backend, subnet, vni,
mtu}``) into the network subsystem, resolves the **per-session** data-plane backend
(vxlan / host-gw / wireguard) by name, and composes:

- per-session setup/teardown via `SessionNetworkCoordinator` (bridge + peers), and
- per-container launch/terminate via `ContainerdKernelOrchestrator`
  (runtime + `ContainerNetworkProvisioner`).

The runtime client and the network subsystem remain separate classes that never
reference each other; this facade and the orchestrator are the only composition points.
Each backend is instantiated per session with the backend the manager selected.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast

from ai.backend.agent.containerd.oci import SESSION_ID_LABEL
from ai.backend.agent.containerd.orchestrator import ContainerdKernelOrchestrator, LaunchResult
from ai.backend.agent.containerd.runtime.interface import ExecResult, OciRuntime
from ai.backend.agent.containerd.session_tracker import SessionContainerTracker, TeardownScope
from ai.backend.agent.errors.network import SessionNetworkGone, UnusableVtep
from ai.backend.agent.network.cni import CniRunner
from ai.backend.agent.network.coordinator import SessionNetworkCoordinator
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator, LocalSubnetLayout
from ai.backend.agent.network.native_attacher import HostLocalIpam
from ai.backend.agent.network.provisioner import ContainerNetworkProvisioner
from ai.backend.common.network.keys import endpoint_key, session_meta_key
from ai.backend.common.network.types import (
    EndpointPlan,
    Member,
    NetworkBackendKind,
    SessionNetMeta,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
    from ai.backend.common.etcd import AbstractKVStore
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_MTU = 1500


def session_net_meta_from_network_config(
    session_id: str, network_config: Mapping[str, Any]
) -> SessionNetMeta:
    """Parse the manager-provided network_config into a SessionNetMeta."""
    vni_raw = network_config.get("vni")
    return SessionNetMeta(
        session_id=session_id,
        subnet=network_config["subnet"],
        backend=NetworkBackendKind(network_config["backend"]),
        mtu=int(network_config.get("mtu") or _DEFAULT_MTU),
        vni=int(vni_raw) if vni_raw is not None else None,
    )


class UnknownNetworkBackend(RuntimeError):
    pass


class ContainerdSessionNetwork:
    _etcd: AbstractKVStore
    _agent_id: str
    _host_ip: str
    _runtime: OciRuntime
    _cni_runner: CniRunner
    _backends: Mapping[str, AbstractNetworkAgentPluginV2[Any]]
    # Builds the per-session container-attach provisioner (one per session, so it can name its
    # own session without having witnessed the attach). Overridable so the privileged network
    # helper can supply a proxy that RPCs attach/detach instead of running them here.
    _make_provisioner: Callable[[AbstractNetworkAgentPluginV2[Any], str], Any]
    _coordinators: dict[str, SessionNetworkCoordinator]
    _orchestrators: dict[str, ContainerdKernelOrchestrator]
    # Tracks container<->session so the last kernel's removal deterministically tears the
    # session network down (otherwise overlay devices + etcd members leak).
    _tracker: SessionContainerTracker
    # container_id -> (session_id, attach plan, task_pid): the network detach inputs captured
    # at attach time, so the clean/remove phase can release the host veth + IPAM + MASQ even
    # though it is a separate lifecycle call from attach. Without it those host-side resources
    # leak (the container's netns removal only reclaims the container-side veth). Rebuilt from
    # ground truth by `recover` after a restart.
    _attachments: dict[str, tuple[str, EndpointPlan, int]]
    # The durable journals this process owns, and so may reconcile on restart. Both are None when
    # a privileged helper owns the host state (it keeps its own records and outlives the agent).
    _local_subnets: LocalSubnetAllocator | None
    _ipam: HostLocalIpam | None
    # One lock per session, so the per-node data-plane setup runs once even when several kernels of
    # the same session are created concurrently on this node (the agent gathers up to
    # kernel_creation_concurrency create_kernel coroutines). Without it two ensure_session calls
    # both pass the "already set up?" check across the setup await, and the second's
    # setup_session_network deletes the vxlan/bridge the first just created.
    _session_locks: dict[str, asyncio.Lock]
    # How many tasks hold or wait on each session's lock, so it is dropped only when the last one
    # leaves (see _session_locked for why its identity must outlive a single critical section).
    _session_lock_users: dict[str, int]
    # This node's validated VTEP, or None when it has no address that can anchor a vxlan tunnel.
    # A vxlan session refuses to set up here in that case, rather than publishing a VTEP its peers
    # cannot reach and building an overlay that carries nothing.
    _vtep_ip: str | None

    def __init__(
        self,
        etcd: AbstractKVStore,
        *,
        agent_id: str,
        host_ip: str,
        runtime: OciRuntime,
        cni_runner: CniRunner,
        backends: Mapping[str, AbstractNetworkAgentPluginV2[Any]],
        provisioner_factory: Callable[[AbstractNetworkAgentPluginV2[Any], str], Any] | None = None,
        local_subnets: LocalSubnetAllocator | None = None,
        ipam: HostLocalIpam | None = None,
        vtep_ip: str | None = None,
    ) -> None:
        self._etcd = etcd
        self._agent_id = agent_id
        self._host_ip = host_ip
        self._vtep_ip = vtep_ip
        self._runtime = runtime
        self._cni_runner = cni_runner
        self._backends = backends
        self._make_provisioner = provisioner_factory or (
            lambda backend, _session_id: ContainerNetworkProvisioner(backend, self._cni_runner)
        )
        self._coordinators = {}
        self._orchestrators = {}
        self._tracker = SessionContainerTracker()
        self._attachments = {}
        self._local_subnets = local_subnets
        self._ipam = ipam
        self._session_locks = {}
        self._session_lock_users = {}

    async def open(self) -> None:
        """Open the runtime client (e.g. establish the containerd gRPC channel)."""
        await self._runtime.open()

    async def close(self) -> None:
        await self._runtime.close()

    # --- restart recovery -------------------------------------------------------------------

    async def recover(self) -> None:
        """Rebuild this node's session-network state from ground truth after an agent restart.

        Every field below is process memory that a restart empties, while the resources they
        name — bridges, veths, IPAM leases, MASQ rules, etcd members — outlive the process. So a
        restarted agent that skipped this would resume its kernels with no way to detach them
        (`remove_container` finds no attachment), no way to tear their session down (the tracker
        is empty), and no reaction to peers joining or leaving (no coordinator, no watch).

        Ground truth is the containerd labels (which container belongs to which session) plus the
        manager's etcd records (the session's meta, and each endpoint's overlay IP). Nothing is
        read back from this process's own prior state, because there is none.

        Finally the durable journals are reconciled against the live containers: a session or a
        container that died while the agent was down still holds its /24 block, its address and
        its host veth, and only this pass can give them back.
        """
        live = await self._live_containers()
        metas: dict[str, SessionNetMeta] = {}
        for session_id in sorted(set(live.values())):
            meta = await self._read_session_meta(session_id)
            if meta is None:
                # The manager dropped the session's meta while we were down; its containers are
                # orphans that clean_kernel will remove. Leave them untracked rather than guess.
                log.warning("no network meta for live session {}; not resuming", session_id)
                continue
            try:
                await self._resume_session(session_id, meta)
            except Exception:
                log.exception("failed to resume session network for {}", session_id)
                continue
            metas[session_id] = meta

        for container_id, session_id in live.items():
            meta = metas.get(session_id)
            if meta is None:
                continue
            self._tracker.track(session_id, container_id)
            try:
                attachment = await self._recover_attachment(container_id, session_id, meta)
            except Exception:
                # one container's plan re-derivation failing (e.g. its overlay endpoint dropped
                # from etcd) must not abort recovery for the rest; it stays tracked but detach-less,
                # and its host leftovers are reclaimed as orphans on a later clean.
                log.exception("failed to recover attachment for container {}", container_id)
                continue
            if attachment is not None:
                self._attachments[container_id] = attachment

        await self._reclaim_orphans(live)

    async def _live_containers(self) -> dict[str, str]:
        """``{container_id: session_id}`` for every container this node still runs for us."""
        live: dict[str, str] = {}
        for info in await self._runtime.list_container_infos():
            if session_id := info.labels.get(SESSION_ID_LABEL):
                live[info.id] = session_id
        return live

    async def _read_session_meta(self, session_id: str) -> SessionNetMeta | None:
        raw = await self._etcd.get(session_meta_key(session_id))
        if not raw:
            return None
        return session_net_meta_from_network_config(session_id, json.loads(raw))

    async def _read_overlay_ip(self, session_id: str, container_id: str) -> str | None:
        raw = await self._etcd.get(endpoint_key(session_id, container_id))
        if not raw:
            return None
        ip = json.loads(raw).get("ip")
        return str(ip) if ip else None

    async def _resume_session(self, session_id: str, meta: SessionNetMeta) -> None:
        backend = self._resolve_backend(meta)
        coordinator = SessionNetworkCoordinator(self._etcd, backend, self._agent_id)
        orchestrator = ContainerdKernelOrchestrator(
            self._runtime, self._make_provisioner(backend, session_id)
        )
        # resume, not start: the devices are up and carrying this session's traffic.
        await coordinator.resume(meta, self._self_member(meta))
        self._coordinators[session_id] = coordinator
        self._orchestrators[session_id] = orchestrator

    async def _recover_attachment(
        self, container_id: str, session_id: str, meta: SessionNetMeta
    ) -> tuple[str, EndpointPlan, int] | None:
        """Reconstruct the detach inputs captured at attach time.

        The plan is re-derived rather than stored: `attach_endpoint` is a function of the session
        meta and the manager-assigned overlay IP, both of which are durable in etcd, and its
        node-local /24 comes from the journal, which is idempotent per session. The task PID is
        asked of containerd. So the plan a restarted agent detaches with is the same plan the
        pre-restart agent attached with.
        """
        pid = await self._runtime.container_pid(container_id)
        if pid is None:
            return None  # no live task; the host-side leftovers are reclaimed as an orphan
        backend = self._resolve_backend(meta)
        kernel_config: dict[str, Any] = {}
        if overlay_ip := await self._read_overlay_ip(session_id, container_id):
            kernel_config["cluster_network_ip"] = overlay_ip
        plan = await backend.attach_endpoint(cast(Any, kernel_config), cast(Any, {}), meta=meta)
        return (session_id, plan, pid)

    async def _reclaim_orphans(self, live: Mapping[str, str]) -> None:
        """Give back what the journals still hold for containers and sessions that are gone.

        Both are keyed off the *live* ground truth (containers by id, sessions by the ids those
        containers carry), never off which sessions successfully resumed: a session whose meta the
        manager dropped, or whose resume raised, is still live if its containers are — reclaiming
        its /24 would free a block whose bridge is up, and the next session to take it would delete
        that live bridge. A block is reclaimed only when no live container names its session.

        Both journals are None under a privileged helper: it owns the host state and its own
        records, and it outlives the agent, so there is nothing here to reclaim.
        """
        if self._ipam is not None:
            await self._reclaim_orphan_addresses(self._ipam, frozenset(live))
        if self._local_subnets is not None:
            await self._reclaim_orphan_subnets(self._local_subnets, frozenset(live.values()))

    async def _reclaim_orphan_addresses(
        self, ipam: HostLocalIpam, live_containers: frozenset[str]
    ) -> None:
        """Release host-local addresses (and their host veths) owned by dead containers.

        The journal names each owner as ``<container_id>/<ifname>``, and the host veth's name is a
        pure function of that pair, so the DEL needs nothing the journal does not already hold.
        Only host-local addresses are journalled, and those are always the LOCAL (NAT) attachment,
        so reconstructing its config from the subnet reproduces what attach emitted.
        """
        for subnet in ipam.subnets():
            for owner, ip in (await ipam.owners(subnet)).items():
                container_id, _, ifname = owner.partition("/")
                if not ifname or container_id in live_containers:
                    continue
                config = {"ipam": {"type": "host-local", "subnet": subnet}, "ipMasq": True}
                try:
                    await self._cni_runner(
                        "DEL", ifname=ifname, netns="", container_id=container_id, config=config
                    )
                except Exception:
                    log.exception("failed to reclaim address of dead container {}", container_id)
                else:
                    log.info("reclaimed address {} of dead container {}", ip, container_id)

    async def _reclaim_orphan_subnets(
        self, allocator: LocalSubnetAllocator, live_sessions: frozenset[str]
    ) -> None:
        """Release node-local /24 blocks whose session has no live container on this node.

        Only the block is reclaimed, not the session's devices: naming them needs the meta the
        manager may already have deleted, and a leftover device is cleared by name by the next
        `setup_session_network` that reuses it. A leaked block would never come back — the pool
        holds 256.
        """
        for session_id in await allocator.sessions():
            if session_id in live_sessions:
                continue
            try:
                await allocator.release(session_id)
            except Exception:
                # one failed release must not abort the sweep and strand the rest
                log.exception("failed to reclaim subnet block of dead session {}", session_id)
            else:
                log.info("reclaimed node-local subnet block of dead session {}", session_id)

    def _resolve_backend(self, meta: SessionNetMeta) -> AbstractNetworkAgentPluginV2[Any]:
        try:
            return self._backends[str(meta.backend)]
        except KeyError:
            raise UnknownNetworkBackend(
                f"no data-plane backend registered for '{meta.backend}' "
                f"(available: {sorted(self._backends)})"
            ) from None

    def _self_member(self, meta: SessionNetMeta) -> Member:
        """This node's membership record — the one every peer reads and programs into its FDB.

        The VTEP published here is the *validated* one, never the raw configured address: a peer
        guards on `vtep_ip is None` only, so an empty or unspecified string would sail through and
        become `bridge fdb append ... dst ''` (fails) or `dst 0.0.0.0` (points nowhere).

        With no usable VTEP this raises rather than publishing a null one, and it does so here --
        the one place both the create path and the RESTART path build the record -- because a null
        is not merely useless to peers, it is destructive: their reconcile drops every endpoint
        whose member has no VTEP, so a restarted node that republished null would have its peers
        tear the FDB/ARP entries for all of its running kernels out from under a healthy session.
        Refusing leaves the previously published record (and this node's live devices) untouched;
        recover() logs the session and moves on.
        """
        if meta.backend is NetworkBackendKind.VXLAN and self._vtep_ip is None:
            raise UnusableVtep(
                f"agent {self._agent_id} cannot take part in the multi-node overlay session"
                f" {meta.session_id}: container.advertised-host/bind-host is not a routable unicast"
                " address this host holds. Set it to the address peers reach this node on."
            )
        return Member(
            agent_id=self._agent_id,
            host_ip=self._host_ip,
            vtep_ip=self._vtep_ip if meta.backend is NetworkBackendKind.VXLAN else None,
            ip_range=None,
        )

    @contextlib.asynccontextmanager
    async def _session_locked(self, session_id: str) -> AsyncIterator[None]:
        """Hold this session's setup/teardown lock.

        The lock is refcounted rather than simply popped on teardown, because its *identity* has to
        stay stable for as long as anyone holds or waits on it. `Lock.release()` only schedules the
        first waiter — the releasing task runs on to its next await — so a teardown that dropped the
        lock from the dict right after releasing it would leave the woken waiter holding an orphan,
        while the next arrival minted a fresh lock and entered the critical section alongside it:
        the very concurrent setup this lock exists to prevent. Registering as a user *before* the
        first await, and dropping the entry only when the last user leaves, keeps one lock per
        in-flight session and still lets the dict shrink to empty.
        """
        lock = self._session_locks.get(session_id)
        if lock is None:
            lock = asyncio.Lock()
            self._session_locks[session_id] = lock
        self._session_lock_users[session_id] = self._session_lock_users.get(session_id, 0) + 1
        try:
            async with lock:
                yield
        finally:
            remaining = self._session_lock_users[session_id] - 1
            if remaining:
                self._session_lock_users[session_id] = remaining
            else:
                del self._session_lock_users[session_id]
                self._session_locks.pop(session_id, None)

    async def ensure_session(
        self, session_id: str, kernel_id: str, network_config: Mapping[str, Any]
    ) -> SessionNetMeta:
        """Resolve the session's backend, set up this node's data plane, publish membership, and
        register the per-session coordinator + orchestrator.

        The kernel is registered as a *user* of the session network here, before its container
        exists: a kernel is created in stages (image pull, scratch, container), and the agent runs
        those stages for several kernels of a session concurrently. Counting only containers would
        make a sibling that dies early look like the session's last kernel and tear the whole data
        plane down under the ones still being built (see SessionContainerTracker.reserve).
        """
        meta = session_net_meta_from_network_config(session_id, network_config)
        if meta.backend is NetworkBackendKind.VXLAN and self._vtep_ip is None:
            # Refuse the session here rather than build an overlay this node cannot be reached on.
            # Silently joining would strand the whole session: the peers program our unusable VTEP,
            # their traffic to our kernels is dropped, and it surfaces as a hang at rendezvous.
            raise UnusableVtep(
                f"agent {self._agent_id} cannot join the multi-node overlay session {session_id}:"
                " container.advertised-host/bind-host is not a routable unicast address this host"
                " holds. Set it to the address peers reach this node on."
            )
        # Serialize per session: the "already set up?" check and the setup that follows straddle an
        # await, so two concurrent kernels of one session would both set the data plane up and the
        # second would delete the first's devices (setup_session_network clears leftovers by name).
        async with self._session_locked(session_id):
            # Claim the session before the idempotency check, so a teardown of this session cannot
            # be decided (by a sibling's removal) between our check and the kernel we are here for.
            self._tracker.reserve(session_id, kernel_id)
            if session_id in self._coordinators:
                # Already set up on this node (e.g. a second kernel of the same session placed
                # here). Session-network setup is per node, not per kernel — do it once.
                return meta
            coordinator: SessionNetworkCoordinator | None = None
            try:
                backend = self._resolve_backend(meta)
                coordinator = SessionNetworkCoordinator(self._etcd, backend, self._agent_id)
                orchestrator = ContainerdKernelOrchestrator(
                    self._runtime, self._make_provisioner(backend, session_id)
                )
                # "No coordinator" does not mean "no data plane": a session whose resume failed on
                # the last restart (or whose meta briefly vanished) keeps running its kernels while
                # this process knows nothing about it. Rebuilding under them would delete the very
                # bridge they are enslaved to and purge the addresses they hold — so ask containerd,
                # not our own memory, and adopt what is already carrying their traffic.
                survivors = await self._live_containers_of(session_id)
                if survivors:
                    await coordinator.resume(meta, self._self_member(meta))
                else:
                    await coordinator.start(meta, self._self_member(meta))
                    # The block this session just claimed can only hold *stale* claims: it has no
                    # containers. Clearing them is what makes a pinned address safe to hand out,
                    # whichever way the block came back to the pool — a teardown purges it too, but
                    # a block reclaimed as an orphan on restart does not, and a claim leaked by a
                    # failed detach is exactly what a later pin would collide with (and, since a pin
                    # that cannot be honoured fails its kernel, keep colliding with).
                    await self._purge_local_addresses(session_id)
            except Exception:
                # Unwind: the coordinator may already have published this node's membership and
                # started its watch tasks, and it is about to go out of scope unregistered — nobody
                # could ever stop it. And the claim above must not outlive the kernel that made it.
                if coordinator is not None:
                    with contextlib.suppress(Exception):
                        await coordinator.stop(session_id)
                self._tracker.release_pending(kernel_id)
                raise
            # Register only AFTER a successful start, so a partial failure (which raises here)
            # doesn't leave a half-set-up coordinator that the idempotency check above would
            # then skip on retry — a retry must re-run the full setup cleanly.
            self._coordinators[session_id] = coordinator
            self._orchestrators[session_id] = orchestrator
            await self._adopt_containers(survivors, session_id, meta)
            return meta

    async def _live_containers_of(self, session_id: str) -> list[str]:
        """The containers this node still runs for a session. Asked of containerd, which is the only
        thing that knows about a session this process failed to resume."""
        live = await self._live_containers()
        return [cid for cid, sid in live.items() if sid == session_id]

    async def _adopt_containers(
        self, container_ids: Sequence[str], session_id: str, meta: SessionNetMeta
    ) -> None:
        """Take over the kernels of a session this node was already running.

        They are what hold the session network open, so a session adopted without them would be
        torn down the moment the kernel that adopted it left — deleting the devices and releasing
        the addresses of containers that are still running. Their detach inputs are re-derived the
        same way a restart re-derives them (from etcd + the journals), so their removal can still
        free the host veth and the address they hold.
        """
        for container_id in container_ids:
            self._tracker.track(session_id, container_id)
            try:
                attachment = await self._recover_attachment(container_id, session_id, meta)
            except Exception:
                # As in recover(): one container's plan re-derivation failing leaves it tracked but
                # detach-less (its host leftovers are reclaimed as orphans), and must not stop the
                # session — or the kernel adopting it — from coming up.
                log.exception("failed to adopt the attachment of container {}", container_id)
                continue
            if attachment is not None:
                self._attachments[container_id] = attachment

    def session_of(self, container_id: str) -> str | None:
        """The session a live container belongs to, from the attach record (rebuilt by `recover`
        after a restart). The helper's port verbs need it to reach the right session lock."""
        attachment = self._attachments.get(container_id)
        return attachment[0] if attachment is not None else None

    async def local_subnet_of(self, session_id: str) -> str | None:
        """This session's node-local LOCAL subnet (the /26 both backends carve from the node pool),
        so a single-node cluster session can lay out deterministic peer IPs in it and write
        /etc/hosts.

        A *lookup*, never an allocation: the session's block is claimed by setup_session_network,
        which has already run by the time a kernel is prepared. Allocating here instead would let a
        kernel that is still being prepared while its session is torn down (a sibling died first)
        mint a fresh block for a dead session — one no teardown will ever release, since the
        session's coordinator is gone, so it would leak from the node's pool until a restart.

        None under a privileged helper, which owns the pool and assigns the addresses itself — the
        agent cannot compute them, so peer resolution there is the helper's to add.
        """
        if self._local_subnets is None:
            return None
        return await self._local_subnets.subnet_of(session_id)

    async def teardown_session(self, session_id: str) -> None:
        # Under the same per-session lock as setup, so a teardown racing the last kernel's setup
        # cannot tear down devices mid-creation (or leave a coordinator the setup is still filling).
        async with self._session_locked(session_id):
            coordinator = self._coordinators.pop(session_id, None)
            self._orchestrators.pop(session_id, None)
            # Before the block goes back, not after: once released, the same CIDR can be handed to
            # the next session, and purging it then would wipe *that* session's claims.
            await self._purge_local_addresses(session_id)
            if coordinator is not None:
                await coordinator.stop(session_id)

    async def _purge_local_addresses(self, session_id: str) -> None:
        """Drop the IPAM claims in this session's LOCAL block, whose containers are all gone."""
        if self._ipam is None or self._local_subnets is None:
            return  # a privileged helper owns both journals, and reclaims them itself
        if (subnet := await self._local_subnets.subnet_of(session_id)) is not None:
            await self._ipam.purge_subnet(subnet)

    def _orchestrator_of(self, session_id: str) -> ContainerdKernelOrchestrator:
        """The session's orchestrator, or a diagnosable error if its network is gone.

        It can be gone under a kernel that is still being created: a sibling that fails early used
        to look like the session's last kernel and take the whole session network with it. The
        tracker's reservation is what prevents that now — this is the guard that keeps the leftover
        case a named error rather than a bare KeyError from a dict lookup.
        """
        orchestrator = self._orchestrators.get(session_id)
        if orchestrator is None:
            raise SessionNetworkGone(
                f"the network of session {session_id} is not set up on this node (it was torn down"
                " while this kernel was being created)"
            )
        return orchestrator

    async def launch_container(
        self,
        session_id: str,
        container_id: str,
        *,
        image_ref: str,
        command: list[str],
        oci_spec: dict[str, Any],
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
    ) -> LaunchResult:
        result = await self._orchestrator_of(session_id).launch(
            container_id,
            image_ref=image_ref,
            command=command,
            oci_spec=oci_spec,
            meta=meta,
            kernel_config=kernel_config,
            cluster_info=cluster_info,
        )
        self._tracker.track(session_id, container_id)
        self._attachments[container_id] = (session_id, result.plan, result.handle.pid)
        return result

    async def create_container(
        self,
        session_id: str,
        container_id: str,
        *,
        image_ref: str,
        command: list[str],
        oci_spec: dict[str, Any],
    ) -> None:
        """Create the container (not started) — maps to AbstractAgent.prepare_container."""
        await self._orchestrator_of(session_id).create(
            container_id, image_ref=image_ref, command=command, oci_spec=oci_spec
        )
        self._tracker.track(session_id, container_id)

    async def start_and_attach_container(
        self,
        session_id: str,
        container_id: str,
        *,
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
    ) -> LaunchResult:
        """Start the container + attach CNI — maps to AbstractAgent.start_container."""
        result = await self._orchestrator_of(session_id).start_and_attach(
            container_id, meta=meta, kernel_config=kernel_config, cluster_info=cluster_info
        )
        self._attachments[container_id] = (session_id, result.plan, result.handle.pid)
        return result

    async def terminate_container(
        self, session_id: str, container_id: str, *, plan: EndpointPlan, task_pid: int
    ) -> None:
        await self._orchestrator_of(session_id).terminate(
            container_id, plan=plan, task_pid=task_pid
        )

    async def exec_in_container(
        self,
        container_id: str,
        args: Sequence[str],
        *,
        uid: int | None = None,
        gid: int | None = None,
        cwd: str | None = None,
        timeout_sec: float = 30.0,
    ) -> ExecResult:
        return await self._runtime.exec_in_container(
            container_id, args, uid=uid, gid=gid, cwd=cwd, timeout_sec=timeout_sec
        )

    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        return await self._runtime.image_entrypoint(image_ref)

    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        await self._runtime.pull_image(image_ref, auth=auth)

    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        await self._runtime.push_image(image_ref, auth=auth)

    async def remove_image(self, image_ref: str, *, sync: bool = False) -> None:
        await self._runtime.remove_image(image_ref, sync=sync)

    async def image_exists(self, image_ref: str) -> bool:
        return await self._runtime.image_exists(image_ref)

    async def image_config_digest(self, image_ref: str) -> str | None:
        return await self._runtime.image_config_digest(image_ref)

    async def image_digest(self, image_ref: str) -> str | None:
        return await self._runtime.image_digest(image_ref)

    async def kill_container(self, container_id: str, *, signal: int) -> None:
        await self._runtime.kill_container(container_id, signal=signal)

    async def stop_container(self, container_id: str, *, grace_period: float) -> None:
        await self._runtime.stop_container(container_id, grace_period=grace_period)

    async def remove_container(self, container_id: str) -> None:
        # Detach the container's network first, using the plan captured at attach: this frees
        # the host veth, releases the host-local IPAM address, and removes the egress MASQ rule
        # when the last container of the subnet leaves. Removing the container reclaims only the
        # container-side veth (via netns teardown), so skipping detach leaks host-side state.
        # Best-effort: a detach hiccup must not block container removal (or session teardown).
        attachment = self._attachments.pop(container_id, None)
        if attachment is not None:
            session_id, plan, task_pid = attachment
            orchestrator = self._orchestrators.get(session_id)
            if orchestrator is not None:
                try:
                    await orchestrator.detach(container_id, plan=plan, task_pid=task_pid)
                except Exception:
                    log.exception("network detach failed for container {}", container_id)
        try:
            await self._runtime.remove_container(container_id)
        finally:
            # Untrack even if the runtime call failed (channel down, deadline): the clean event is
            # not retried — the agent drops the kernel from its registry either way — so a kernel
            # left tracked here would hold its session network open for good.
            scope = self._tracker.untrack(container_id)
            if scope is not None:
                await self._teardown_session_network(scope)

    async def release_kernel(self, kernel_id: str) -> None:
        """Give up a kernel's claim on the session network when it will never reach removal.

        A kernel that fails before its container exists is never cleaned by the agent (it enters the
        kernel registry only once the container is prepared, and a destroy for a kernel it has never
        heard of returns without queueing a clean), so nothing would ever release the claim its
        `ensure_session` made — the session's devices, its LOCAL block and its etcd membership would
        be pinned until the agent restarted. A no-op for a kernel that has a container: that one is
        released by its own removal.
        """
        scope = self._tracker.release_pending(kernel_id)
        if scope is not None:
            await self._teardown_session_network(scope)

    async def _teardown_session_network(self, scope: TeardownScope) -> None:
        """The last kernel of a session on this node is gone — tear its network down
        deterministically via the per-session coordinator (data-plane devices + etcd
        member). Best-effort: a teardown failure must not break kernel cleanup, but it is
        logged so leaks are visible."""
        try:
            if scope.session_id in self._coordinators:
                await self.teardown_session(scope.session_id)
        except Exception:
            log.exception("session network teardown failed for {}", scope.session_id)


def build_containerd_session_network(
    etcd: AbstractKVStore,
    *,
    agent_id: str,
    host_ip: str,
    uplink: str = "eth0",
    runtime: OciRuntime | None = None,
    cni_runner: CniRunner | None = None,
    backends: Mapping[str, AbstractNetworkAgentPluginV2[Any]] | None = None,
    helper_socket: str | None = None,
    local_subnet_layout: LocalSubnetLayout | None = None,
    vtep_ip: str | None = None,
) -> ContainerdSessionNetwork:
    """Assemble a ContainerdSessionNetwork with default real collaborators.

    Defaults: the native containerd gRPC runtime client, the native veth/bridge attach
    runner (host-native iproute2/iptables — no ``/opt/cni/bin`` dependency), and both the
    vxlan (multi-node overlay) and bridge (single-node local) backends on ``uplink``. Any
    collaborator can be overridden (used by ContainerdAgent, and injectable in tests).
    Additional backends (host-gw / wireguard) are registered here as they land.
    """
    # Lazy imports: keep this facade module decoupled from the concrete runtime/backend.
    from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime
    from ai.backend.agent.network.backends.bridge import BridgeNetworkPlugin
    from ai.backend.agent.network.backends.vxlan import VxlanNetworkPlugin
    from ai.backend.agent.network.local_subnet import get_local_subnet_allocator
    from ai.backend.agent.network.native_attacher import (
        NativeBridgeAttachRunner,
        get_host_local_ipam,
    )

    runtime = runtime or ContainerdGrpcRuntime(namespace="backend-ai")
    cni_runner = cni_runner or NativeBridgeAttachRunner()

    # With a helper socket, every privileged host op (bridge setup/teardown + veth/netns
    # attach) is delegated to the CAP_NET_ADMIN/CAP_SYS_ADMIN helper, so this (agent) process
    # needs no network privilege: the backend becomes a proxy and the per-container
    # provisioner RPCs the helper. See ai.backend.agent.network.helper.
    make_provisioner: Callable[[AbstractNetworkAgentPluginV2[Any], str], Any] | None = None
    # Journals this process may reconcile on restart; left None under a helper, which owns the
    # host state, keeps its own records, and outlives the agent.
    owned_local_subnets: LocalSubnetAllocator | None = None
    owned_ipam: HostLocalIpam | None = None
    if helper_socket is not None:
        from ai.backend.agent.network.helper.client import (
            HelperBackendProxy,
            HelperClient,
            HelperProvisioner,
        )

        client = HelperClient(helper_socket)
        proxy = HelperBackendProxy({}, {}, client=client, uplink=uplink)
        backends = {
            str(NetworkBackendKind.VXLAN): proxy,
            str(NetworkBackendKind.BRIDGE): proxy,
        }

        def _helper_provisioner_factory(
            _backend: AbstractNetworkAgentPluginV2[Any], session_id: str
        ) -> Any:
            return HelperProvisioner(client, session_id)

        make_provisioner = _helper_provisioner_factory
    else:
        # The process-wide owner of the node-local pool: shared by both backends here (they carve
        # their LOCAL block out of the same pool) and by every other agent this runtime hosts.
        owned_local_subnets = get_local_subnet_allocator(layout=local_subnet_layout)
        owned_ipam = get_host_local_ipam()
        if backends is None:
            backends = {
                str(NetworkBackendKind.VXLAN): VxlanNetworkPlugin(
                    {}, {}, uplink=uplink, local_subnets=owned_local_subnets
                ),
                str(NetworkBackendKind.BRIDGE): BridgeNetworkPlugin(
                    {}, {}, uplink=uplink, local_subnets=owned_local_subnets
                ),
            }
    return ContainerdSessionNetwork(
        etcd,
        agent_id=agent_id,
        host_ip=host_ip,
        runtime=runtime,
        cni_runner=cni_runner,
        backends=backends,
        provisioner_factory=make_provisioner,
        local_subnets=owned_local_subnets,
        ipam=owned_ipam,
        vtep_ip=vtep_ip,
    )
