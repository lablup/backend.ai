"""Privileged network helper daemon (BEP-1062).

This is the ONLY component that holds CAP_NET_ADMIN + CAP_SYS_ADMIN. The unprivileged
agent connects over a unix socket and sends semantic verbs (``protocol.py``); the helper
derives every side-effecting value itself and performs the native veth/bridge/netns work
that would otherwise force the whole agent to run privileged.

Trust model (why a compromised agent stays contained):

- **Peer auth**: the socket is 0600 and every connection is checked with SO_PEERCRED;
  only the configured agent uid may drive the helper.
- **No caller-supplied targets**: the agent sends only ``session_id`` / ``container_id``.
  The helper derives device names/subnets from the session it set up and re-resolves the
  container PID from containerd (authoritative) — never trusting a PID/netns/argv/config
  from the agent (closes the argv-injection and PID-TOCTOU classes; see ``netns.py``).
- **Per-session serialization**: one asyncio.Lock per session serializes
  setup/attach/detach/teardown so concurrent requests cannot race the device registry.

Only setup/teardown/attach/detach are exposed; there is no generic "run command" verb.

The helper is a daemon that outlives the agent, but it is not immortal: it can be restarted or
crash while the node's kernels keep running. Its session registry is in memory, so on boot it
rebuilds that registry from its own journal (``journal.py``) reconciled against containerd — see
`recover`. Nothing is taken back from the agent, which is the process this separation exists to
contain.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import struct
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from ai.backend.agent.containerd.oci import SESSION_ID_LABEL
from ai.backend.agent.network.cni import CniAttacher, plan_to_invocations
from ai.backend.agent.network.helper import netns as netns_mod
from ai.backend.agent.network.helper import policy
from ai.backend.agent.network.helper.journal import AttachRecord, HelperJournal
from ai.backend.agent.network.helper.protocol import (
    HelperOp,
    HelperRequest,
    HelperResponse,
    ProtocolError,
)
from ai.backend.agent.network.native_attacher import HostLocalIpam, get_host_local_ipam
from ai.backend.agent.network.port_forward import PortForwarder, forwards_for
from ai.backend.common.network.types import (
    Member,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.containerd.runtime.interface import OciRuntime
    from ai.backend.agent.network.cni import CniRunner
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# Capability bit numbers we care about (linux/capability.h).
_CAP_NAMES = {12: "CAP_NET_ADMIN", 21: "CAP_SYS_ADMIN", 0: "CAP_CHOWN", 1: "CAP_DAC_OVERRIDE"}


def _self_effective_caps() -> str:
    """Decode this process's effective capability set for a startup log line, so the
    operator can confirm the helper holds only the intended (network) capabilities."""
    try:
        with Path("/proc/self/status").open() as f:
            for line in f:
                if line.startswith("CapEff:"):
                    bits = int(line.split()[1], 16)
                    held = [name for bit, name in _CAP_NAMES.items() if bits & (1 << bit)]
                    others = bits & ~sum(1 << b for b in _CAP_NAMES)
                    tail = "" if not others else f" (+{others.bit_count()} more)"
                    return f"CapEff=0x{bits:x} [{','.join(held) or 'none'}]{tail}"
    except OSError:
        pass
    return "CapEff=?"


class HelperError(RuntimeError):
    """A request could not be served. The message returned to the agent is generic;
    the privileged detail is logged helper-side only."""


class _SessionEntry:
    meta: SessionNetMeta
    backend: AbstractNetworkAgentPluginV2[Any]
    attached: dict[str, Any]  # container_id -> EndpointPlan (kept for detach)
    # container_id -> the LOCAL address the helper itself assigned. The only address a published
    # host port may be DNAT'd to; never taken from the agent.
    local_ips: dict[str, str]

    def __init__(self, meta: SessionNetMeta, backend: AbstractNetworkAgentPluginV2[Any]) -> None:
        self.meta = meta
        self.backend = backend
        self.attached = {}
        self.local_ips = {}


class NetworkHelperServer:
    _socket_path: str
    _allowed_uid: int
    _agent_id: str
    _host_ip: str
    _runtime: OciRuntime
    _attacher: CniAttacher
    _forwarder: PortForwarder
    _backends: dict[str, AbstractNetworkAgentPluginV2[Any]]
    _sessions: dict[str, _SessionEntry]
    _locks: dict[str, asyncio.Lock]
    _journal: HelperJournal
    _netns: netns_mod.NetnsPinner
    # The store the attach path allocates LOCAL addresses from. Read on recovery to find the
    # address a pre-restart attach assigned, which is the address its published ports DNAT to.
    _ipam: HostLocalIpam

    def __init__(
        self,
        *,
        socket_path: str,
        allowed_uid: int,
        agent_id: str,
        host_ip: str,
        runtime: OciRuntime,
        cni_runner: CniRunner,
        backends: dict[str, AbstractNetworkAgentPluginV2[Any]],
        forwarder: PortForwarder | None = None,
        journal: HelperJournal | None = None,
        ipam: HostLocalIpam | None = None,
        netns_pinner: netns_mod.NetnsPinner | None = None,
    ) -> None:
        self._socket_path = socket_path
        self._allowed_uid = allowed_uid
        self._agent_id = agent_id
        self._host_ip = host_ip
        self._runtime = runtime
        self._attacher = CniAttacher(cni_runner)
        self._forwarder = forwarder or PortForwarder()
        self._backends = backends
        self._sessions = {}
        self._locks = {}
        self._journal = journal or HelperJournal()
        self._ipam = ipam or get_host_local_ipam()
        self._netns = netns_pinner or netns_mod.NetnsPinner()

    def _lock(self, session_id: str) -> asyncio.Lock:
        lock = self._locks.get(session_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[session_id] = lock
        return lock

    async def serve_forever(self) -> None:
        await self._runtime.open()
        # Before the socket exists, so no request can race the rebuild and be refused for a session
        # this helper is about to remember.
        await self.recover()
        sock_path = Path(self._socket_path)
        if sock_path.exists():
            sock_path.unlink()
        server = await asyncio.start_unix_server(self._handle_conn, path=self._socket_path)
        sock_path.chmod(0o600)
        log.info(
            "network helper listening on {} (agent uid={})", self._socket_path, self._allowed_uid
        )
        log.info("running as uid={} with {}", os.getuid(), _self_effective_caps())
        async with server:
            await server.serve_forever()

    async def recover(self) -> None:
        """Rebuild the session registry after a helper restart, and give back what died while we
        were down.

        The registry is memory; the devices are not. A restarted helper that skipped this would
        hold a node whose bridges, vxlan devices and DNAT rules are all up and carrying traffic,
        while refusing every verb about them — a new kernel could not join a running session, and a
        teardown would report success while leaking the session's devices *and* its node-local
        subnet block, which the pool never gets back.

        Ground truth is this helper's own journal (what it set up and attached) reconciled against
        containerd (what is actually still running). The agent is not consulted: it is the process
        this separation exists to contain, and a session's subnet is exactly the thing it must not
        be able to re-declare.
        """
        try:
            live = await self._live_containers()
            journalled_sessions = await self._journal.sessions()
            journalled_attachments = await self._journal.attachments()
        except Exception:
            log.exception("could not read the helper journal; starting with an empty registry")
            return
        if not journalled_sessions and not journalled_attachments:
            return

        live_sessions = {
            session_id
            for session_id, cfg in journalled_sessions.items()
            if any(sid == session_id for sid in live.values())
        }
        log.info(
            "recovering {} live session(s) of {} journalled; {} container(s) still running",
            len(live_sessions),
            len(journalled_sessions),
            len(live),
        )

        # Dead containers first, while their session's devices and journal records still exist:
        # the DEL needs the plan, and the plan needs the session. Tearing the session down first
        # would release its subnet block and leave these addresses stranded in the IPAM store.
        for container_id, record in journalled_attachments.items():
            if container_id in live:
                continue
            await self._reclaim_dead_container(container_id, record, journalled_sessions)

        for session_id, raw_config in journalled_sessions.items():
            try:
                if session_id in live_sessions:
                    await self._readopt_session(
                        session_id, raw_config, live, journalled_attachments
                    )
                else:
                    await self._reclaim_dead_session(session_id, raw_config)
            except Exception:
                # One unrecoverable session must not cost us the others: a helper that gave up here
                # would refuse every verb for every session on the node.
                log.exception("failed to recover session {}", session_id)

    async def _live_containers(self) -> dict[str, str]:
        """``{container_id: session_id}`` for every container containerd still runs for us."""
        live: dict[str, str] = {}
        for info in await self._runtime.list_container_infos():
            if session_id := info.labels.get(SESSION_ID_LABEL):
                live[info.id] = session_id
        return live

    def _meta_of(self, session_id: str, raw_config: dict[str, Any]) -> SessionNetMeta:
        cfg = policy.validate_network_config(raw_config)
        return SessionNetMeta(
            session_id=session_id,
            subnet=cfg.subnet or "",
            backend=cfg.backend,
            mtu=cfg.mtu,
            vni=cfg.vni,
        )

    async def _readopt_session(
        self,
        session_id: str,
        raw_config: dict[str, Any],
        live: dict[str, str],
        attachments: dict[str, AttachRecord],
    ) -> None:
        """Take a still-running session back over — without touching its data plane.

        `adopt_session_network`, not `setup_session_network`: setup deletes a stale device of the
        session's name before CNI recreates it, which is right for a fresh session and fatal for
        this one — its bridge is up and carrying the kernels' traffic.
        """
        meta = self._meta_of(session_id, raw_config)
        backend = self._resolve_backend(meta.backend)
        await backend.adopt_session_network(meta, self._self_member(meta.backend))
        entry = _SessionEntry(meta, backend)
        for container_id in (cid for cid, sid in live.items() if sid == session_id):
            record = attachments.get(container_id)
            if record is None:
                # Running, in this session, but we never journalled attaching it: it was attached
                # by nobody we know of. Leave it out rather than invent a plan for it — detach
                # still withdraws its DNAT rules, which are tagged with the container itself.
                log.warning("no attach record for live container {}; not adopting", container_id)
                continue
            plan = await self._derive_plan(backend, meta, record.overlay_ip)
            entry.attached[container_id] = plan
            if (local_ip := await self._local_ip_of(plan, container_id)) is not None:
                entry.local_ips[container_id] = local_ip
        self._sessions[session_id] = entry
        log.info(
            "re-adopted session {} with {} attached container(s)", session_id, len(entry.attached)
        )

    async def _reclaim_dead_session(self, session_id: str, raw_config: dict[str, Any]) -> None:
        """Tear down a session whose containers are all gone. Only this pass can: the agent
        already believes it torn down (or is itself gone), so nothing else will ever name these
        devices, and the node-local block they hold is finite."""
        meta = self._meta_of(session_id, raw_config)
        backend = self._resolve_backend(meta.backend)
        await backend.teardown_session_network(session_id)
        await self._journal.forget_session(session_id)
        self._locks.pop(session_id, None)
        log.info("reclaimed the network of dead session {}", session_id)

    async def _reclaim_dead_container(
        self,
        container_id: str,
        record: AttachRecord,
        journalled_sessions: dict[str, dict[str, Any]],
    ) -> None:
        """Give back the host veth, the LOCAL address and the DNAT rules of a container that died
        while we were down. The container's own netns took its end of the veth with it; the host
        side, its address and its rules are ours to release."""
        try:
            await self._forwarder.remove_container(container_id)
            raw_config = journalled_sessions.get(record.session_id)
            if raw_config is not None:
                meta = self._meta_of(record.session_id, raw_config)
                backend = self._resolve_backend(meta.backend)
                plan = await self._derive_plan(backend, meta, record.overlay_ip)
                await self._del_attachment(plan, container_id)
            await self._journal.forget_attachment(container_id)
        except Exception:
            log.exception("failed to reclaim the network of dead container {}", container_id)
        else:
            log.info("reclaimed the network of dead container {}", container_id)

    async def _derive_plan(
        self,
        backend: AbstractNetworkAgentPluginV2[Any],
        meta: SessionNetMeta,
        overlay_ip: str | None,
    ) -> Any:
        """Re-derive the plan a pre-restart attach produced.

        It is a pure function of the session meta and the overlay IP, and its node-local block comes
        from the allocator's journal, which is idempotent per session — so this reproduces the very
        plan that attach applied, which is what makes it safe to detach with.
        """
        kernel_config: dict[str, Any] = {}
        if overlay_ip is not None:
            kernel_config["cluster_network_ip"] = policy.validate_overlay_ip(
                overlay_ip, meta.subnet
            )
        return await backend.attach_endpoint(cast(Any, kernel_config), cast(Any, {}), meta=meta)

    async def _local_ip_of(self, plan: Any, container_id: str) -> str | None:
        """The LOCAL address this container holds, read back from the store the attach allocated it
        from. It is what its published ports DNAT to, so a restarted helper must know it before it
        can serve PUBLISH_PORTS for a pre-restart container."""
        for spec in plan.attachments:
            if spec.role is not NetworkRole.LOCAL:
                continue
            subnet = (spec.cni_config.get("ipam") or {}).get("subnet")
            if not subnet:
                return None
            owners = await self._ipam.owners(str(subnet))
            return owners.get(f"{container_id}/{spec.interface_name}")
        return None

    def _self_member(self, backend: NetworkBackendKind) -> Member:
        return Member(
            agent_id=self._agent_id,
            host_ip=self._host_ip,
            vtep_ip=self._host_ip if backend is NetworkBackendKind.VXLAN else None,
            ip_range=None,
        )

    def _peer_uid(self, writer: asyncio.StreamWriter) -> int:
        sock = writer.get_extra_info("socket")
        creds = sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        _pid, uid, _gid = struct.unpack("3i", creds)
        return int(uid)

    async def _handle_conn(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            uid = self._peer_uid(writer)
            if uid != self._allowed_uid:
                log.warning("rejecting connection from uid {} (allowed {})", uid, self._allowed_uid)
                writer.write(HelperResponse(ok=False, error="unauthorized").encode())
                await writer.drain()
                return
            line = await reader.readline()
            if not line:
                return
            resp = await self._dispatch(line)
            writer.write(resp.encode())
            await writer.drain()
        except Exception:
            log.exception("helper connection handler failed")
            try:
                writer.write(HelperResponse(ok=False, error="internal error").encode())
                await writer.drain()
            except Exception:
                pass
        finally:
            writer.close()

    async def _dispatch(self, line: bytes) -> HelperResponse:
        try:
            req = HelperRequest.decode(line)
            session_id = policy.validate_session_id(req.session_id)
        except (ProtocolError, policy.PolicyViolation) as e:
            return HelperResponse(ok=False, error=str(e))
        async with self._lock(session_id):
            try:
                match req.op:
                    case HelperOp.SETUP_SESSION:
                        await self._setup(session_id, req.network_config or {})
                        return HelperResponse(ok=True)
                    case HelperOp.TEARDOWN_SESSION:
                        await self._teardown(session_id)
                        return HelperResponse(ok=True)
                    case HelperOp.ATTACH_CONTAINER:
                        assigned = await self._attach(session_id, req.container_id, req.ip)
                        return HelperResponse(ok=True, assigned=assigned)
                    case HelperOp.DETACH_CONTAINER:
                        await self._detach(session_id, req.container_id)
                        return HelperResponse(ok=True)
                    case HelperOp.ADD_PEER | HelperOp.DEL_PEER:
                        await self._peer(session_id, req)
                        return HelperResponse(ok=True)
                    case HelperOp.ADD_ENDPOINT | HelperOp.DEL_ENDPOINT:
                        await self._endpoint(session_id, req)
                        return HelperResponse(ok=True)
                    case HelperOp.PUBLISH_PORTS:
                        await self._publish_ports(session_id, req)
                        return HelperResponse(ok=True)
                    case HelperOp.UNPUBLISH_PORTS:
                        return HelperResponse(ok=True, host_ports=await self._unpublish_ports(req))
                    case HelperOp.LIST_PORTS:
                        return HelperResponse(ok=True, forwards=await self._list_ports())
            except (policy.PolicyViolation, netns_mod.NetnsError, HelperError) as e:
                return HelperResponse(ok=False, error=str(e))
            except Exception:
                log.exception("helper op {} failed for session {}", req.op, session_id)
                return HelperResponse(ok=False, error="operation failed")

    def _resolve_backend(self, backend: NetworkBackendKind) -> AbstractNetworkAgentPluginV2[Any]:
        try:
            return self._backends[str(backend)]
        except KeyError:
            raise HelperError("unsupported backend") from None

    async def _setup(self, session_id: str, raw_config: dict[str, Any]) -> None:
        cfg = policy.validate_network_config(raw_config)
        meta = SessionNetMeta(
            session_id=session_id,
            subnet=cfg.subnet or "",
            backend=cfg.backend,
            mtu=cfg.mtu,
            vni=cfg.vni,
        )
        backend = self._resolve_backend(cfg.backend)
        # Journal before the host is mutated: a record with no device is reconciled away on the
        # next boot, while a device with no record is one nobody can ever name again.
        await self._journal.record_session(session_id, dict(raw_config))
        await backend.setup_session_network(meta, self._self_member(cfg.backend))
        self._sessions[session_id] = _SessionEntry(meta, backend)

    async def _teardown(self, session_id: str) -> None:
        entry = self._sessions.pop(session_id, None)
        self._locks.pop(session_id, None)
        if entry is not None:
            await entry.backend.teardown_session_network(session_id)
        elif (raw_config := (await self._journal.sessions()).get(session_id)) is not None:
            # We journalled this session but hold no entry for it — recovery could not rebuild it.
            # Tear it down from the record anyway: reporting success while leaving the bridge up
            # and the session's subnet block claimed is the one outcome we cannot afford, because
            # nothing will ever name them again.
            meta = self._meta_of(session_id, raw_config)
            await self._resolve_backend(meta.backend).teardown_session_network(session_id)
        await self._journal.forget_session(session_id)

    async def _attach(
        self, session_id: str, container_id: str | None, overlay_ip: str | None
    ) -> dict[str, str]:
        if container_id is None:
            raise policy.PolicyViolation("attach requires container_id")
        container_id = policy.validate_container_id(container_id)
        entry = self._sessions.get(session_id)
        if entry is None:
            raise HelperError("attach before setup")
        # The manager-assigned overlay IP (multi-node vxlan) is agent-supplied, so validate it is
        # confined to THIS session's subnet before trusting it; None (single node) keeps the
        # host-local fallback. attach_endpoint reads it from kernel_config["cluster_network_ip"];
        # the deterministic MAC is derived from it server-side (overlay_cni_config).
        kernel_config: dict[str, Any] = {}
        if overlay_ip is not None:
            kernel_config["cluster_network_ip"] = policy.validate_overlay_ip(
                overlay_ip, entry.meta.subnet
            )
        # Authoritative PID resolution from containerd — the agent's view is never trusted.
        pid = await self._runtime.container_pid(container_id)
        if pid is None:
            raise HelperError("no running task for container")
        pinned = self._netns.open(pid)
        try:
            # Re-confirm the PID<->container binding still holds after pinning, so a
            # PID reused between resolution and pin cannot slip through.
            pid2 = await self._runtime.container_pid(container_id)
            if pid2 != pid or not self._netns.alive(pinned):
                raise netns_mod.NetnsError("container task changed during attach")
            # The plan (bridge/subnet CNI config) is derived helper-side from the session meta;
            # the overlay's static IP (+ derived MAC) comes from the validated kernel_config.
            plan = await entry.backend.attach_endpoint(
                cast(Any, kernel_config), cast(Any, {}), meta=entry.meta
            )
            # The native attacher moves the veth by PID (``ip link set ... netns <pid>``),
            # so it needs the ``/proc/<pid>/ns/net`` form, not the pinned-fd path. The pin
            # above already validated this is a live, non-host container netns; we keep the
            # pidfd open across the attach so a vanished process is still detectable.
            # Journalled before the attach, so a helper that dies mid-attach still knows on its next
            # boot that this container may hold a veth and an address to give back.
            await self._journal.record_attachment(
                container_id, session_id, kernel_config.get("cluster_network_ip")
            )
            assigned = await self._attacher.attach(
                plan, container_id=container_id, netns=f"/proc/{pid}/ns/net"
            )
            entry.attached[container_id] = plan
            if (local_ip := assigned.get(NetworkRole.LOCAL)) is not None:
                entry.local_ips[container_id] = local_ip
            return {str(role): ip for role, ip in assigned.items()}
        finally:
            pinned.close()

    async def _publish_ports(self, session_id: str, req: HelperRequest) -> None:
        """DNAT the agent-chosen host ports to this container's LOCAL address.

        The address is the helper's own record from attach, not something the agent sent: that is
        what keeps a compromised agent from pointing one of the node's ports at an arbitrary host.
        """
        if req.container_id is None:
            raise policy.PolicyViolation("publish requires container_id")
        container_id = policy.validate_container_id(req.container_id)
        ports = policy.validate_port_pairs(req.ports)
        entry = self._sessions.get(session_id)
        if entry is None:
            raise HelperError("publish before setup")
        local_ip = entry.local_ips.get(container_id)
        if local_ip is None:
            raise HelperError("publish before attach")
        await self._forwarder.install(forwards_for(container_id, local_ip, ports))

    async def _unpublish_ports(self, req: HelperRequest) -> tuple[int, ...]:
        """Withdraw every rule tagged with this container, returning the host ports it held.

        Needs no session entry: the rules name their own container, so this works after a helper
        restart too, when nothing in memory remembers the attach.
        """
        if req.container_id is None:
            raise policy.PolicyViolation("unpublish requires container_id")
        container_id = policy.validate_container_id(req.container_id)
        return tuple(await self._forwarder.remove_container(container_id))

    async def _list_ports(self) -> tuple[tuple[str, int, str, int], ...]:
        """Every published port on this node, read back from the rules themselves."""
        return tuple(
            (f.container_id, f.host_port, f.container_ip, f.container_port)
            for f in await self._forwarder.list_forwards()
        )

    async def _detach(self, session_id: str, container_id: str | None) -> None:
        if container_id is None:
            raise policy.PolicyViolation("detach requires container_id")
        container_id = policy.validate_container_id(container_id)
        # Withdraw first, and unconditionally: a DNAT rule outliving its container would send the
        # next holder of that host port at an address that is about to disappear. Keyed by the
        # container's own tag, so it holds even if this helper never saw the attach.
        await self._forwarder.remove_container(container_id)
        entry = self._sessions.get(session_id)
        if entry is None:
            await self._journal.forget_attachment(container_id)
            return
        entry.local_ips.pop(container_id, None)
        plan = entry.attached.pop(container_id, None)
        if plan is not None:
            await self._del_attachment(plan, container_id)
        await self._journal.forget_attachment(container_id)

    async def _del_attachment(self, plan: Any, container_id: str) -> None:
        """Hand back the host side of an attachment: the veth and, for host-local IPAM, the
        address. Detach only needs the host side; it does not enter the (possibly already-gone)
        container netns, so no netns handle is required."""
        for inv in reversed(plan_to_invocations(plan)):
            await self._attacher._runner(
                "DEL", ifname=inv.ifname, netns="", container_id=container_id, config=inv.config
            )

    def _require_session(self, session_id: str) -> _SessionEntry:
        entry = self._sessions.get(session_id)
        if entry is None:
            raise HelperError("peer/endpoint programming before session setup")
        return entry

    async def _peer(self, session_id: str, req: HelperRequest) -> None:
        """Program (ADD_PEER) or remove (DEL_PEER) a peer VTEP's overlay forwarding. The
        Member carries only the validated VTEP; the backend uses nothing else here."""
        entry = self._require_session(session_id)
        vtep_ip = policy.validate_ipv4(req.vtep_ip, what="vtep_ip")
        peer = Member(agent_id="", host_ip=vtep_ip, vtep_ip=vtep_ip, ip_range=None)
        if req.op is HelperOp.ADD_PEER:
            await entry.backend.add_peer(session_id, peer)
        else:
            await entry.backend.del_peer(session_id, peer)

    async def _endpoint(self, session_id: str, req: HelperRequest) -> None:
        """Program (ADD_ENDPOINT) or remove (DEL_ENDPOINT) a remote container endpoint's
        unicast FDB + ARP entry."""
        entry = self._require_session(session_id)
        ip = policy.validate_ipv4(req.ip, what="endpoint ip")
        mac = policy.validate_mac(req.mac)
        vtep_ip = policy.validate_ipv4(req.vtep_ip, what="vtep_ip")
        if req.op is HelperOp.ADD_ENDPOINT:
            await entry.backend.add_endpoint(session_id, ip=ip, mac=mac, vtep_ip=vtep_ip)
        else:
            await entry.backend.del_endpoint(session_id, ip=ip, mac=mac, vtep_ip=vtep_ip)
