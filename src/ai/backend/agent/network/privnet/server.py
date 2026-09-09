"""Privileged network privnet daemon (BEP-1078).

This is the ONLY component that holds CAP_NET_ADMIN + CAP_SYS_ADMIN. The unprivileged
agent connects over a unix socket and sends semantic verbs (``protocol.py``); the privnet
derives every side-effecting value itself and performs the native veth/bridge/netns work
that would otherwise force the whole agent to run privileged.

Trust model (why a compromised agent stays contained):

- **Peer auth**: the socket is 0600 and every connection is checked with SO_PEERCRED;
  only the configured agent uid may drive the privnet.
- **No caller-supplied targets**: the agent sends only ``session_id`` / ``container_id``.
  The privnet derives device names/subnets from the session it set up and re-resolves the
  container PID from THIS NODE'S runtime — never trusting a PID/netns/argv/config from the
  agent (closes the argv-injection and PID-TOCTOU classes; see ``netns.py``). On containerd
  that resolution is authoritative on its own: the PID comes from a root-owned daemon. A
  rootless backend has no daemon and its container record is a journal the agent writes, so
  the netns is additionally required to be owned by the agent's own user namespace — an
  unprivileged agent can only have created namespaces it owns, which bounds it to what it
  could have made anyway (``expected_owner_uid`` in ``netns.py``).
- **Session binding**: a container may only be attached to the session that owns it, read from
  the container's own label rather than from the request.
- **Only the agent's own processes**: a cgroup operation names a PID, and that PID must run as
  the agent's uid, so a root daemon cannot be moved into a cgroup the agent controls.
- **Per-session serialization**: one asyncio.Lock per session serializes
  setup/attach/detach/teardown so concurrent requests cannot race the device registry.

Only setup/teardown/attach/detach are exposed; there is no generic "run command" verb.

The privnet is a daemon that outlives the agent, but it is not immortal: it can be restarted or
crash while the node's kernels keep running. Its session registry is in memory, so on boot it
rebuilds that registry from its own journal (``journal.py``) reconciled against containerd — see
`recover`. Nothing is taken back from the agent, which is the process this separation exists to
contain.
"""

from __future__ import annotations

