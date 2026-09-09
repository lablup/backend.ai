"""Agent-side client + proxies for the privnet daemon (BEP-1078).

These let the *unprivileged* agent keep its normal composition (SessionNetworkCoordinator
owns etcd membership; the orchestrator drives per-container attach) while every privileged
side effect is delegated to the privnet as a semantic verb. The agent sends only
``session_id`` / ``container_id``; it never builds argv, device names, netns paths, or CNI
config — so it holds no CAP_NET_ADMIN / CAP_SYS_ADMIN.

- ``PrivNetClient`` — one short-lived unix-socket round trip per request.
- ``PrivNetBackendProxy`` — an ``AbstractNetworkAgentPluginV2`` whose privileged methods
  (setup/teardown) become RPCs; overlay peer/endpoint programming is handled privnet-side.
- ``PrivNetProvisioner`` — the per-container attach/detach path, replacing
  the in-process ``CniProvisioner`` when the privnet is enabled.
"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast, override

from ai.backend.agent.errors.network import (
    PrivilegedNetworkHelperFailed,
    PrivilegedNetworkHelperUnreachable,
)
from ai.backend.agent.network.caps import probe_caps
from ai.backend.agent.network.port_forward import PortForward
from ai.backend.agent.network.privnet.protocol import (
    PrivNetOp,
    PrivNetRequest,
    PrivNetResponse,
    ProtocolError,
)
from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    EndpointPlan,
    Member,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig


#: The privnet refused or failed a request. Named here for the callers that have always used
#: these names; the classes themselves are `BackendAIError`s, so what reaches the manager says
#: which node and which socket rather than an errno.
PrivNetClientError = PrivilegedNetworkHelperFailed


#: The protocol version that introduced RECOVERY_STATUS. A daemon below it cannot answer, and
#: "did not answer" is not "nothing to report".
_RECOVERY_STATUS_VERSION = 2
#: The protocol version that introduced ENCRYPTION_PROBE.
_ENCRYPTION_PROBE_VERSION = 3
#: The first protocol that FENCES a session request on the incarnation it names. A daemon below it
#: reads the field as noise, so a request issued for a session that no longer exists is carried out
#: against whatever holds its id now -- which is the whole failure the field exists to stop.
_FENCED_SESSION_VERSION = 4
#: How long one privnet verb may take. Generous, because the far side runs real privileged
#: commands under a node-wide lock; finite, because without it one wedged command stops every
#: session operation on this agent with nothing in the log to say why.
_CALL_TIMEOUT_SEC = 120.0


PrivNetUnreachable = PrivilegedNetworkHelperUnreachable


class PrivNetClient:
    _socket_path: str
    #: session_id -> the incarnation this agent set the session up for. Stamped onto every
    #: session-scoped request so the privnet can refuse one issued for an incarnation it no longer
    #: holds -- see `bind_session`.
    _generations: dict[str, str]

    def __init__(self, socket_path: str) -> None:
        self._socket_path = socket_path
        self._generations = {}

    def bind_session(self, session_id: str, generation: str | None) -> None:
        """Remember which incarnation of ``session_id`` this agent is working on.

        Every later request for it carries this, and the privnet refuses one that names an
        incarnation it does not hold. The alternative is to thread the generation through each of
        the fifteen call sites, several of which are handed only a session id (`detach`,
        `teardown_session_network`, the port forwarder) -- and the one that is missed is the hole.

        A session with no generation (a node-local BRIDGE session, or a manager older than the
        field) binds nothing: there is no incarnation to name, and stamping a request with one the
        privnet cannot check gains nothing.
        """
        if generation is None:
            self._generations.pop(session_id, None)
            return
        self._generations[session_id] = generation

    def release_session(self, session_id: str) -> None:
        """Forget the incarnation, once this agent is done with the session."""
        self._generations.pop(session_id, None)

    async def fencing_problems(self) -> dict[str, str]:
        """Whether this daemon checks WHICH incarnation of a session a request was issued for.

        Agent and privnet are separate processes and upgrade separately, so a daemon older than
        the fence reads the incarnation as noise: the session comes up, and the first request
        delayed across a teardown and a rebuild is carried out against whatever holds the id then.

        Reported as readiness rather than checked per session. It is a property of the daemon, not
        of a session; the manager reads readiness before it places anything here, so a node whose
        helper cannot fence stops taking overlay sessions instead of failing them one at a time --
        and a session already built cannot be un-built by a later refusal anyway.

        A failure to ask is itself a problem, as it is for the other two probes.
        """
        try:
            resp = await self.call(PrivNetRequest(PrivNetOp.RECOVERY_STATUS, "status"))
        except (PrivNetClientError, ProtocolError, OSError) as e:
            return {
                "privnet:fencing": (
                    f"this node's privnet could not report its protocol version ({e}), so whether"
                    " it checks which incarnation of a session a request is for is unknown"
                )
            }
        version = resp.version if resp.version is not None else 1
        if version >= _FENCED_SESSION_VERSION:
            return {}
        return {
            "privnet:fencing": (
                f"this node's privnet speaks protocol {version}, which carries out a session"
                " request without checking which incarnation of the session it was issued for"
                f" (protocol {_FENCED_SESSION_VERSION} does); restart it on the agent's version"
            )
        }

    async def recovery_problems(self) -> dict[str, str]:
        """What the privnet says it could not take charge of.

        Never empty-on-failure. Empty means "asked, and it has nothing outstanding" -- and that is
        what the readiness probe turns into "this node may take sessions". A privnet that died
        between the reachability check and this call, or that answered with an internal error,
        knows nothing about its own state, and reporting that as health is how the manager keeps
        scheduling onto a node whose data plane is unmanaged.

        A daemon too old to know the verb is told apart by `version`, not by the shape of its
        error: it cannot report what it does not track, so its silence is not an answer either.
        """
        try:
            resp = await self.call(PrivNetRequest(PrivNetOp.RECOVERY_STATUS, "status"))
        except (PrivNetClientError, ProtocolError, OSError) as e:
            # ProtocolError too: a truncated line (the daemon died mid-answer) and a corrupt frame
            # both arrive here, and both mean this node cannot say what it has not recovered.
            return {
                "privnet:status": f"this node's privnet could not report its recovery state ({e})"
            }
        if resp.version is None or resp.version < _RECOVERY_STATUS_VERSION:
            return {
                "privnet:status": (
                    "this node's privnet speaks protocol"
                    f" {resp.version if resp.version is not None else 1}, which cannot report what"
                    f" it failed to recover (protocol {_RECOVERY_STATUS_VERSION} does); restart it"
                    " on the agent's version"
                )
            }
        return dict(resp.problems or {})

    async def encryption_problems(self) -> dict[str, str]:
        """What the privnet found when it tried to install the overlay's ESP state.

        A failure to ask is itself a problem: the point of asking is to find out whether this node
        can encrypt, and "I could not find out" is not "it can". A daemon too old to know the verb
        is told apart by `version` rather than by the shape of its error.
        """
        try:
            resp = await self.call(PrivNetRequest(PrivNetOp.ENCRYPTION_PROBE, "probe"))
        except (PrivNetClientError, ProtocolError, OSError) as e:
            return {
                "privnet:encryption": (
                    f"this node's privnet could not report whether it can encrypt an overlay ({e})"
                )
            }
        if resp.version is None or resp.version < _ENCRYPTION_PROBE_VERSION:
            return {
                "privnet:encryption": (
                    "this node's privnet speaks protocol"
                    f" {resp.version if resp.version is not None else 1}, which cannot say whether"
                    " it can encrypt an overlay; restart it on the agent's version"
                )
            }
        return dict(resp.problems or {})

    async def reachable(self) -> str | None:
        """None if the privileged helper answers, else why it does not.

        Every device, rule and XFRM object on a privnet-backed node is made by that process, so a
        node whose socket is dead can serve no session at all -- and used to find out at create
        time, one node at a time, with a bare `ConnectionRefusedError` for a reason.
        """
        try:
            _, writer = await asyncio.open_unix_connection(self._socket_path)
        except FileNotFoundError:
            return f"the privileged network helper's socket {self._socket_path} does not exist"
        except ConnectionRefusedError:
            return (
                f"nothing is listening on the privileged network helper's socket"
                f" {self._socket_path} (the privnet process is not running)"
            )
        except PermissionError:
            return (
                f"this agent may not connect to {self._socket_path}; the privnet allows one uid"
                " and it is not this one (it takes it from SUDO_UID, so launching privnet through"
                " a second sudo makes it allow root instead)"
            )
        except OSError as e:
            return f"could not reach the privileged network helper at {self._socket_path}: {e}"
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return None

    async def call(self, req: PrivNetRequest) -> PrivNetResponse:
        req = self._stamped(req)
        try:
            async with asyncio.timeout(_CALL_TIMEOUT_SEC):
                return await self._call(req)
        except TimeoutError as e:
            # A privnet wedged inside a privileged command answers nothing and closes nothing. The
            # agent side of that used to wait forever, holding whatever it was doing for the
            # session; the deadline turns it into a failure the caller can retry or report.
            raise PrivNetClientError(
                f"the privileged network helper at {self._socket_path} did not answer"
                f" {req.op} within {_CALL_TIMEOUT_SEC:.0f}s"
            ) from e

    def _stamped(self, req: PrivNetRequest) -> PrivNetRequest:
        """The request, naming the incarnation this agent bound for its session.

        Done here rather than at each call site so that a verb added later is fenced by default.
        A request that already names one is left alone (SETUP/ADOPT carry theirs in the network
        config), and a session id nothing is bound for is not a session -- the node-wide ops use
        the field as a lock key.
        """
        if req.generation is not None:
            return req
        generation = self._generations.get(req.session_id)
        if generation is None:
            return req
        return dataclasses.replace(req, generation=generation)

    async def _call(self, req: PrivNetRequest) -> PrivNetResponse:
        try:
            reader, writer = await asyncio.open_unix_connection(self._socket_path)
        except OSError as e:
            # Named, not raw: this reaches a session-creation path, and a bare
            # ConnectionRefusedError there says nothing about which node, which socket, or that
            # the whole data plane on this node is down rather than one operation failing.
            raise PrivNetUnreachable(
                f"the privileged network helper at {self._socket_path} is unreachable ({e}); no"
                " overlay device, firewall rule or XFRM object can be made on this node until it"
                " is back"
            ) from e
        try:
            writer.write(req.encode())
            await writer.drain()
            line = await reader.readline()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        resp = PrivNetResponse.decode(line)
        if not resp.ok:
            raise PrivNetClientError(resp.error or "privnet request failed")
        return resp

    async def confine_container(
        self, session_id: str, container_id: str, top_pid: int, limits: Mapping[str, str]
    ) -> None:
        """Have the privnet create this container's cgroup and move its tree in.

        A rootless backend has no daemon to do it (containerd/dockerd declare `cgroupsPath` and
        their root daemon obliges), so an unprivileged agent otherwise leaves the kernel in its own
        cgroup: no memory limit, no cpuset pin, no per-kernel stats.
        """
        await self.call(
            PrivNetRequest(
                op=PrivNetOp.CONFINE_CONTAINER,
                session_id=session_id,
                container_id=container_id,
                cgroup_pid=top_pid,
                cgroup_limits=dict(limits),
            )
        )

    async def release_container(self, session_id: str, container_id: str) -> None:
        await self.call(
            PrivNetRequest(
                op=PrivNetOp.RELEASE_CONTAINER,
                session_id=session_id,
                container_id=container_id,
            )
        )

    async def local_subnet_of(self, session_id: str) -> str | None:
        """The session's node-local LOCAL /26, from the privnet that owns the pool.

        The agent has no LOCAL journal of its own in privnet mode, so this is how it learns the
        subnet it needs to lay out single-node cluster peers. Returns None when the privnet holds
        no block for the session (unknown or torn down) — the query never allocates, so an
        unresolved name degrades to "no peer entry" rather than minting a phantom block.

        A failed query — an unreachable privnet, or one too old to know the verb — also degrades to
        None, not an exception. This lookup sits on the kernel-creation path (``_peer_host_map``):
        raising here would abort the whole kernel over a best-effort name-resolution step, and a
        deploy where the agent leads the privnet in version would break every single-node cluster.
        Degrading loses only the peer /etc/hosts entries (the pre-existing gap), and the kernel
        still comes up.
        """
        try:
            resp = await self.call(PrivNetRequest(op=PrivNetOp.LOCAL_SUBNET, session_id=session_id))
        except (PrivNetClientError, OSError, ProtocolError) as e:
            # PrivNetClientError: an ok=False reply (bad session, or an op an older privnet does
            # not know). OSError: the socket is missing or the privnet is not accepting. Both mean
            # "no answer", and on the kernel-creation path that must degrade, not abort.
            log.warning("privnet LOCAL_SUBNET query for {} failed, degrading: {}", session_id, e)
            return None
        return resp.subnet


def _network_config_from_meta(meta: SessionNetMeta) -> dict[str, Any]:
    return {
        "backend": str(meta.backend),
        "subnet": meta.subnet or None,
        "vni": meta.vni,
        "mtu": meta.mtu,
        # Which incarnation of the session id this declaration is for. Journalled with the rest,
        # so the privnet still knows it after its own restart, and part of the VNI binding digest
        # -- two incarnations that happen to draw the same subnet and VNI are otherwise the same
        # declaration by every field the privnet compares.
        "generation": meta.generation,
        # Not defaulted on the far side: an operator who moved the overlay off 4789 did so because
        # the fabric drops it, and a privnet that quietly used 4789 would build a tunnel nothing
        # carries -- with the agent's own ESP policy written for the other port.
        "vxlan_port": meta.vxlan_port,
        "encryption_key": meta.encryption_key,
    }


class PrivNetBackendProxy(AbstractNetworkAgentPluginV2["AbstractKernel"]):
    """Backend facade the agent's coordinator drives; privileged host ops go to the privnet.

    Single-node overlay concerns (peers/endpoints) are no-ops here because the privnet owns
    the overlay data plane; they are wired as privnet verbs when multi-node lands."""

    _client: PrivNetClient
    _uplink: str

    def __init__(
        self, plugin_config: Any, local_config: Any, *, client: PrivNetClient, uplink: str = "eth0"
    ) -> None:
        super().__init__(plugin_config, local_config)
        self._client = client
        self._uplink = uplink

    @override
    async def init(self, context: Any = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, plugin_config: Any) -> None:
        self.plugin_config = plugin_config

    @override
    async def probe_caps(self) -> AgentNetworkCaps:
        # Non-privileged NIC feature probe stays agent-side.
        return await probe_caps(self._uplink)

    @override
    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        # Bound BEFORE the call, so a setup that fails partway still has its later requests --
        # the teardown that unwinds it, above all -- naming the incarnation it was building.
        self._client.bind_session(meta.session_id, meta.generation)
        await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.SETUP_SESSION,
                session_id=meta.session_id,
                network_config=_network_config_from_meta(meta),
                generation=meta.generation,
            )
        )

    @override
    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Make sure the privnet serving THIS agent knows the session.

        Usually nothing to do: the privnet owns the devices and recovers them from its own journal
        reconciled against containerd, which is the only source the trust model lets it believe.

        But "the privnet" is per agent, and a session can be shared by two agents on one host --
        the second one's kernels join devices the first one's privnet made. That privnet has no
        record of the session, so every later attach is refused with "attach before setup" and
        every peer with "peer programming before session setup".

        ADOPT, not SETUP. Setup deletes the session's bridge, VXLAN device and LOCAL bridge before
        rebuilding them, so sending it here cuts the network out from under every container already
        running on them -- the very containers this call exists to keep serving.
        """
        self._client.bind_session(meta.session_id, meta.generation)
        await self._client.call(
            PrivNetRequest(
                PrivNetOp.ADOPT_SESSION,
                meta.session_id,
                network_config=_network_config_from_meta(meta),
                generation=meta.generation,
            )
        )

    @override
    async def withdraw_session_network(self, session_id: str) -> None:
        """Ask the privnet to drop its ownership of a session whose devices must stay.

        Failures propagate. Swallowing them looks harmless -- the devices remain either way -- but
        what the withdrawal removes is this node's CLAIM: the privnet's journal record, its ESP
        pair claim and its watchdog responsibility. Reporting that as done makes the caller drop
        this node's member key and cancel its teardown retry, so the manager believes the VNI is
        free while all of it is still here.
        """
        await self._client.call(PrivNetRequest(PrivNetOp.WITHDRAW_SESSION, session_id))
        # Only once it landed: a failed withdrawal is retried, and the retry must still name the
        # incarnation whose state this node is trying to let go of.
        self._client.release_session(session_id)

    @override
    async def teardown_session_network(self, session_id: str) -> None:
        await self._client.call(
            PrivNetRequest(op=PrivNetOp.TEARDOWN_SESSION, session_id=session_id)
        )
        self._client.release_session(session_id)

    @override
    async def ensure_session_security(self, session_id: str, peers: Sequence[Member]) -> None:
        # Not inheritable as a no-op: the privnet owns the data plane, so the state that has to be
        # re-asserted lives there, while the reconcile that drives it runs here. A failure comes
        # back as an error and is what keeps this pass's peers out of the coordinator's applied
        # set, so they are reprogrammed once the privnet can protect them again.
        await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.ENSURE_SECURITY,
                session_id=session_id,
                vteps=tuple(peer.vtep_ip for peer in peers if peer.vtep_ip is not None),
            )
        )

    @override
    async def add_peer(self, session_id: str, peer: Member) -> None:
        if peer.vtep_ip is None:
            return  # non-overlay peer (bridge): nothing to program on the overlay
        await self._client.call(
            PrivNetRequest(op=PrivNetOp.ADD_PEER, session_id=session_id, vtep_ip=peer.vtep_ip)
        )

    @override
    async def del_peer(self, session_id: str, peer: Member) -> None:
        if peer.vtep_ip is None:
            return
        await self._client.call(
            PrivNetRequest(op=PrivNetOp.DEL_PEER, session_id=session_id, vtep_ip=peer.vtep_ip)
        )

    @override
    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.ADD_ENDPOINT, session_id=session_id, ip=ip, mac=mac, vtep_ip=vtep_ip
            )
        )

    @override
    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.DEL_ENDPOINT, session_id=session_id, ip=ip, mac=mac, vtep_ip=vtep_ip
            )
        )

    @override
    async def setup_dns_redirect(self, session_id: str, loopback_port: int) -> None:
        # The agent bound the resolver on 127.0.0.1:<loopback_port> and hands only that port down;
        # the privnet derives the gateway from the session it owns and installs the :53 DNAT — a
        # compromised agent can point :53 at its own loopback port, nothing else.
        await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.SETUP_DNS_REDIRECT, session_id=session_id, dns_port=loopback_port
            )
        )

    @override
    async def teardown_dns_redirect(self, session_id: str) -> None:
        await self._client.call(
            PrivNetRequest(op=PrivNetOp.TEARDOWN_DNS_REDIRECT, session_id=session_id)
        )

    @override
    async def attach_endpoint(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
    ) -> EndpointPlan:
        # The live attach goes through PrivNetProvisioner (a semantic ATTACH verb), so the only
        # caller here is the agent's restart recovery, re-deriving the plan it will later detach
        # with. Under a privnet that plan lives privnet-side, and detach is a verb naming the
        # container — so the agent needs nothing but a handle, and an empty plan is that handle.
        # (Raising instead, as this used to, aborted recovery for every container on the node and
        # left them all with no detach path: their host veths and addresses then leaked.)
        return EndpointPlan(attachments=[])

    @override
    async def detach_endpoint(self, kernel: AbstractKernel) -> None:
        pass


class PrivNetProvisioner:
    """The ``ContainerNetworkProvisioner`` that routes per-container attach/detach to
    the privnet. The agent-supplied ``task_pid`` is intentionally ignored: the privnet resolves
    the PID from containerd itself and pins the netns, so a stale/forged PID cannot mislead it.

    One provisioner per session (the session network builds it alongside that session's
    orchestrator), so detach knows its session without having to have witnessed the attach — which
    is what a restarted agent has not done for the kernels that outlived it.
    """

    _client: PrivNetClient
    _session_id: str

    def __init__(self, client: PrivNetClient, session_id: str) -> None:
        self._client = client
        self._session_id = session_id

    async def attach(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
        container_id: str,
        task_pid: int,
        on_planned: Callable[[EndpointPlan], None] | None = None,
    ) -> tuple[EndpointPlan, dict[NetworkRole, str]]:
        # The concrete plan lives privnet-side (kept there for detach), so the agent's copy is an
        # empty handle -- but it is handed over BEFORE the RPC, which is the whole point of the
        # callback: detach names the container, and a call cancelled mid-RPC may already have
        # attached it. Recorded first, that container is detachable; recorded after, it leaked.
        plan = EndpointPlan(attachments=[])
        if on_planned is not None:
            on_planned(plan)
        # Relay the manager-assigned overlay IP (present for multi-node vxlan sessions) so the
        # privnet attaches the container at its central, disjoint address instead of a per-node
        # host-local one. The privnet re-validates it is within the session subnet; None (single
        # node) leaves the privnet on its host-local fallback. The MAC is derived from the IP
        # privnet-side, so it is not sent.
        overlay_ip = kernel_config.get("cluster_network_ip")
        # Single-node cluster: the deterministic LOCAL address this kernel must be pinned at so its
        # real address matches the /etc/hosts map the agent wrote. Sent alongside the overlay IP; the
        # privnet re-validates it is within the session's LOCAL subnet. Without this the privnet takes
        # a host-local dynamic address that need not match the map, and peer resolution is wrong.
        # local_static_ip is an agent-added key, not part of the KernelCreationConfig TypedDict.
        local_ip: str | None = cast(Any, kernel_config).get("local_static_ip")
        resp = await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.ATTACH_CONTAINER,
                session_id=meta.session_id,
                container_id=container_id,
                ip=overlay_ip,
                local_ip=local_ip,
            )
        )
        assigned: dict[NetworkRole, str] = {}
        for role_name, ip in (resp.assigned or {}).items():
            try:
                assigned[NetworkRole(role_name)] = ip
            except ValueError:
                continue
        return plan, assigned

    async def detach(self, plan: EndpointPlan, *, container_id: str, task_pid: int) -> None:
        # The plan is ignored: the privnet holds the real one (and re-derives it after its own
        # restart). Detach names the container; the privnet resolves everything else.
        await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.DETACH_CONTAINER,
                session_id=self._session_id,
                container_id=container_id,
            )
        )