import asyncio
import contextlib
import enum
import logging
import os
import pwd
import socket
import stat
import struct
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from ai.backend.agent.errors.network import (
    PrivnetAlreadyRunning,
    PrivnetConfigurationInvalid,
    UnsafePrivnetSocket,
    UnusableVtep,
)
from ai.backend.agent.network.cni import CniAttacher, plan_to_invocations
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator, get_local_subnet_allocator
from ai.backend.agent.network.locator import ContainerLocator
from ai.backend.agent.network.native_attacher import (
    HostLocalIpam,
    get_host_local_ipam,
    redirect_session_dns,
    remove_dns_redirect,
)
from ai.backend.agent.network.port_forward import PortForwarder, forwards_for
from ai.backend.agent.network.privnet import netns as netns_mod
from ai.backend.agent.network.privnet import policy
from ai.backend.agent.network.privnet.journal import AttachRecord, PrivNetJournal
from ai.backend.agent.network.privnet.protocol import (
    PROTOCOL_VERSION,
    ForwardEntry,
    PrivNetOp,
    PrivNetRequest,
    PrivNetResponse,
    ProtocolError,
)
from ai.backend.agent.network.vni_registry import (
    Binding,
    VniConflict,
    VniRegistry,
    config_digest,
)
from ai.backend.common.network.types import (
    Member,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.network.cni import CniRunner
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: How often to retry bringing down a tunnel the recovery preflight could not close. Slow:
#: the thing being waited for is an operator or a transient kernel condition, not a race.
_FAIL_CLOSE_RETRY_INTERVAL = 30.0
#: How often to retry a recovery that could not complete. Same reasoning as above:
#: what is being waited for is a runtime or filesystem coming back, not a race.
_RECOVERY_RETRY_INTERVAL = 30.0
#: The longest one request may take, WAITING FOR THE BARRIER INCLUDED. Well above any real
#: operation -- each privileged command is capped far lower and a request runs a handful of them.
#:
#: Deliberately below the agent client's own deadline (`client._CALL_TIMEOUT_SEC`). Above it, the
#: agent gives up first and the privnet goes on working: the RPC says the operation failed while
#: the host state says it succeeded, minutes later, and nothing reconciles the two. Below it, the
#: server is always the one that decides, and the agent sees the answer it decided on.
_REQUEST_TIMEOUT_SEC = 90.0
#: The longest a recovery pass may hold the barrier. Larger than a request because it works
#: through every session on the node, and finite for the same reason: nothing else runs while it
#: does. What it does not finish stays on the books and the timer brings it back.
_RECOVERY_TIMEOUT_SEC = 240.0
#: Verbs that only read. They skip the node-wide mutation barrier, because nothing they do can
#: race a recovery pass and a readiness probe must not wait on one.
_READ_ONLY_OPS = frozenset({
    PrivNetOp.RECOVERY_STATUS,
    # It writes, but only on documentation addresses nothing else can name, so it cannot race a
    # recovery pass -- and a readiness probe must not queue behind one.
    PrivNetOp.ENCRYPTION_PROBE,
    PrivNetOp.LIST_PORTS,
    PrivNetOp.LOCAL_SUBNET,
})


# Capability bit numbers we care about (linux/capability.h).
_CAP_NAMES = {12: "CAP_NET_ADMIN", 21: "CAP_SYS_ADMIN", 0: "CAP_CHOWN", 1: "CAP_DAC_OVERRIDE"}


def _self_effective_caps() -> str:
    """Decode this process's effective capability set for a startup log line, so the
    operator can confirm the privnet holds only the intended (network) capabilities."""
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


class PrivNetError(RuntimeError):
    """A request could not be served. The message returned to the agent is generic;
    the privileged detail is logged privnet-side only."""


class _Liveness(enum.Enum):
    """What the runtime says about something a recovery pass is about to delete."""

    GONE = "gone"
    #: Running again under a container THIS agent owns.
    OURS = "ours"
    #: Running under a container another agent on this host owns. Its devices are not ours to
    #: delete and its session is not ours to adopt -- but our own stale record of it is ours to
    #: drop, and nothing else will ever do it.
    FOREIGN = "foreign"
    UNKNOWN = "unknown"

    @property
    def reason(self) -> str:
        if self is _Liveness.OURS:
            return "it is running again; this pass must adopt it rather than reclaim it"
        if self is _Liveness.FOREIGN:
            return "another agent on this host is running it"
        return "the runtime could not be asked whether it is still gone"


class _ReclaimDeferred(Exception):
    """The runtime disagrees with the snapshot, so nothing was reclaimed.

    Neither a failure nor a completed reclaim: the caller must keep it on the books, because the
    only other outcome it knows -- a clean return -- clears the marker that brings the retry back.
    """


class _SessionEntry:
    meta: SessionNetMeta
    backend: AbstractNetworkAgentPluginV2[Any]
    attached: dict[str, Any]  # container_id -> EndpointPlan (kept for detach)
    # container_id -> the LOCAL address the privnet itself assigned. The only address a published
    # host port may be DNAT'd to; never taken from the agent.
    local_ips: dict[str, str]

    #: The configuration digest this session's VNI is bound to node-wide, so the binding is
    #: released under the same name it was made under.
    digest: str
    #: Whether the node-wide registry actually records this session's VNI as BUILT. False means
    #: this entry exists but the store never took the mark, and another privnet reads the VNI as a
    #: half-finished build it may rebuild -- over these very devices. An entry in that state must
    #: not let a later ADOPT return early, or the retry that would fix it never runs.
    built: bool

    def __init__(
        self,
        meta: SessionNetMeta,
        backend: AbstractNetworkAgentPluginV2[Any],
        digest: str = "",
    ) -> None:
        self.meta = meta
        self.backend = backend
        self.digest = digest
        self.built = False
        self.attached = {}
        self.local_ips = {}


def _descendants(pid: int) -> list[int]:
    """Every process under ``pid``, so the whole container tree lands in the cgroup."""
    found: list[int] = []
    frontier = [pid]
    while frontier:
        current = frontier.pop()
        try:
            children = Path(f"/proc/{current}/task/{current}/children").read_text().split()
        except OSError:
            continue
        for raw in children:
            child = int(raw)
            found.append(child)
            frontier.append(child)
    return found


def _make_cgroup(cgroup: Path, limits: Mapping[str, str], top_pid: int) -> None:
    """Create the leaf, write the limits and move the tree in — reporting what did not land.

    Every write here used to be swallowed, which reproduced on this path the exact defect the
    delegation exists to fix: a kernel running with `memory.max = max` and nothing anywhere saying
    so. An undelegated controller or a read-only leaf is not a corner case (it is what an operator
    sees after changing the cgroup layout), so a limit that could not be written is raised — the
    agent already logs it against the container and starts the kernel anyway, so the launch is not
    made more fragile, only less silent.
    """
    parent = cgroup.parent
    parent.mkdir(parents=True, exist_ok=True)
    # A controller only reaches a child if the parent delegates it. Not fatal on its own: the leaf
    # may already have the files, and the per-limit failures below are the ones that matter.
    with contextlib.suppress(OSError):
        (parent / "cgroup.subtree_control").write_text("+cpu +cpuset +io +memory")
    cgroup.mkdir(exist_ok=True)
    failed: list[str] = []
    for name, value in limits.items():
        # Only the leaf's own interface files, never a path the caller composed.
        if "/" in name or name.startswith("."):
            failed.append(f"{name} (not an interface file)")
            continue
        try:
            (cgroup / name).write_text(value)
        except OSError as e:
            failed.append(f"{name}={value} ({e.strerror})")
    moved = False
    for pid in (top_pid, *_descendants(top_pid)):
        try:
            (cgroup / "cgroup.procs").write_text(str(pid))
            moved = True
        except ProcessLookupError:
            continue  # a transient setup process that already exited
        except OSError as e:
            failed.append(f"cgroup.procs={pid} ({e.strerror})")
    if not moved:
        # Limits on a cgroup nobody is in confine nothing, so this is a failure even if every
        # interface file was written.
        failed.append(f"no process of the tree under {top_pid} could be moved in")
    if failed:
        raise PrivNetError(f"cgroup {cgroup} only partly applied: {'; '.join(failed)}")


def _remove_cgroup(cgroup: Path) -> None:
    try:
        cgroup.rmdir()
    except FileNotFoundError:
        pass  # never created, or already reclaimed
    except OSError as e:
        # EBUSY means processes are still in it. Left behind rather than retried here, but said
        # out loud: these accumulate one per kernel and nothing else revisits this path.
        log.warning("could not remove the cgroup {}: {!r}", cgroup, e)


class PrivNetServer:
    _socket_path: str
    _allowed_uid: int
    _agent_id: str
    _host_ip: str
    # The validated VTEP. The privnet, not the agent, owns the host's networking when it runs, so it
    # is the one that publishes this node's membership — and an unusable address published there is
    # what strands a whole overlay session (see network.vtep). None disables vxlan sessions here.
    _vtep_ip: str | None
    _runtime: ContainerLocator
    _attacher: CniAttacher
    _forwarder: PortForwarder
    _backends: dict[str, AbstractNetworkAgentPluginV2[Any]]
    _sessions: dict[str, _SessionEntry]
    _locks: dict[str, asyncio.Lock]
    # How many in-flight ops hold or wait on each session's lock, so the lock is dropped from
    # `_locks` only when the last one leaves (see `_session_locked`) — never while it is still held.
    _lock_users: dict[str, int]
    _journal: PrivNetJournal
    _netns: netns_mod.NetnsPinner
    # The store the attach path allocates LOCAL addresses from. Read on recovery to find the
    # address a pre-restart attach assigned, which is the address its published ports DNAT to.
    _ipam: HostLocalIpam
    # The node-local pool both backends carve their LOCAL block out of. The privnet is its single
    # owner (it owns every privileged network op), so it is also the one that can answer which
    # block a session holds — the LOCAL_SUBNET query the agent uses to resolve single-node peers.
    _local_subnets: LocalSubnetAllocator
    #: Node-wide VNI -> (session, configuration) bindings, so one agent's declaration cannot name
    #: the VNI another agent's live session is running on -- see `vni_registry`.
    _vni_registry: VniRegistry
    #: Keeps retrying the fail-close for tunnels the recovery preflight left UP.
    _fail_close_tasks: dict[int, asyncio.Task[None]]
    #: Why the last recovery could not even read its inputs, or None.
    _recovery_failed: str | None
    #: Sessions this process holds state for but could not re-adopt, and why.
    _unrecovered_sessions: dict[str, str]
    #: Containers that died while we were down and whose host-side state we could not give back.
    _unreclaimed_containers: dict[str, str]
    #: Dead sessions whose devices and subnet block we could not give back, and why.
    _unreclaimed_sessions: dict[str, str]
    #: Retries recovery while any of the four above is non-empty.
    _recovery_retry_task: asyncio.Task[None] | None
    #: Held by every request and by the whole of a recovery retry, so the two cannot interleave.
    #: The retry reads a snapshot of the journal and the runtime and then acts on it -- pruning
    #: node-wide claims, reclaiming dead sessions -- and a SETUP that lands in between makes the
    #: snapshot a lie about the very session whose claim the prune then deletes.
    #:
    #: Always taken BEFORE any per-session lock, on both paths, so the order is one way only.
    _mutation_lock: asyncio.Lock

    def __init__(
        self,
        *,
        socket_path: str,
        allowed_uid: int,
        agent_id: str,
        host_ip: str,
        runtime: ContainerLocator,
        cni_runner: CniRunner,
        backends: dict[str, AbstractNetworkAgentPluginV2[Any]],
        vtep_ip: str | None = None,
        forwarder: PortForwarder | None = None,
        journal: PrivNetJournal | None = None,
        ipam: HostLocalIpam | None = None,
        local_subnets: LocalSubnetAllocator | None = None,
        vni_registry: VniRegistry | None = None,
        netns_owner_uid: int | None = None,
        netns_pinner: netns_mod.NetnsPinner | None = None,
    ) -> None:
        self._socket_path = socket_path
        self._allowed_uid = allowed_uid
        if not agent_id.strip():
            # It is the owner half of every node-wide claim this process makes. An empty one
            # writes claims no reader can attribute, and an unattributable claim on a VNI reads as
            # nobody -- after which the next setup deletes the devices behind it.
            raise PrivnetConfigurationInvalid("network privnet requires a non-empty agent id")
        self._agent_id = agent_id
        self._host_ip = host_ip
        # Validated by the entry point (__main__), like the agent validates its own before handing
        # it to the session network — the address is a deployment fact, not something to re-derive
        # per request. None means this node cannot anchor a tunnel: vxlan sessions are refused.
        self._vtep_ip = vtep_ip
        self._runtime = runtime
        self._attacher = CniAttacher(cni_runner)
        self._forwarder = forwarder or PortForwarder()
        self._backends = backends
        self._sessions = {}
        self._locks = {}
        self._lock_users = {}
        self._journal = journal or PrivNetJournal()
        self._ipam = ipam or get_host_local_ipam()
        self._local_subnets = local_subnets or get_local_subnet_allocator(owner=agent_id)
        self._vni_registry = vni_registry or VniRegistry()
        self._fail_close_tasks = {}
        self._recovery_failed = None
        self._unrecovered_sessions = {}
        self._unreclaimed_containers = {}
        self._unreclaimed_sessions = {}
        self._recovery_retry_task = None
        self._mutation_lock = asyncio.Lock()
        # Set only where the PID record is agent-written (the rootless backends); see _attach.
        self._netns_owner_uid = netns_owner_uid
        self._netns = netns_pinner or netns_mod.NetnsPinner()

    @contextlib.asynccontextmanager
    async def _session_locked(self, session_id: str) -> AsyncIterator[None]:
        """Hold this session's per-session lock across one operation.

        The lock is refcounted rather than popped on teardown, because its *identity* must stay
        stable for as long as anyone holds or waits on it. ``Lock.release()`` only schedules the
        first waiter -- the releasing task runs on to its next await -- so a teardown that dropped
        the lock from the dict right after releasing it would leave the woken waiter holding an
        orphan, while the next arrival minted a fresh lock and entered the critical section alongside
        it: the very concurrent op this lock exists to prevent (a SETUP racing a TEARDOWN of the same
        session would then build and delete the same-named bridge at once). Registering as a user
        before the first await and dropping the entry only when the last user leaves keeps one lock
        per in-flight session and still lets the dict shrink back to empty.
        """
        lock = self._locks.get(session_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[session_id] = lock
        self._lock_users[session_id] = self._lock_users.get(session_id, 0) + 1
        try:
            async with lock:
                yield
        finally:
            remaining = self._lock_users[session_id] - 1
            if remaining:
                self._lock_users[session_id] = remaining
            else:
                del self._lock_users[session_id]
                self._locks.pop(session_id, None)

    async def serve_forever(self) -> None:
        sock_path = Path(self._socket_path)
        await self._prepare_socket_path(sock_path)
        # Both under a deadline, and both before the socket exists -- which is the point: nothing
        # can race the rebuild, and nothing can reach this node while it is stuck opening a
        # runtime that will not answer. Stuck is fail-closed, but a node that never finishes
        # starting is a node that serves nothing, forever, with no way to say so.
        # Before the runtime, before anything that can block: a backend that has not completed
        # its fail-close preflight owes this node an answer about every tunnel that survived, and
        # the debt has to exist before the first await that could stop us reaching it. Recorded
        # after, a startup that timed out opening the runtime left an EMPTY unclosed set, a
        # fail-close retry that swept it and reported success, and a node that called itself
        # healthy over tunnels it had never looked at.
        for backend in self._backends.values():
            preflight_owed = getattr(backend, "owe_fail_close_preflight", None)
            if preflight_owed is not None:
                preflight_owed()
        try:
            async with asyncio.timeout(_RECOVERY_TIMEOUT_SEC):
                await self._runtime.open()
                await self.recover()
        except TimeoutError:
            log.error(
                "privnet startup recovery did not finish within {}s; serving with what it has and"
                " retrying the rest",
                _RECOVERY_TIMEOUT_SEC,
            )
            self._recovery_failed = (
                f"startup recovery did not finish within {_RECOVERY_TIMEOUT_SEC:.0f}s"
            )
            # The preflight may have been cut short. Every device it had not reached is recorded
            # as unclosed (see `prepare_recovery`), and this is what keeps trying to bring them
            # down -- the ordinary recovery retry does not re-run the preflight.
            for backend in self._backends.values():
                self._start_fail_close_retry(backend)
            self._start_recovery_retry()
        server = await asyncio.start_unix_server(self._handle_conn, path=self._socket_path)
        bound_socket = sock_path.lstat()
        self._restrict_socket(sock_path)
        log.info(
            "network privnet listening on {} (agent uid={})", self._socket_path, self._allowed_uid
        )
        log.info("running as uid={} with {}", os.getuid(), _self_effective_caps())
        self._warn_if_not_separated()
        try:
            async with server:
                await server.serve_forever()
        finally:
            await self._runtime.close()
            self._unlink_bound_socket(sock_path, bound_socket)

    async def _prepare_socket_path(self, sock_path: Path) -> None:
        """Refuse foreign paths and live daemons; remove only our own stale socket."""
        try:
            original = sock_path.lstat()
        except FileNotFoundError:
            return
        if not stat.S_ISSOCK(original.st_mode) or original.st_uid != os.geteuid():
            raise UnsafePrivnetSocket(
                f"refusing to replace {sock_path}: it is not a socket owned by uid {os.geteuid()}"
            )
        try:
            reader, writer = await asyncio.open_unix_connection(sock_path)
        except FileNotFoundError:
            return
        except ConnectionRefusedError:
            try:
                current = sock_path.lstat()
            except FileNotFoundError:
                return
            if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
                raise UnsafePrivnetSocket(
                    f"refusing to replace changed socket path {sock_path}"
                ) from None
            sock_path.unlink()
            return
        except OSError as e:
            raise UnsafePrivnetSocket(f"cannot verify existing socket {sock_path}: {e}") from e
        del reader
        writer.close()
        await writer.wait_closed()
        raise PrivnetAlreadyRunning(f"another privnet is listening on {sock_path}")

    def _unlink_bound_socket(self, sock_path: Path, bound_socket: os.stat_result) -> None:
        """Remove the socket on shutdown only if it is still the one this process bound."""
        try:
            current = sock_path.lstat()
        except FileNotFoundError:
            return
        if (current.st_dev, current.st_ino) == (bound_socket.st_dev, bound_socket.st_ino):
            sock_path.unlink()

    def _restrict_socket(self, sock_path: Path) -> None:
        """Make the socket reachable by the agent and nobody else.

        0600 is right only while the two processes share a uid. Under real privilege separation
        this daemon owns the socket and the agent is a different user, so the connect needs group
        access -- granted to the agent's primary group and to no one else. `_peer_uid` still gates
        every connection; this only decides who may knock.
        """
        if self._allowed_uid == os.geteuid():
            sock_path.chmod(0o600)
            return
        try:
            gid = pwd.getpwuid(self._allowed_uid).pw_gid
        except KeyError:
            # No passwd entry to take a group from. Owner-only is not usable by the agent, so say
            # so plainly rather than leave a socket nothing can reach.
            raise PrivNetError(
                f"cannot grant the agent (uid {self._allowed_uid}) access to {sock_path}: it has"
                " no passwd entry, so its group cannot be resolved. Set BACKENDAI_PRIVNET_UID to"
                " the agent's uid, or run both as the same user."
            ) from None
        try:
            os.chown(sock_path, -1, gid)
        except PermissionError as e:
            # `chown` to a group this process is not a member of needs CAP_CHOWN. Say which of the
            # two is missing rather than leave a socket the agent cannot open.
            raise PrivNetError(
                f"cannot hand {sock_path} to the agent (uid {self._allowed_uid}, gid {gid}): {e}."
                " Add that group to this service's SupplementaryGroups, or give it CAP_CHOWN."
            ) from e
        sock_path.chmod(0o660)

    def _warn_if_not_separated(self) -> None:
        """Say out loud when the containment this daemon exists for is not actually in place.

        Running as the agent's own uid is a supported deployment and the common one, but it is not
        privilege separation: the agent can then unlink this process's journal, its claim files and
        its socket, and everything below is a defence in depth rather than a boundary. That is a
        deployment fact nothing in the code can fix, so it is stated once, here, where an operator
        reading the startup log will see it.
        """
        if self._allowed_uid != os.geteuid():
            return
        log.warning(
            "network privnet is running as the agent's own uid ({}): the agent can modify this"
            " process's journal and claims, so this is defence in depth, not containment. For a"
            " real boundary run the privnet as its own user with the agent's uid in"
            " BACKENDAI_PRIVNET_UID, and give that user sole ownership of {} and the node-wide"
            " claim directories.",
            self._allowed_uid,
            self._journal_root(),
        )

    def _journal_root(self) -> str:
        return str(getattr(self._journal, "_dir", "the privnet state directory"))

    async def _retry_recovery(self) -> None:
        """Re-attempt only what recovery could not do -- never the whole of it.

        Under `_mutation_lock` from the first read to the last write. What follows acts on a
        snapshot of the journal and the runtime: a SETUP that completes in the middle of it is
        absent from that snapshot, and the node-wide prune below then deletes the VNI claim of a
        session that was built moments ago -- leaving it running with no ownership on this host.

        `recover()` begins by bringing down every tunnel on this node and pruning every claim,
        which is correct exactly once, before anything is trusted. On a timer it is destructive:
        one session that keeps failing would take every healthy VXLAN down and up again every
        thirty seconds. So this re-reads the journal and re-adopts only what still needs it --
        under the same per-session lock the RPC verbs take, so a session being SET UP right now is
        not mistaken for a dead one.

        "What still needs it" is every live session when the first pass could not read its inputs
        at all, and the sessions that failed individually otherwise.
        """
        try:
            async with asyncio.timeout(_RECOVERY_TIMEOUT_SEC):
                async with self._mutation_lock:
                    await self._retry_recovery_locked()
        except TimeoutError:
            # It holds the barrier for its whole run, so a pass that will not finish is a node
            # that serves nothing. What it did not get to is still on the books -- that is what
            # the markers are for -- and the timer brings it back.
            log.error(
                "the privnet recovery pass exceeded {}s; releasing the node-wide lock and leaving"
                " the rest for the next attempt",
                _RECOVERY_TIMEOUT_SEC,
            )
            self._recovery_failed = (
                f"a recovery pass did not finish within {_RECOVERY_TIMEOUT_SEC:.0f}s"
            )

    async def _retry_recovery_locked(self) -> None:
        try:
            live, owned = await self._live_and_owned()
            journalled_sessions = await self._journal.sessions()
            journalled_attachments = await self._journal.attachments()
            journalled_peers = await self._journal.peers()
        except Exception as e:
            self._recovery_failed = str(e)
            return
        # A first pass that could not read its inputs adopted NOTHING, so there is no per-session
        # mark to work from and every live session still needs adopting -- the tunnels are all
        # down and the registry is empty, which is safe but is not a recovery. Iterating the empty
        # mark set would have cleared the failure flag and left the node exactly there.
        never_adopted = self._recovery_failed is not None
        self._recovery_failed = None
        # Recomputed every pass, and BEFORE the rebind: a session running here that this privnet
        # has no record of is not something a later pass may forget, and its VNI must not be
        # pruned on the strength of a journal that does not mention it.
        orphans = self._orphaned_live_sessions(owned, journalled_sessions)
        unbound = await self._rebind_journalled(journalled_sessions, prune=not orphans)
        # Gone from the journal since the failure: another verb finished the job, and holding the
        # marker would keep this timer running for something that no longer exists.
        for container_id in list(self._unreclaimed_containers):
            if container_id not in journalled_attachments:
                self._unreclaimed_containers.pop(container_id, None)
        for session_id in list(self._unreclaimed_sessions):
            if session_id not in journalled_sessions:
                self._unreclaimed_sessions.pop(session_id, None)
        # Dead containers first, for the reason the first pass does them first: the DEL needs the
        # session's plan, and reclaiming the session releases it. A pass that never adopted
        # anything never reached this either, so everything dead is still owed its reclaim.
        for container_id, record in journalled_attachments.items():
            if container_id in live:
                self._unreclaimed_containers.pop(container_id, None)
                continue
            if not never_adopted and container_id not in self._unreclaimed_containers:
                continue
            await self._reclaim_dead_container(container_id, record, journalled_sessions)
        pending = (
            {session_id for session_id in journalled_sessions if session_id in set(owned.values())}
            if never_adopted
            else set(self._unrecovered_sessions)
        )
        for session_id in sorted(pending):
            if session_id in orphans:
                continue  # not journalled and not gone: still running here, still unmanageable
            if session_id not in journalled_sessions:
                # Gone while we were failing to adopt it: there is nothing left to recover, and
                # keeping the mark would hold this node out of service for a session that ended.
                self._unrecovered_sessions.pop(session_id, None)
                continue
            if (reason := unbound.get(session_id)) is not None:
                self._unrecovered_sessions[session_id] = reason
                continue
            async with self._session_locked(session_id):
                try:
                    await self._readopt_session(
                        session_id,
                        journalled_sessions[session_id],
                        journalled_peers.get(session_id),
                        owned,
                        journalled_attachments,
                    )
                    self._sessions[session_id].built = True
                except Exception as e:
                    self._unrecovered_sessions[session_id] = str(e)
                    continue
                try:
                    # Adoption holds an encrypted tunnel DOWN; this is what raises it again once
                    # its complete peer set is back. Without it the retry left every recovered
                    # session dark -- adopted, protected, and carrying nothing.
                    await self._restore_live_security(session_id, journalled_peers.get(session_id))
                except Exception as e:
                    self._unrecovered_sessions[session_id] = str(e)
                    continue
                # BOTH markers. A session that came back is recorded as an unreclaimed dead one
                # too, and the sweep below skips it for being in `_sessions` -- so that marker
                # outlived the thing it described and kept the node reporting itself unrecovered
                # over a session it had fully taken back.
                self._now_managed(session_id)
                log.info("privnet recovered session {} on a later attempt", session_id)
        self._unrecovered_sessions.update(orphans)
        if self._unrecovered_sessions:
            return  # the dead-state sweep below needs a complete picture of what is live
        # Only once every live session is adopted: a dead session's devices are named after its
        # VNI, and reclaiming one whose VNI a live session now holds deletes the LIVE session's
        # devices. Deferred out of the first pass because it never ran there either -- the failure
        # that brought us here happened before it.
        live_vnis = {
            vni
            for session_id in journalled_sessions
            if session_id in self._sessions
            and (vni := self._journalled_vni(journalled_sessions.get(session_id))) is not None
        }
        for session_id, raw_config in journalled_sessions.items():
            if session_id in self._sessions:
                continue
            if (reason := unbound.get(session_id)) is not None:
                self._unreclaimed_sessions[session_id] = reason
                continue
            if (vni := self._journalled_vni(raw_config)) is not None and vni in live_vnis:
                self._unreclaimed_sessions[session_id] = f"VNI {vni} is held by a live session"
                continue
            # Under the session's own lock, and re-checked inside it: everything above was decided
            # from a snapshot, and this is the step that deletes devices.
            async with self._session_locked(session_id):
                if session_id in self._sessions:
                    continue  # adopted since the snapshot; not dead after all
                if session_id not in await self._journal.sessions():
                    self._unreclaimed_sessions.pop(session_id, None)
                    continue  # somebody finished it while we were deciding
                try:
                    await self._reclaim_dead_session(
                        session_id, raw_config, journalled_peers.get(session_id)
                    )
                except _ReclaimDeferred as e:
                    self._unreclaimed_sessions[session_id] = str(e)
                    if session_id in set((await self._live_and_owned())[1].values()):
                        # Alive again. It is not a dead session at all, so the next pass must
                        # ADOPT it rather than keep asking whether it may be deleted.
                        self._unrecovered_sessions[session_id] = str(e)
                except Exception as e:
                    log.exception(
                        "failed to reclaim dead session {} on a later attempt", session_id
                    )
                    self._unreclaimed_sessions[session_id] = str(e)
                else:
                    self._unreclaimed_sessions.pop(session_id, None)

    async def _probe_encryption(self) -> dict[str, str]:
        """What would stop this node holding up its end of an ESP tunnel, found out by trying.

        Answered here because it needs CAP_NET_ADMIN: the agent asking holds none, so its own
        attempt could only read /proc and guess.
        """
        backend = self._backends.get(str(NetworkBackendKind.VXLAN))
        probe = getattr(backend, "probe_encryption_support", None)
        if probe is None:
            return {}  # a backend with no encryption to probe
        try:
            return {f"privnet:encryption:{n}": why for n, why in enumerate(await probe())}
        except Exception as e:
            log.exception("the overlay encryption probe failed")
            return {"privnet:encryption": f"this node's encryption probe did not complete ({e})"}

    def recovery_problems(self) -> dict[str, str]:
        """Everything this privnet knows it has not been able to take charge of, and why.

        Read by the agent's readiness probe. Without it a node whose privnet cannot manage a live
        session -- one it has no journal record of, one whose VNI belongs to something else --
        looks healthy from every other angle, and the manager goes on scheduling onto it.
        """
        problems: dict[str, str] = {}
        if self._recovery_failed is not None:
            problems["privnet:recovery"] = self._recovery_failed
        for session_id, reason in self._unrecovered_sessions.items():
            problems[f"privnet:session:{session_id}"] = reason
        for session_id, reason in self._unreclaimed_sessions.items():
            problems[f"privnet:dead-session:{session_id}"] = reason
        for container_id, reason in self._unreclaimed_containers.items():
            problems[f"privnet:dead-container:{container_id}"] = reason
        for name, backend in self._backends.items():
            unclosed = getattr(backend, "unclosed_devices", None)
            if unclosed is None:
                continue
            for device in sorted(unclosed()):
                # A tunnel the recovery preflight could not bring down. Until it is down, what it
                # carries is unknown -- and every new session on this backend is refused by
                # `_require_closed` anyway, so a node advertising itself ready over one is
                # advertising a lie.
                problems[f"privnet:unclosed:{device}"] = (
                    f"the {name} backend could not bring down a tunnel that survived a previous"
                    " life on this node"
                )
            # Devices are not all a failed setup can leave: firewall rules it could not remove
            # stay behind the VNI, and the next session given that VNI runs into them.
            debt = getattr(backend, "cleanup_debt", None)
            if debt is not None:
                problems.update({f"privnet:{what}": why for what, why in debt().items()})
        return problems

    def _recovery_pending(self) -> bool:
        """Whether anything recovery owes this node is still outstanding.

        Reclaiming is part of that debt, not a best-effort extra: the host veth, the LOCAL address,
        the DNAT rules and the node-local subnet block of a dead container or session are given back
        by this pass and by nothing else.
        """
        return bool(
            self._recovery_failed is not None
            or self._unrecovered_sessions
            or self._unreclaimed_containers
            or self._unreclaimed_sessions
        )

    def _start_recovery_retry(self) -> None:
        """Keep retrying whatever recovery could not do, on a timer.

        The privnet stays up through a failed recovery on purpose -- refusing every verb for every
        session would be worse -- but "stays up" is not "recovers". A transient container-runtime
        or journal error otherwise leaves this node's sessions unmanaged, their tunnels closed and
        their teardowns undone, until somebody restarts the process.
        """
        if self._recovery_retry_task is not None and not self._recovery_retry_task.done():
            return

        async def _loop() -> None:
            while True:
                await asyncio.sleep(_RECOVERY_RETRY_INTERVAL)
                if not self._recovery_pending():
                    return
                try:
                    await self._retry_recovery()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("retrying privnet recovery failed")

        self._recovery_retry_task = asyncio.create_task(_loop())

    def _start_fail_close_retry(self, backend: AbstractNetworkAgentPluginV2[Any]) -> None:
        """Keep trying to bring down what the recovery preflight could not.

        The preflight failing does not stop this process -- that is deliberate, so live sessions
        can retry their own transitions -- but it leaves a tunnel UP that nothing owns. Retrying
        only when a new session asks for setup means a node whose sessions have all ended never
        retries at all.
        """
        retry = getattr(backend, "retry_fail_close", None)
        if retry is None:
            return  # a backend with no surviving-device concept
        identity = id(backend)
        if (existing := self._fail_close_tasks.get(identity)) is not None and not existing.done():
            return

        async def _loop() -> None:
            while True:
                await asyncio.sleep(_FAIL_CLOSE_RETRY_INTERVAL)
                try:
                    if not await retry():
                        return  # everything is down; nothing left to come back for
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("retrying the fail-close of surviving tunnels failed")

        self._fail_close_tasks[identity] = asyncio.create_task(_loop())

    async def recover(self) -> None:
        """Rebuild the session registry after a privnet restart, and give back what died while we
        were down.

        The registry is memory; the devices are not. A restarted privnet that skipped this would
        hold a node whose bridges, vxlan devices and DNAT rules are all up and carrying traffic,
        while refusing every verb about them — a new kernel could not join a running session, and a
        teardown would report success while leaking the session's devices *and* its node-local
        subnet block, which the pool never gets back.

        Ground truth is this privnet's own journal (what it set up and attached) reconciled against
        containerd (what is actually still running). The agent is not consulted: it is the process
        this separation exists to contain, and a session's subnet is exactly the thing it must not
        be able to re-declare.
        """
        # Host links survive this process but the registry and the ability to classify them do not.
        # Fail-close first, before trusting that a journal exists or is parseable. A successfully
        # readopted session is reopened by its backend; an orphan stays down and cannot carry
        # clear-text traffic indefinitely behind an empty registry.
        prepared: set[int] = set()
        for backend in self._backends.values():
            identity = id(backend)
            if identity in prepared:
                continue
            prepared.add(identity)
            try:
                # Before recovery, so the protection chains exist from the moment this process
                # does. Created lazily by the first session instead, they show up as state that
                # appeared from nowhere -- which is what a leak looks like, and they are not one:
                # their lifetime is this process's (see `_remove_owned_chains`).
                #
                # In its own guard: this is preparation, and the fail-close preflight below is the
                # step that must not be skipped. Letting a failed setup carry it away would leave
                # every surviving tunnel UP for the reason the chains could not be built.
                await backend.init()
            except Exception:
                log.exception(
                    "network backend startup setup failed; continuing to the recovery preflight"
                )
            try:
                await backend.prepare_recovery()
                self._start_fail_close_retry(backend)
            except Exception:
                # A backend preflight attempts every owned device before it raises. Keep the
                # privileged service available so the journal can classify those devices, live
                # sessions can retry their own fail-close transition, and unrelated backends stay
                # manageable instead of entering the same process crash loop.
                log.exception(
                    "network backend recovery preflight failed; continuing in degraded mode"
                )
                # Degraded mode is the reason this exists. Without a timer, a tunnel that could
                # not be brought down stays UP for as long as this process runs unless a new
                # session happens to ask for setup -- and on a node whose sessions all ended,
                # nothing ever asks.
                self._start_fail_close_retry(backend)
        try:
            live, owned = await self._live_and_owned()
            journalled_sessions = await self._journal.sessions()
            journalled_attachments = await self._journal.attachments()
            journalled_peers = await self._journal.peers()
        except Exception as e:
            log.exception(
                "could not read the privnet journal; leaving surviving tunnels down and starting "
                "with an empty registry"
            )
            # Distinct from an empty journal, which is a complete answer: this is "the answer
            # could not be read", and the flag is what brings the retry back.
            # Left down is safe, but permanently down is not a recovery. Without this the whole
            # node's sessions stay unmanaged until the process restarts, however transient the
            # runtime or journal error was.
            self._recovery_failed = str(e)
            self._start_recovery_retry()
            return
        # Read successfully, so whatever failed last time is no longer failing. Clearing it here
        # rather than after the loop below matters for the empty case: an empty journal is a
        # complete answer, and returning with the flag still set would keep this node reporting
        # itself unrecovered for as long as it runs.
        self._recovery_failed = None
        # Before the rebind, because its prune's premise is that the journal is the whole list of
        # what this agent owns -- and an orphan is exactly a counterexample.
        orphans = self._orphaned_live_sessions(owned, journalled_sessions)
        self._unrecovered_sessions = dict(orphans)
        unbound = await self._rebind_journalled(journalled_sessions, prune=not orphans)
        if not journalled_sessions and not journalled_attachments:
            self._unreclaimed_containers.clear()
            self._unreclaimed_sessions.clear()
            # An orphan is the one thing an empty journal can still owe: a container running here
            # that no record accounts for. Returning without the timer left that mark with nothing
            # to ever clear it, so the node stayed out of service after the container was gone.
            if self._recovery_pending():
                self._start_recovery_retry()
            return

        # Ours to adopt: journalled here AND running under a container this agent owns. A
        # co-located agent's container of the same session is not a reason for us to take it back.
        live_sessions = {
            session_id for session_id in journalled_sessions if session_id in set(owned.values())
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
                self._unreclaimed_containers.pop(container_id, None)
                continue
            await self._reclaim_dead_container(container_id, record, journalled_sessions)

        # Adopt every live session before reasserting or reclaiming anything. VXLAN adoption holds
        # encrypted tunnels down, and its XFRM policy/SA are shared by sessions on the same node
        # pair. This phase therefore closes every affected data path and rebuilds every surviving
        # owner refcount before a later command can update or delete the shared pair.
        for session_id in sorted(live_sessions):
            if (reason := unbound.get(session_id)) is not None:
                # Not ours to adopt. Recorded so the node reports itself unrecovered and the timer
                # comes back to it: the conflict may be a stale binding that a later pass clears.
                self._unrecovered_sessions[session_id] = reason
                continue
            try:
                await self._readopt_session(
                    session_id,
                    journalled_sessions[session_id],
                    journalled_peers.get(session_id),
                    owned,
                    journalled_attachments,
                )
                # `_rebind_journalled` already re-bound this VNI and recorded it as built (or it
                # has none), which is what `built` claims -- see `_SessionEntry`.
                self._sessions[session_id].built = True
            except Exception as e:
                # One unrecoverable session must not cost us the others: a privnet that gave up here
                # would refuse every verb for every session on the node. Recorded rather than only
                # logged, because a session left out of the registry is one whose tunnel stays
                # closed and whose teardown never runs -- and nothing else comes back to it.
                log.exception("failed to recover session {}", session_id)
                self._unrecovered_sessions[session_id] = str(e)
            else:
                self._unrecovered_sessions.pop(session_id, None)

        # Only after all live encrypted tunnels are down and their ownership is known may each
        # complete peer set be re-asserted and its tunnel reopened.
        for session_id in sorted(live_sessions):
            if session_id not in self._sessions:
                continue
            try:
                await self._restore_live_security(session_id, journalled_peers.get(session_id))
            except Exception as e:
                # Adoption holds an encrypted tunnel DOWN, and this is what raises it again. Only
                # logged, the session stayed dark for the life of the process: the node reported
                # itself recovered, the retry timer never started, and nothing else asks.
                log.exception("failed to restore security for session {}", session_id)
                self._unrecovered_sessions[session_id] = f"its protection was not restored ({e})"

        # Dead teardown is last: its shared-pair refcount now sees every surviving user.
        # A dead session's devices are named after its VNI, and the manager hands VNIs back out.
        # Reclaiming one whose VNI a live session now holds deletes the LIVE session's devices --
        # measured on three nodes: a terminated session and a running one both held VNI 4138, and
        # reclaiming the dead one left the running session RUNNING with its kernels up, its vxlan
        # device gone and no cross-node traffic. Leave those in the journal instead: the next
        # recovery reclaims them once the live session has ended, so nothing is lost by waiting.
        live_vnis = {
            vni
            for session_id in live_sessions
            if (vni := self._journalled_vni(journalled_sessions.get(session_id))) is not None
        }
        for session_id, raw_config in journalled_sessions.items():
            if session_id in live_sessions:
                continue
            if (reason := unbound.get(session_id)) is not None:
                # Its VNI is somebody else's now, and reclaiming deletes devices by that name.
                self._unreclaimed_sessions[session_id] = reason
                continue
            if (vni := self._journalled_vni(raw_config)) is not None and vni in live_vnis:
                log.warning(
                    "not reclaiming dead session {}: VNI {} now belongs to a live session on this "
                    "node, and its devices are named after it; deferring to a later recovery",
                    session_id,
                    vni,
                )
                # A marker, because "later" has to arrive: the retry timer is what brings this
                # session back once the live one has ended, and without it its devices and subnet
                # block wait for the next restart of this process.
                self._unreclaimed_sessions[session_id] = f"VNI {vni} is held by a live session"
                continue
            try:
                await self._reclaim_dead_session(
                    session_id, raw_config, journalled_peers.get(session_id)
                )
            except _ReclaimDeferred as e:
                # Not a failure and not a success: the runtime says otherwise now, so this stays
                # on the books for the retry, which reads a fresh snapshot.
                self._unreclaimed_sessions[session_id] = str(e)
            except Exception as e:
                log.exception("failed to recover session {}", session_id)
                self._unreclaimed_sessions[session_id] = str(e)
            else:
                self._unreclaimed_sessions.pop(session_id, None)
        if self._recovery_pending():
            self._start_recovery_retry()

    async def _rebind_journalled(
        self, journalled_sessions: dict[str, dict[str, Any]], *, prune: bool = True
    ) -> dict[str, str]:
        """Re-establish this agent's VNI bindings from its journal, and drop the rest.

        Bindings outlive the process that made them -- that is the point -- but a crash between
        binding a VNI and tearing it down leaves one with nobody behind it, and the VNI it names
        is then refused to every later session on this node. Only this agent's own bindings are
        touched; a co-located agent's are its to settle.

        Returns the journalled sessions whose VNI this node could NOT bind, and why. They must be
        left alone entirely: the VNI belongs to something else now, and both the paths recovery
        would take next -- adopting (which holds a VXLAN of that name down) and reclaiming (which
        deletes it) -- act on the device by its name, which is the other session's device.
        """
        live: list[tuple[str, str]] = []
        unbound: dict[str, str] = {}
        for session_id, raw_config in journalled_sessions.items():
            try:
                vni = policy.validate_network_config(raw_config).vni
            except Exception:
                continue
            if vni is None:
                continue
            digest = config_digest(raw_config)
            live.append((session_id, digest))
            try:
                async with self._vni_registry.binding(
                    vni, self._agent_id, session_id, digest
                ) as bound:
                    if not bound.recorded:
                        unbound[session_id] = (
                            f"this node's binding on VNI {vni} could not be recorded"
                        )
                    elif bound.already_held:
                        # Its devices are known to exist, which is what recovery is about to
                        # adopt. Nothing to change.
                        pass
                    elif not bound.mark_built():
                        # Bound but not marked built, and it would not take the mark: the next
                        # setup of this session would read "not built" and rebuild the very
                        # devices this recovery is about to adopt.
                        unbound[session_id] = (
                            f"this node's binding on VNI {vni} could not be marked built"
                        )
            except VniConflict as e:
                # Someone else has this VNI now. Adopting anyway would take THEIR data plane down:
                # an encrypted adopt holds the VXLAN of that name down, and a reclaim deletes it.
                unbound[session_id] = str(e)
        for session_id, reason in unbound.items():
            log.warning("journalled session {} cannot re-bind its VNI: {}", session_id, reason)
        if not prune:
            # A session is running on this node that the journal does not mention, so the journal
            # is not the whole list of what this agent owns -- and the prune's whole premise is
            # that it is. Dropping a claim on that basis takes a live session's ownership away.
            log.warning(
                "not pruning this agent's VNI bindings: a session is running here that this"
                " privnet has no record of, so the journal cannot be trusted as the full list"
            )
            return unbound
        try:
            dropped = await self._vni_registry.prune(self._agent_id, live)
        except Exception:
            log.exception("could not prune this agent's stale VNI bindings")
            return unbound
        if dropped:
            log.info("dropped {} stale VNI binding(s) of this agent", dropped)
        return unbound

    def _now_managed(self, session_id: str) -> None:
        """This privnet is on top of the session again, so drop whatever it was reported for.

        A session running here with no record of it is reported until there IS a record: the
        report is what stops the manager scheduling onto a node that cannot manage what it holds.
        Setting it up or adopting it is the thing that ends that, and nothing else does.
        """
        self._unrecovered_sessions.pop(session_id, None)
        self._unreclaimed_sessions.pop(session_id, None)

    def _orphaned_live_sessions(
        self, live: dict[str, str], journalled_sessions: dict[str, dict[str, Any]]
    ) -> dict[str, str]:
        """Sessions with a container running here that this privnet has no record of.

        Neither adoptable (the record is what says what the session IS) nor reclaimable (nothing
        here names its devices), so the only honest thing is to keep saying so. A node reporting
        itself recovered over a session it cannot manage is how that session's VNI is handed out
        again underneath it.
        """
        return dict.fromkeys(
            sorted(set(live.values()) - set(journalled_sessions)),
            "a container of this session is running on this node, but this privnet has no journal record of it",
        )

    async def _live_and_owned(self) -> tuple[dict[str, str], dict[str, str]]:
        """``(every kernel container on this NODE, the subset this agent owns)``, from ONE listing.

        The two scopes answer different questions -- "would deleting this take something that is
        running?" and "is this mine to adopt?" -- and taking them from two listings makes them
        disagree about the same container. Measured shape: a container that ends between the two
        reads is present in the first and absent from the second, so its attachment is skipped as
        live while its session is classified as dead, and the session's devices go while its
        attachment record and the address it leases stay behind with nothing naming them.

        A container whose owner the runtime cannot name is nobody's: not adopted here, and still
        counted in the first scope, which is what stops anything deleting it.
        """
        live: dict[str, str] = {}
        owned: dict[str, str] = {}
        for container_id, container in (await self._runtime.live_sessions()).items():
            live[container_id] = container.session_id
            if container.owner_agent_id == self._agent_id:
                owned[container_id] = container.session_id
        return live, owned

    async def _live_containers(self) -> dict[str, str]:
        """``{container_id: session_id}`` for every kernel container on this NODE."""
        return (await self._live_and_owned())[0]

    def _meta_of(self, session_id: str, raw_config: dict[str, Any]) -> SessionNetMeta:
        cfg = policy.validate_network_config(raw_config)
        return SessionNetMeta(
            session_id=session_id,
            subnet=cfg.subnet or "",
            backend=cfg.backend,
            mtu=cfg.mtu,
            vni=cfg.vni,
            vxlan_port=cfg.vxlan_port,
            encryption_key=cfg.encryption_key,
            encryption_key_id=cfg.encryption_key_id,
            generation=cfg.generation,
        )

    def _members_of(self, peer_vteps: Sequence[str]) -> list[Member]:
        return [
            Member(agent_id="", host_ip=vtep, vtep_ip=vtep)
            for vtep in (
                policy.validate_ipv4(raw_vtep, what="journalled vtep_ip") for raw_vtep in peer_vteps
            )
        ]

    async def _readopt_session(
        self,
        session_id: str,
        raw_config: dict[str, Any],
        peer_vteps: Sequence[str] | None,
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
        peers = self._members_of(peer_vteps or ())
        await backend.restore_session_peer_ownership(session_id, peers)
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

    async def _restore_live_security(
        self, session_id: str, peer_vteps: Sequence[str] | None
    ) -> None:
        entry = self._sessions[session_id]
        # VXLAN adoption holds an encrypted tunnel down. Only the full, durable peer set can
        # re-assert every outbound policy and safely reopen it; waiting for a later agent request
        # would leave surviving sessions dark after every privnet restart.
        if entry.meta.encryption_key is not None and peer_vteps is None:
            # Upgrade compatibility: older journals have no peer record. Empty and unknown are
            # different here -- reopening for an unknown set recreates the clear-text window this
            # recovery path exists to close. The agent's next full ENSURE_SECURITY supplies the
            # authoritative set and reopens the tunnel.
            log.warning(
                "keeping encrypted session {}'s tunnel down until the agent supplies its full "
                "peer set; this journal predates durable peer ownership",
                session_id,
            )
            return
        await entry.backend.ensure_session_security(session_id, self._members_of(peer_vteps or ()))

    def _journalled_vni(self, raw_config: dict[str, Any] | None) -> int | None:
        """The VNI a journalled session claims, or None when it has none or cannot be read.

        Deliberately tolerant: this only decides whether reclaiming a dead session could name a
        live one's devices, and an unreadable entry is handled by the reclaim path itself.
        """
        if not raw_config:
            return None
        try:
            vni = policy.validate_network_config(raw_config).vni
        except Exception:
            return None
        return vni

    async def _reclaim_dead_session(
        self, session_id: str, raw_config: dict[str, Any], peer_vteps: Sequence[str] | None
    ) -> None:
        """Tear down a session whose containers are all gone. Only this pass can: the agent
        already believes it torn down (or is itself gone), so nothing else will ever name these
        devices, and the node-local block they hold is finite."""
        meta = self._meta_of(session_id, raw_config)
        if meta.vni is None:
            liveness = await self._recheck(session_id, session=True)
            if liveness is _Liveness.FOREIGN:
                await self._withdraw_stale(session_id, meta, "")
                return
            if liveness is not _Liveness.GONE:
                raise _ReclaimDeferred(liveness.reason)
            await self._reclaim_devices(session_id, meta, peer_vteps)
            await self._journal.forget_session(session_id)
            log.info("reclaimed the network of dead session {}", session_id)
            return
        digest = config_digest(raw_config)
        liveness = await self._recheck(session_id, session=True)
        if liveness is _Liveness.FOREIGN:
            await self._withdraw_stale(session_id, meta, digest)
            return
        if liveness is not _Liveness.GONE:
            raise _ReclaimDeferred(liveness.reason)
        # Before the adopt, not after the teardown. Adoption holds an encrypted tunnel DOWN, so
        # even reaching that far for a session another agent is still running would take its
        # traffic with it -- and this pass runs precisely because this node's own runtime shows no
        # containers, which says nothing about the runtime a co-located agent uses.
        async with self._vni_registry.releasing(
            meta.vni, self._agent_id, session_id, digest
        ) as freed:
            if freed is None:
                raise PrivNetError(
                    f"cannot reclaim dead session {session_id}: this node could not determine"
                    f" whether another agent still holds VNI {meta.vni}"
                )
            if not freed:
                log.info(
                    "not reclaiming dead session {}: another agent on this node still holds VNI"
                    " {}; dropping only this agent's record of it",
                    session_id,
                    meta.vni,
                )
                await self._journal.forget_session(session_id)
                return
            await self._reclaim_devices(session_id, meta, peer_vteps)
        await self._journal.forget_session(session_id)
        log.info("reclaimed the network of dead session {}", session_id)

    async def _recheck(self, what: str, *, session: bool) -> _Liveness:
        """Ask the runtime again, right before deleting anything of ``what``.

        Three answers, because two are not enough. The node-wide barrier holds off other privnet
        requests; it holds off nothing in containerd, so a container can start between the
        snapshot this pass read and the moment it acts -- and treating "it is back" the same as
        "it is gone, carry on" left the caller clearing its retry marker over a live session it
        had not adopted. It stayed journalled, unadopted, its tunnel held down, and nothing came
        back to it.
        """
        try:
            live, owned = await self._live_and_owned()
        except Exception as e:
            log.warning("could not re-check the runtime before reclaiming {}: {}", what, e)
            return _Liveness.UNKNOWN
        present = set(live.values()) if session else set(live)
        if what not in present:
            return _Liveness.GONE
        ours = set(owned.values()) if session else set(owned)
        if what in ours:
            log.info("not reclaiming {}: it is running again", what)
            return _Liveness.OURS
        log.info("not reclaiming {}: another agent on this host is running it", what)
        return _Liveness.FOREIGN

    async def _withdraw_stale(self, session_id: str, meta: SessionNetMeta, digest: str) -> None:
        """Drop this agent's record of a session another agent on the host is running.

        Its devices are not ours to delete -- containers are on them -- and its session is not
        ours to adopt, because we do not run any of them. But the journal record, the VNI binding
        and the recovery debt ARE ours, and nothing else will ever drop them: deferring instead
        left this agent reporting itself unrecovered, with its timer running, for as long as the
        other agent's session lived.
        """
        if meta.vni is not None and digest:
            async with self._vni_registry.releasing(
                meta.vni, self._agent_id, session_id, digest
            ) as freed:
                if freed is not False:
                    # False is the only safe answer here. True means OUR claim is the last one on
                    # a VNI whose devices are carrying another agent's containers: dropping it
                    # leaves the registry saying the VNI is free, and the next session to draw it
                    # deletes `baivx<vni>` out from under them. None means we could not tell.
                    #
                    # Raising keeps the claim -- `releasing` drops it only when the block returns
                    # -- and leaves the session on the books, which is where an operator can see
                    # a co-located agent that is not claiming what it runs.
                    raise _ReclaimDeferred(
                        f"another agent runs session {session_id}, but this node's binding on VNI"
                        f" {meta.vni} is "
                        + ("the last one on it" if freed is True else "of an undetermined count")
                        + "; keeping it rather than leaving the VNI readable as free"
                    )
        await self._journal.forget_session(session_id)
        log.info(
            "withdrew this agent's ownership of session {}: another agent on this host runs it",
            session_id,
        )

    async def _reclaim_devices(
        self, session_id: str, meta: SessionNetMeta, peer_vteps: Sequence[str] | None
    ) -> None:
        backend = self._resolve_backend(meta.backend)
        # Real backends derive teardown from process-local metadata. Reconstruct both the session
        # and its journalled peer ownership first; calling teardown on a fresh backend is an
        # idempotent no-op and used to leak the VXLAN devices, filter rule and XFRM state.
        await backend.adopt_session_network(meta, self._self_member(meta.backend))
        await backend.restore_session_peer_ownership(session_id, self._members_of(peer_vteps or ()))
        if meta.encryption_key is not None and peer_vteps is None:
            log.warning(
                "dead encrypted session {} predates peer journalling; reclaiming its devices but "
                "leaving unidentifiable shared XFRM state in place",
                session_id,
            )
        await backend.teardown_session_network(session_id)

    async def _reclaim_dead_container(
        self,
        container_id: str,
        record: AttachRecord,
        journalled_sessions: dict[str, dict[str, Any]],
    ) -> None:
        """Give back the host veth, the LOCAL address and the DNAT rules of a container that died
        while we were down. The container's own netns took its end of the veth with it; the host
        side, its address and its rules are ours to release."""
        liveness = await self._recheck(container_id, session=False)
        if liveness is not _Liveness.GONE:
            # Back, or unaskable. Either way this is debt, not a completed reclaim: the caller
            # clears the marker on a clean return, and clearing it here is what stopped the retry.
            self._unreclaimed_containers[container_id] = liveness.reason
            return
        try:
            await self._forwarder.remove_container(container_id)
            raw_config = journalled_sessions.get(record.session_id)
            if raw_config is not None:
                meta = self._meta_of(record.session_id, raw_config)
                backend = self._resolve_backend(meta.backend)
                plan = await self._derive_plan(backend, meta, record.overlay_ip)
                await self._del_attachment(plan, container_id)
            await self._journal.forget_attachment(container_id)
        except Exception as e:
            # Marked, not just logged: the address stays allocated and the DNAT rules stay in the
            # table until this succeeds, and the container is gone -- nothing else will ever ask
            # for it again.
            log.exception("failed to reclaim the network of dead container {}", container_id)
            self._unreclaimed_containers[container_id] = str(e)
        else:
            self._unreclaimed_containers.pop(container_id, None)
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
        from. It is what its published ports DNAT to, so a restarted privnet must know it before it
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
        """This node's membership record — what every peer reads and programs into its FDB. Only the
        *validated* VTEP goes in: peers guard on `vtep_ip is None` alone, so "" or 0.0.0.0 would
        sail through into an FDB entry that fails or points nowhere."""
        return Member(
            agent_id=self._agent_id,
            host_ip=self._host_ip,
            vtep_ip=self._vtep_ip if backend is NetworkBackendKind.VXLAN else None,
        )

    def _require_vtep(self, backend: NetworkBackendKind) -> None:
        """A vxlan session must not be set up on a node that cannot be reached at its VTEP: the
        peers would program an unusable address and the session hangs at rendezvous with no error."""
        if backend is NetworkBackendKind.VXLAN and self._vtep_ip is None:
            raise UnusableVtep(
                f"network privnet on agent {self._agent_id} cannot join a multi-node overlay session:"
                f" its host address ({self._host_ip!r}) is not a routable unicast IPv4 held by an"
                " interface of this host that is up. Set BACKENDAI_PRIVNET_HOST_IP (and the"
                " agent's container.advertised-host) to the address peers reach this node on."
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
                writer.write(PrivNetResponse(ok=False, error="unauthorized").encode())
                await writer.drain()
                return
            line = await reader.readline()
            if not line:
                return
            resp = await self._dispatch(line)
            # Stamped here rather than at each `return`: it is a property of the daemon, not of
            # the verb, and a caller uses it to tell "does not know this verb" from "said no".
            writer.write(replace(resp, version=PROTOCOL_VERSION).encode())
            await writer.drain()
        except Exception:
            log.exception("privnet connection handler failed")
            try:
                writer.write(PrivNetResponse(ok=False, error="internal error").encode())
                await writer.drain()
            except Exception:
                pass
        finally:
            writer.close()

    async def _dispatch(self, line: bytes) -> PrivNetResponse:
        try:
            req = PrivNetRequest.decode(line)
            session_id = policy.validate_session_id(req.session_id)
        except (ProtocolError, policy.PolicyViolation) as e:
            return PrivNetResponse(ok=False, error=str(e))
        if req.op in _READ_ONLY_OPS:
            # No barrier: these change nothing, and a readiness probe must not queue behind a
            # recovery pass that is busy re-adopting a node's worth of sessions.
            async with self._session_locked(session_id):
                return await self._dispatch_locked(req, session_id)
        try:
            # The deadline covers WAITING for the barrier as well as holding it. Started after the
            # acquire, a request queued behind a long recovery pass had no deadline at all -- the
            # part of its life it is most likely to spend.
            async with asyncio.timeout(_REQUEST_TIMEOUT_SEC):
                # Global first, then per-session: the recovery retry takes them in that order too.
                async with self._mutation_lock, self._session_locked(session_id):
                    return await self._dispatch_locked(req, session_id)
        except TimeoutError:
            # A backstop, not the primary defence: every command and lock wait beneath this is
            # already bounded. What it guarantees is that the node-wide barrier is always given
            # back -- one request that found a new way to block would otherwise stop every attach,
            # teardown and peer update on this node for as long as it runs.
            log.error(
                "privnet op {} for session {} exceeded {}s; releasing the node-wide lock",
                req.op,
                session_id,
                _REQUEST_TIMEOUT_SEC,
            )
            return PrivNetResponse(
                ok=False,
                error=f"the operation did not finish within {_REQUEST_TIMEOUT_SEC:.0f}s",
            )

    async def _dispatch_locked(self, req: PrivNetRequest, session_id: str) -> PrivNetResponse:
        if (refusal := await self._wrong_incarnation(req, session_id)) is not None:
            return refusal
        try:
            match req.op:
                case PrivNetOp.SETUP_SESSION:
                    await self._setup(session_id, req.network_config or {})
                    return PrivNetResponse(ok=True)
                case PrivNetOp.ADOPT_SESSION:
                    await self._adopt(session_id, req.network_config or {})
                    return PrivNetResponse(ok=True)
                case PrivNetOp.TEARDOWN_SESSION:
                    await self._teardown(session_id)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.WITHDRAW_SESSION:
                    await self._withdraw(session_id)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.ATTACH_CONTAINER:
                    assigned = await self._attach(
                        session_id, req.container_id, req.ip, req.local_ip
                    )
                    return PrivNetResponse(ok=True, assigned=assigned)
                case PrivNetOp.DETACH_CONTAINER:
                    await self._detach(session_id, req.container_id)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.ADD_PEER | PrivNetOp.DEL_PEER:
                    await self._peer(session_id, req)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.ENSURE_SECURITY:
                    await self._ensure_security(session_id, req)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.ADD_ENDPOINT | PrivNetOp.DEL_ENDPOINT:
                    await self._endpoint(session_id, req)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.PUBLISH_PORTS:
                    await self._publish_ports(session_id, req)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.UNPUBLISH_PORTS:
                    return PrivNetResponse(ok=True, host_ports=await self._unpublish_ports(req))
                case PrivNetOp.LIST_PORTS:
                    return PrivNetResponse(ok=True, forwards=await self._list_ports())
                case PrivNetOp.CONFINE_CONTAINER:
                    await self._confine_container(req)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.RELEASE_CONTAINER:
                    await self._release_container(req)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.LOCAL_SUBNET:
                    return PrivNetResponse(ok=True, subnet=await self._local_subnet(session_id))
                case PrivNetOp.SETUP_DNS_REDIRECT:
                    await self._setup_dns_redirect(session_id, req.dns_port)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.TEARDOWN_DNS_REDIRECT:
                    await remove_dns_redirect(session_id)
                    return PrivNetResponse(ok=True)
                case PrivNetOp.RECOVERY_STATUS:
                    return PrivNetResponse(ok=True, problems=self.recovery_problems())
                case PrivNetOp.ENCRYPTION_PROBE:
                    return PrivNetResponse(ok=True, problems=await self._probe_encryption())
        except (policy.PolicyViolation, netns_mod.NetnsError, PrivNetError) as e:
            return PrivNetResponse(ok=False, error=str(e))
        except Exception:
            log.exception("privnet op {} failed for session {}", req.op, session_id)
            return PrivNetResponse(ok=False, error="operation failed")

    def _resolve_backend(self, backend: NetworkBackendKind) -> AbstractNetworkAgentPluginV2[Any]:
        try:
            return self._backends[str(backend)]
        except KeyError:
            raise PrivNetError("unsupported backend") from None

    async def _wrong_incarnation(
        self, req: PrivNetRequest, session_id: str
    ) -> PrivNetResponse | None:
        """Refuse a request issued for an incarnation of the session this node does not hold.

        The lock above orders requests for one session id; it cannot tell whose they are. A session
        id is reused, so a TEARDOWN_SESSION that was delayed across a teardown and a rebuild is, by
        session id alone, a perfectly valid instruction to delete the data plane that is now live
        -- and the same goes for DETACH_CONTAINER, DEL_PEER and the DNS redirect. The generation
        the agent stamps on each request is the only thing that tells them apart.

        Applied once, here, so a verb added later is fenced without being remembered.

        What is fenced is decided by what this node HOLDS, not by what the request carries. A
        session whose incarnation this node knows accepts requests for that incarnation and no
        other -- including a request naming none, which is what an agent from before the fence
        sends and what a caller that built its own client sends by mistake. Both are exactly the
        shape a stale request has, and neither can be told from one. A session this node holds no
        incarnation for is not fenced: that is a node-local session, one set up before the field,
        or a node-wide op using the session field as a lock key.
        """
        live = await self._live_generation(session_id)
        if live is None or live == req.generation:
            return None
        log.warning(
            "refusing {} for session {}: it names incarnation {}, and this node holds {}",
            req.op,
            session_id,
            req.generation or "none",
            live,
        )
        return PrivNetResponse(
            ok=False,
            error=(
                f"session {session_id} on this node is incarnation {live}, and this request was"
                f" issued for {req.generation or 'no incarnation'}; refusing rather than acting on"
                " the data plane of a session the request was not meant for"
            ),
        )

    async def _live_generation(self, session_id: str) -> str | None:
        """The incarnation of the session this node currently holds state for, if it names one.

        The live entry first, the journal second -- the same order and the same reason as
        `_binding_of`: after a restart the entry is gone and the record is all there is. None means
        this node holds nothing under the id, or holds it from before the field, and there is
        nothing to tell a request apart from.
        """
        entry = self._sessions.get(session_id)
        if entry is not None:
            return entry.meta.generation
        raw_config = await self._journalled_config(session_id)
        if raw_config is None:
            return None
        generation = raw_config.get("generation")
        return str(generation) if generation else None

    async def _setup(self, session_id: str, raw_config: dict[str, Any]) -> None:
        cfg = policy.validate_network_config(raw_config)
        self._require_vtep(cfg.backend)  # refuse before anything is journalled or built
        meta = self._meta_of(session_id, raw_config)
        backend = self._resolve_backend(cfg.backend)
        digest = config_digest(raw_config)
        if cfg.vni is None:
            # Nothing to bind: this backend's devices are not named after a VNI, so no declaration
            # can point at another session's, and there is no binding to record as built.
            await self._build(session_id, meta, backend, raw_config, digest)
            self._sessions[session_id].built = True
            return
        try:
            # The binding is held across the build, not taken and dropped before it: between
            # "this VNI is free" and the devices existing there is a window in which a co-located
            # agent decides the same thing, and the two then build over each other.
            async with self._vni_registry.binding(
                cfg.vni, self._agent_id, session_id, digest
            ) as bound:
                if not bound.recorded:
                    raise PrivNetError(
                        f"cannot set session {session_id} up: its VNI {cfg.vni} could not be bound"
                        " in the node-wide registry, so this node cannot tell whether another"
                        " session is already running on it"
                    )
                if bound.already_held:
                    # A co-located agent (or this one before a restart) already built this very
                    # session. Building again deletes its devices first, and they are carrying its
                    # containers -- so take it over instead. Decided under the binding's lock, so
                    # nothing can claim the VNI between the answer and acting on it.
                    await self._adopt_bound(session_id, raw_config, digest, bound)
                    return
                try:
                    await self._build(session_id, meta, backend, raw_config, digest)
                except Exception:
                    # No data plane came of it, so the reservation must not read as one: left
                    # behind, the next setup of this session adopts devices that do not exist.
                    bound.abandon()
                    raise
                if bound.mark_built():
                    self._sessions[session_id].built = True
                else:
                    # The devices exist and the store will not say so. Left there, a co-located
                    # agent's setup of this same session reads "not built", takes the build path,
                    # and deletes these devices out from under whatever is already on them. Give
                    # them back instead and let the agent retry the whole thing.
                    await self._teardown_data_plane(
                        session_id, self._sessions.get(session_id), raw_config
                    )
                    await self._journal.forget_session(session_id)
                    bound.abandon()
                    raise PrivNetError(
                        f"session {session_id} was built but its VNI {cfg.vni} could not be"
                        " recorded as built in the node-wide registry; the data plane has been"
                        " removed again rather than left for a co-located agent to rebuild"
                    )
        except VniConflict as e:
            # The declaration names a VNI this node has already given to something else. Setup
            # deletes `baivx<vni>` and its bridges before rebuilding them, so accepting this is
            # how one agent's request cuts another session's containers off the network.
            raise policy.PolicyViolation(str(e)) from None

    async def _build(
        self,
        session_id: str,
        meta: SessionNetMeta,
        backend: AbstractNetworkAgentPluginV2[Any],
        raw_config: dict[str, Any],
        digest: str,
    ) -> None:
        """Journal the session and build its data plane, with its VNI binding held."""
        # Journal before the host is mutated: a record with no device is reconciled away on the
        # next boot, while a device with no record is one nobody can ever name again.
        await self._journal.record_session(session_id, dict(raw_config))
        try:
            await backend.setup_session_network(meta, self._self_member(meta.backend))
        except BaseException:
            # A setup that failed may have left rules or a device its own undo could not remove.
            # The fail-close timer is what comes back for those, and it stops once there is
            # nothing left -- so a failure long after recovery has to start it again.
            self._start_fail_close_retry(backend)
            raise
        self._sessions[session_id] = _SessionEntry(meta, backend, digest)
        self._now_managed(session_id)

    def _binding_of(
        self, session_id: str, raw_config: dict[str, Any] | None
    ) -> tuple[int, str] | None:
        """The (VNI, configuration digest) this agent bound for the session, if it bound one.

        The live entry first, the journal second: after a restart the entry is gone and the record
        is all there is, and releasing under the wrong digest leaves the claim on disk.
        """
        entry = self._sessions.get(session_id)
        if entry is not None and entry.meta.vni is not None and entry.digest:
            return entry.meta.vni, entry.digest
        if raw_config is None:
            return None
        try:
            vni = policy.validate_network_config(raw_config).vni
        except Exception:
            return None
        return None if vni is None else (vni, config_digest(raw_config))

    async def _adopt(self, session_id: str, raw_config: dict[str, Any]) -> None:
        """Take a session whose data plane already exists on this host into this privnet.

        Never `_setup`. Setup deletes the session's overlay bridge, its VXLAN device and its LOCAL
        bridge before rebuilding them, which is correct for a fresh session and cuts every running
        container of one that is already up -- the surviving veths are not re-enslaved to the new
        bridge, so the kernels keep running with no network at all.

        Two callers, one meaning: an agent that restarted under its own live session, and a second
        agent on this host joining a session another agent's privnet built. Both are "this session
        exists; be responsible for it", and neither is "build it".
        """
        cfg = policy.validate_network_config(raw_config)
        self._require_vtep(cfg.backend)
        declared = self._meta_of(session_id, raw_config)
        if (entry := self._sessions.get(session_id)) is not None:
            # Already ours. Rebuilding the entry would drop the attachment plans it holds, which
            # are what every later detach is derived from, so re-declaring is a no-op -- but only
            # if it is the same session. A different declaration under a live name is the trust
            # boundary this process exists for, not an update.
            if entry.meta != declared:
                raise PrivNetError(
                    f"session {session_id} is already set up on this node with a different network"
                    " configuration; refusing to redeclare it"
                )
            if entry.built:
                return
            # The entry is here but the registry never recorded the VNI as built, so a co-located
            # privnet still reads it as a half-finished build it may rebuild over these devices.
            # Returning early on the entry alone is what made every retry of this ADOPT a no-op
            # and left the node in that state for good.
            log.warning(
                "re-running the adoption of session {}: its VNI is not recorded as built",
                session_id,
            )
        journalled = (await self._journal.sessions()).get(session_id)
        if journalled is not None and self._meta_of(session_id, journalled) != declared:
            raise PrivNetError(
                f"session {session_id} is journalled on this node with a different network"
                " configuration; refusing to adopt it under a new declaration"
            )
        digest = config_digest(raw_config)
        if cfg.vni is None:
            await self._adopt_bound(session_id, raw_config, digest)
            return
        try:
            async with self._vni_registry.binding(
                cfg.vni, self._agent_id, session_id, digest
            ) as bound:
                if not bound.recorded:
                    raise PrivNetError(
                        f"cannot adopt session {session_id}: its VNI {cfg.vni} could not be"
                        " bound in the node-wide registry"
                    )
                await self._adopt_bound(session_id, raw_config, digest, bound)
        except VniConflict as e:
            raise policy.PolicyViolation(str(e)) from None

    async def _adopt_bound(
        self,
        session_id: str,
        raw_config: dict[str, Any],
        digest: str,
        binding: Binding | None = None,
    ) -> None:
        """Take the session over, with its VNI binding already held."""
        await self._journal.record_session(session_id, dict(raw_config))
        # The same rebuild recovery does, so an adopting privnet regains the attachment plans and
        # LOCAL addresses of containers that are already running under this session.
        await self._readopt_session(
            session_id,
            dict(raw_config),
            (await self._journal.peers()).get(session_id),
            await self._live_containers(),
            await self._journal.attachments(),
        )
        if (entry := self._sessions.get(session_id)) is not None:
            entry.digest = digest
        if binding is None:
            # No VNI, so no binding to vouch for: nothing can name these devices by number.
            if (adopted := self._sessions.get(session_id)) is not None:
                adopted.built = True
            return
        if not binding.mark_built():
            # This agent now serves a data plane that exists, and the store will not say so. A
            # co-located agent would then read "not built" and rebuild these very devices. The
            # entry stays -- its attachment plans are real -- but marked unbuilt, so the next
            # ADOPT runs this again instead of returning early on the entry's mere presence.
            raise PrivNetError(
                f"session {session_id} was adopted but this node could not record its VNI as"
                " built in the node-wide registry"
            )
        if (adopted := self._sessions.get(session_id)) is not None:
            adopted.built = True
        self._now_managed(session_id)

    async def _withdraw(self, session_id: str) -> None:
        """Drop this node's ownership of a session whose devices must stay.

        The agent asking has no kernels of it left, but a co-located agent does -- so nothing on
        the host is removed. What goes is this process's belief that it is responsible: without
        that, its protection watchdog keeps reprogramming a session it no longer serves and its
        ESP pair claim outlives the last agent that had one.
        """
        entry = self._sessions.get(session_id)
        if entry is None:
            return
        binding = self._binding_of(session_id, None)
        if binding is None:
            await self._release_backend_ownership(entry, session_id)
            await self._forget_withdrawn(session_id)
            return
        vni, digest = binding
        async with self._vni_registry.releasing(vni, self._agent_id, session_id, digest) as freed:
            if freed is not False:
                # WITHDRAW means "a co-located agent still has kernels on these devices, so they
                # stay". False is the registry agreeing: somebody else holds the VNI. True says
                # OUR claim was the last one on a VNI whose devices are still up and carrying
                # somebody -- their agent's claim was lost or never made -- and dropping it leaves
                # the VNI readable as free, after which the next session to draw it deletes
                # `baivx<vni>` out from under them. None is not knowing.
                #
                # Raising keeps the claim: `releasing` commits only when this block returns.
                raise PrivNetError(
                    f"session {session_id} cannot be withdrawn: this node's binding on VNI {vni}"
                    + (
                        " is the last one on it, and its devices are staying up"
                        if freed is True
                        else " could not be accounted for"
                    )
                    + "; the session has not been let go"
                )
            # INSIDE. The backend gives up the ESP pair claims and the watchdog responsibility,
            # and it can legitimately refuse -- a pair whose last claim is ours, a journal it
            # cannot read, a lock it cannot take. Done after the block, its failure left the VNI
            # claim already committed while everything else stayed: the retry then found no
            # binding of its own, which `releasing` answers with None, and refused before ever
            # reaching the backend again. It never converged.
            #
            # Raising here keeps the VNI claim, so the retry starts from the same place it did.
            await self._release_backend_ownership(entry, session_id)
        # Outside, so it runs only once the VNI claim has actually gone: `releasing` commits when
        # the block RETURNS and raises when it could not. Dropping the journal record and the
        # session entry inside would leave that failure with nothing to retry from -- the next
        # attempt would find no entry, return success, and the stale claim would refuse this VNI
        # until the next restart.
        await self._forget_withdrawn(session_id)

    async def _release_backend_ownership(self, entry: _SessionEntry, session_id: str) -> None:
        """Give up the ESP pair claims and the watchdog's belief that this session is ours."""
        backend = self._backends.get(str(entry.meta.backend))
        if backend is not None:
            await backend.withdraw_session_network(session_id)

    async def _forget_withdrawn(self, session_id: str) -> None:
        """Drop this process's record of a session it has let go of.

        The journal too, or the next restart reads it back and re-adopts a session this node has
        given up -- taking its ESP pair claim and its watchdog responsibility with it.
        """
        await self._journal.forget_session(session_id)
        self._sessions.pop(session_id, None)

    async def _teardown(self, session_id: str) -> None:
        """Remove the session's data plane -- but only if this node is the last one on it.

        The devices are the HOST's, not this agent's. A co-located agent sharing the session keeps
        its kernels on the same bridge, and its containers do not appear in this privnet's own
        runtime inventory: each backend's locator sees its own runtime and nothing else. So
        "nobody I can see is using it" is not "nobody is using it", and the node-wide binding is
        the only thing that can tell the two apart.

        Decided and acted on under that binding's lock, in that order: releasing after the delete
        made the answer worthless, because the delete had already happened.
        """
        # The lock is NOT popped here: `_session_locked` owns its lifecycle (dropping it only when
        # the last holder/waiter leaves). Popping it mid-hold is exactly the race this call runs
        # under the lock to avoid.
        entry = self._sessions.get(session_id)
        raw_config = await self._journalled_config(session_id)
        binding = self._binding_of(session_id, raw_config)
        if binding is None:
            # No VNI to arbitrate on -- this backend's devices are not named after one, so no
            # other session can be behind them.
            await self._teardown_data_plane(session_id, entry, raw_config)
            await self._journal.forget_session(session_id)
            return
        vni, digest = binding
        withdraw_instead = False
        async with self._vni_registry.releasing(vni, self._agent_id, session_id, digest) as freed:
            if freed is None:
                raise PrivNetError(
                    f"session {session_id} cannot be torn down: this node could not determine"
                    f" whether another agent still holds VNI {vni}, and deleting its devices on a"
                    " guess would cut that agent's containers off the network"
                )
            if not freed:
                # Another agent on this host still has kernels on these devices. Everything this
                # agent owns goes; nothing on the host does -- so this is exactly a withdrawal,
                # and it happens outside, once the claim has actually gone.
                log.info(
                    "not tearing session {} down: another agent on this node still holds VNI {};"
                    " withdrawing this agent's ownership instead",
                    session_id,
                    vni,
                )
                withdraw_instead = True
                if entry is not None:
                    # Inside, for the same reason the data-plane teardown is: it can refuse, and
                    # its failure must keep the VNI claim rather than leave this node holding
                    # everything else with no binding to retry from.
                    await self._release_backend_ownership(entry, session_id)
            else:
                # Inside, because this deletes the host's devices and the claim is what says we
                # may: the answer must not go stale between being given and being acted on.
                await self._teardown_data_plane(session_id, entry, raw_config)
        # Both paths reach here only if the claim went. Anything that drops our record of the
        # session belongs after that, or a failed unlink leaves nothing for the retry to use.
        if withdraw_instead:
            await self._forget_withdrawn(session_id)
            return
        await self._journal.forget_session(session_id)

    async def _teardown_data_plane(
        self,
        session_id: str,
        entry: _SessionEntry | None,
        raw_config: dict[str, Any] | None,
    ) -> None:
        """Remove the session's devices, with this node established as their last holder."""
        if entry is not None:
            await entry.backend.teardown_session_network(session_id)
            self._sessions.pop(session_id, None)
            return
        if raw_config is None:
            return
        # We journalled this session but hold no entry for it — recovery could not rebuild it.
        # Tear it down from the record anyway: reporting success while leaving the bridge up
        # and the session's subnet block claimed is the one outcome we cannot afford, because
        # nothing will ever name them again.
        peer_vteps = (await self._journal.peers()).get(session_id, ())
        meta = self._meta_of(session_id, raw_config)
        backend = self._resolve_backend(meta.backend)
        await backend.adopt_session_network(meta, self._self_member(meta.backend))
        await backend.restore_session_peer_ownership(session_id, self._members_of(peer_vteps))
        await backend.teardown_session_network(session_id)

    async def _journalled_config(self, session_id: str) -> dict[str, Any] | None:
        """The session's journalled network config, or None when the journal has no record of it.

        Only that. An exception here used to become None, and None is what tells teardown there is
        nothing to release and nothing to remove: after a privnet restart with one damaged record,
        a teardown found no binding, deleted no device, dropped the journal record and reported
        success -- leaving the VXLAN, the bridge, the XFRM state, the firewall rules and the LOCAL
        subnet block on the host with nothing left that names them.
        """
        return (await self._journal.sessions()).get(session_id)

    def _kernel_cgroup(self, container_id: str) -> Path:
        """Where this container's cgroup lives. Derived from the validated id, never from the
        request, so the agent cannot name a path outside the tree."""
        return self._runtime.cgroup_path(policy.validate_container_id(container_id))

    def _require_agents_process(self, pid: int) -> None:
        """Refuse a PID that is not the agent's to give.

        The same bound the netns owner check applies on attach: an unprivileged agent can only own
        processes running as its own uid, so anything else is a PID it should not be able to hand
        a privileged operation. Without this the agent could ask for an arbitrary process — say a
        root daemon — to be moved into a cgroup it controls.
        """
        try:
            uid = Path(f"/proc/{pid}/status").read_text().split("Uid:")[1].split()[0]
        except (OSError, IndexError) as e:
            raise PrivNetError("no such process") from e
        if int(uid) != self._allowed_uid:
            raise PrivNetError(f"pid {pid} runs as uid {uid}, not the agent's")

    async def _confine_container(self, req: PrivNetRequest) -> None:
        """Create the container's cgroup, write its limits and move its process tree in."""
        if req.container_id is None or req.cgroup_pid is None:
            raise policy.PolicyViolation("confine requires container_id and cgroup_pid")
        self._require_agents_process(req.cgroup_pid)
        cgroup = self._kernel_cgroup(req.container_id)
        await asyncio.to_thread(_make_cgroup, cgroup, req.cgroup_limits or {}, req.cgroup_pid)

    async def _release_container(self, req: PrivNetRequest) -> None:
        if req.container_id is None:
            raise policy.PolicyViolation("release requires container_id")
        cgroup = self._kernel_cgroup(req.container_id)
        await asyncio.to_thread(_remove_cgroup, cgroup)

    async def _require_container_of_session(self, container_id: str, session_id: str) -> None:
        """Refuse a container that belongs to a different session.

        The overlay address is already confined to the session's own subnet, and the netns owner
        check bounds which namespaces the agent may name at all — but neither says the container
        is *this session's*. Without that, naming a sibling session's container id attaches a veth
        from the wrong session's bridge into a kernel that is not part of it.

        The container carries its own session in a label the agent stamped at creation
        (`ai.backend.session-id`), which the runtime reports: containerd from the daemon's record,
        the rootless backends from their journal. A container we cannot place is warned about and
        allowed — the label is set on every path we know of, and refusing on its absence would turn
        an unknown into a broken session — but one that places *elsewhere* is refused.
        """
        owner = (await self._live_containers()).get(container_id)
        if owner is None:
            log.warning(
                "privnet cannot tell which session container %s belongs to; allowing the attach",
                container_id,
            )
            return
        if owner != session_id:
            raise PrivNetError("container belongs to another session")

    async def _attach(
        self,
        session_id: str,
        container_id: str | None,
        overlay_ip: str | None,
        local_ip: str | None = None,
    ) -> dict[str, str]:
        if container_id is None:
            raise policy.PolicyViolation("attach requires container_id")
        container_id = policy.validate_container_id(container_id)
        entry = self._sessions.get(session_id)
        if entry is None:
            raise PrivNetError("attach before setup")
        await self._require_container_of_session(container_id, session_id)
        # The manager-assigned overlay IP (multi-node vxlan) is agent-supplied, so validate it is
        # confined to THIS session's subnet before trusting it; None (single node) keeps the
        # host-local fallback. attach_endpoint reads it from kernel_config["cluster_network_ip"];
        # the deterministic MAC is derived from it server-side (overlay_cni_config).
        kernel_config: dict[str, Any] = {}
        if overlay_ip is not None:
            kernel_config["cluster_network_ip"] = policy.validate_overlay_ip(
                overlay_ip, entry.meta.subnet
            )
        if local_ip is not None:
            # Single-node cluster pin: honour the address the agent computed for its /etc/hosts map
            # so the container's real LOCAL address matches. Validated as a real IPv4 here; the
            # host-local IPAM confines it to the session's own /26 (a `requested` outside it, or one
            # already taken by a sibling, raises), so a lying agent can at worst fail its own attach.
            kernel_config["local_static_ip"] = policy.validate_ipv4(local_ip, what="local pin ip")
        # PID resolution from the backend's own runtime rather than from the request.
        #
        # How much that is worth depends on the backend. containerd's daemon runs as root and the
        # agent cannot forge its records, so the answer is authoritative. A rootless backend has no
        # daemon: its record is a journal the agent writes, so this is one indirection away from
        # taking the agent's word. `_netns_owner_uid` is what closes that gap — the kernel, not the
        # agent, confirms the namespace is one this agent could have created.
        pid = await self._runtime.container_pid(container_id)
        if pid is None:
            raise PrivNetError("no running task for container")
        pinned = self._netns.open(pid, expected_owner_uid=self._netns_owner_uid)
        try:
            # Re-confirm the PID<->container binding still holds after pinning, so a
            # PID reused between resolution and pin cannot slip through.
            pid2 = await self._runtime.container_pid(container_id)
            if pid2 != pid or not self._netns.alive(pinned):
                raise netns_mod.NetnsError("container task changed during attach")
            # The plan (bridge/subnet CNI config) is derived privnet-side from the session meta;
            # the overlay's static IP (+ derived MAC) comes from the validated kernel_config.
            plan = await entry.backend.attach_endpoint(
                cast(Any, kernel_config), cast(Any, {}), meta=entry.meta
            )
            # The native attacher moves the veth by PID (``ip link set ... netns <pid>``),
            # so it needs the ``/proc/<pid>/ns/net`` form, not the pinned-fd path. The pin
            # above already validated this is a live, non-host container netns; we keep the
            # pidfd open across the attach so a vanished process is still detectable.
            # Journalled before the attach, so a privnet that dies mid-attach still knows on its next
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

    async def _publish_ports(self, session_id: str, req: PrivNetRequest) -> None:
        """DNAT the agent-chosen host ports to this container's LOCAL address.

        The address is the privnet's own record from attach, not something the agent sent: that is
        what keeps a compromised agent from pointing one of the node's ports at an arbitrary host.
        """
        if req.container_id is None:
            raise policy.PolicyViolation("publish requires container_id")
        container_id = policy.validate_container_id(req.container_id)
        ports = policy.validate_port_pairs(req.ports)
        entry = self._sessions.get(session_id)
        if entry is None:
            raise PrivNetError("publish before setup")
        local_ip = entry.local_ips.get(container_id)
        if local_ip is None:
            raise PrivNetError("publish before attach")
        # Stamped with THIS privnet's agent id, not the caller's: the privnet is the process that
        # installs the rule and the one that will reclaim it, and a node can carry several agents
        # over different runtimes whose containers none of the others can see.
        await self._forwarder.install(
            forwards_for(container_id, local_ip, ports, owner_agent_id=self._agent_id)
        )

    async def _unpublish_ports(self, req: PrivNetRequest) -> tuple[int, ...]:
        """Withdraw every rule tagged with this container, returning the host ports it held.

        Needs no session entry: the rules name their own container, so this works after a privnet
        restart too, when nothing in memory remembers the attach.
        """
        if req.container_id is None:
            raise policy.PolicyViolation("unpublish requires container_id")
        container_id = policy.validate_container_id(req.container_id)
        return tuple(await self._forwarder.remove_container(container_id))

    async def _list_ports(self) -> tuple[ForwardEntry, ...]:
        """Every published port on this node, read back from the rules themselves.

        Owner and install time travel with each row because the caller reclaims on them, and this
        daemon is the only thing on the node that can read them -- the rules are root's.
        """
        return tuple(
            (
                f.container_id,
                f.host_port,
                f.container_ip,
                f.container_port,
                f.owner_agent_id,
                f.created_at,
            )
            for f in await self._forwarder.list_forwards()
        )

    async def _local_subnet(self, session_id: str) -> str | None:
        """This session's node-local LOCAL /26, or None if it holds no block.

        Read-only, and the inverse of the concern the rest of this protocol guards: the agent is
        asking which block the privnet ALREADY assigned so it can write /etc/hosts for a
        single-node cluster, not declaring one — a session's subnet is exactly the thing the agent
        must not be able to re-declare, and this only reads it. `subnet_of` never allocates, so a
        query for an unknown or torn-down session returns None rather than minting a block a
        stray kernel could then strand.
        """
        return await self._local_subnets.subnet_of(session_id)

    async def _setup_dns_redirect(self, session_id: str, dns_port: int | None) -> None:
        """Redirect this session's gateway ``:53`` to the agent's resolver on ``127.0.0.1:dns_port``.

        The agent supplies only the loopback port it bound; the privnet derives the gateway from the
        session's own LOCAL block (never trusting the agent for it), so a compromised agent can point
        :53 at its own loopback port and nothing else. No block yet ⇒ nothing to redirect."""
        port = policy.validate_dns_port(dns_port)
        subnet = await self._local_subnets.subnet_of(session_id)
        if subnet is None:
            return
        await redirect_session_dns(subnet, port, session_id)

    async def _detach(self, session_id: str, container_id: str | None) -> None:
        if container_id is None:
            raise policy.PolicyViolation("detach requires container_id")
        container_id = policy.validate_container_id(container_id)
        # Withdraw first, and unconditionally: a DNAT rule outliving its container would send the
        # next holder of that host port at an address that is about to disappear. Keyed by the
        # container's own tag, so it holds even if this privnet never saw the attach.
        await self._forwarder.remove_container(container_id)
        entry = self._sessions.get(session_id)
        if entry is None:
            await self._journal.forget_attachment(container_id)
            return
        plan = entry.attached.get(container_id)
        if plan is not None:
            # The plan names the host veth, the address and the DNAT rules this detach has to
            # give back, and it is the only record of them. Dropping it before the detach ran
            # meant a failed one left nothing to retry with: the next call found no plan, took
            # the branch above, deleted the journal entry and reported success over a veth and
            # an address that were still there. It goes once the detach it describes has
            # happened, and not before.
            await self._del_attachment(plan, container_id)
        entry.attached.pop(container_id, None)
        entry.local_ips.pop(container_id, None)
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
            raise PrivNetError("peer/endpoint programming before session setup")
        return entry

    async def _peer(self, session_id: str, req: PrivNetRequest) -> None:
        """Program (ADD_PEER) or remove (DEL_PEER) a peer VTEP's overlay forwarding. The
        Member carries only the validated VTEP; the backend uses nothing else here."""
        entry = self._require_session(session_id)
        vtep_ip = policy.validate_ipv4(req.vtep_ip, what="vtep_ip")
        peer = Member(agent_id="", host_ip=vtep_ip, vtep_ip=vtep_ip)
        recorded = set((await self._journal.peers()).get(session_id, ()))
        if req.op is PrivNetOp.ADD_PEER:
            # Write-ahead: a crash may leave an extra journal entry, but never host state that no
            # durable record names. ENSURE_SECURITY and teardown are idempotent over that excess.
            recorded.add(vtep_ip)
            await self._journal.record_peers(session_id, sorted(recorded))
            await entry.backend.add_peer(session_id, peer)
        else:
            await entry.backend.del_peer(session_id, peer)
            # Remove only after the host teardown lands. A crash between the two over-records an
            # already-gone pair, which is safe and cleaned idempotently during recovery.
            recorded.discard(vtep_ip)
            await self._journal.record_peers(session_id, sorted(recorded))

    async def _ensure_security(self, session_id: str, req: PrivNetRequest) -> None:
        """Re-assert the session's security state against the membership the agent published.

        Every VTEP is validated the way ADD_PEER's is: the list arrives via the agent and is no
        more trusted here than any other request field.
        """
        entry = self._require_session(session_id)
        peers = self._members_of(req.vteps or ())
        # This is a write-ahead ownership record, not a second membership database. Keep any peer
        # not yet confirmed removed by DEL_PEER so a crash cannot make its XFRM state unnameable.
        recorded = set((await self._journal.peers()).get(session_id, ()))
        recorded.update(peer.vtep_ip for peer in peers if peer.vtep_ip is not None)
        await self._journal.record_peers(session_id, sorted(recorded))
        await entry.backend.ensure_session_security(session_id, peers)

    async def _endpoint(self, session_id: str, req: PrivNetRequest) -> None:
        """Program (ADD_ENDPOINT) or remove (DEL_ENDPOINT) a remote container endpoint's
        unicast FDB + ARP entry."""
        entry = self._require_session(session_id)
        ip = policy.validate_ipv4(req.ip, what="endpoint ip")
        mac = policy.validate_mac(req.mac)
        vtep_ip = policy.validate_ipv4(req.vtep_ip, what="vtep_ip")
        if req.op is PrivNetOp.ADD_ENDPOINT:
            await entry.backend.add_endpoint(session_id, ip=ip, mac=mac, vtep_ip=vtep_ip)
        else:
            await entry.backend.del_endpoint(session_id, ip=ip, mac=mac, vtep_ip=vtep_ip)