# Any valid identifier; LIST_PORTS is node-wide, so the privnet only uses it as a lock key.
_LIST_LOCK_KEY = "list-ports"


class PrivNetPortForwarder:
    """Same shape as ``PortForwarder``, but the iptables work happens in the privnet.

    The container's address is deliberately not sent: the privnet DNATs to the LOCAL address it
    assigned at attach. So ``install`` drops the ``container_ip`` its argument carries — that is
    the agent's belief, not a fact the privnet is willing to act on.
    """

    _client: PrivNetClient
    # container_id -> session_id; the privnet's session lock and its attach record are keyed by it
    _session_of: Callable[[str], str | None]

    def __init__(self, client: PrivNetClient, session_of: Callable[[str], str | None]) -> None:
        self._client = client
        self._session_of = session_of

    def _session_for(self, container_id: str) -> str:
        session_id = self._session_of(container_id)
        if session_id is None:
            raise PrivNetClientError(f"no session known for container {container_id}")
        return session_id

    async def install(self, forwards: Sequence[PortForward]) -> None:
        if not forwards:
            return
        container_id = forwards[0].container_id
        await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.PUBLISH_PORTS,
                session_id=self._session_for(container_id),
                container_id=container_id,
                ports=tuple(
                    (f.host_port, f.container_port, f.host_ip, f.protocol) for f in forwards
                ),
            )
        )

    async def remove_container(self, container_id: str) -> list[int]:
        # The privnet finds the rules by their container tag, so an unknown session is not fatal:
        # fall back to the container id as the lock key rather than leak the rules.
        session_id = self._session_of(container_id) or container_id
        resp = await self._client.call(
            PrivNetRequest(
                op=PrivNetOp.UNPUBLISH_PORTS,
                session_id=session_id,
                container_id=container_id,
            )
        )
        return list(resp.host_ports or ())

    async def list_forwards(self, *, container_id: str | None = None) -> list[PortForward]:
        resp = await self._client.call(
            PrivNetRequest(op=PrivNetOp.LIST_PORTS, session_id=_LIST_LOCK_KEY)
        )
        forwards = [
            PortForward(
                container_id=cid,
                host_port=hp,
                container_ip=ip,
                container_port=cp,
                owner_agent_id=owner,
                created_at=created_at,
            )
            for cid, hp, ip, cp, owner, created_at in (resp.forwards or ())
        ]
        if container_id is None:
            return forwards
        return [f for f in forwards if f.container_id == container_id]
