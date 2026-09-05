"""Integration tests for the privnet daemon's RPC layer (BEP-1062).

These exercise the real client<->server round trip over a unix socket in-process (no
privileges required): peer auth, protocol framing, input policy, and semantic dispatch
to a stub backend. The privileged veth/netns execution is covered by the native attacher
tests and requires a real container namespace, so it is out of scope here.
"""

from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import itertools
import os
import subprocess
import tempfile
from collections.abc import AsyncIterator, Iterator, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any, cast, override

import pytest

import ai.backend.agent.network.privnet.client as client_mod
import ai.backend.agent.network.privnet.server as server_mod
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator
from ai.backend.agent.network.locator import ContainerLocator, LiveContainer
from ai.backend.agent.network.native_attacher import HostLocalIpam
from ai.backend.agent.network.pair_journal import PairJournal
from ai.backend.agent.network.privnet.client import (
    PrivNetBackendProxy,
    PrivNetClient,
    PrivNetClientError,
    PrivNetProvisioner,
)
from ai.backend.agent.network.privnet.journal import PrivNetJournal
from ai.backend.agent.network.privnet.netns import PinnedNetns
from ai.backend.agent.network.privnet.policy import (
    PolicyViolation,
    validate_network_config,
    validate_overlay_ip,
)
from ai.backend.agent.network.privnet.protocol import PrivNetOp, PrivNetRequest, PrivNetResponse
from ai.backend.agent.network.privnet.server import PrivNetServer
from ai.backend.agent.network.vni_registry import Binding, VniRegistry, config_digest
from ai.backend.common.network.types import (
    AttachKind,
    EndpointPlan,
    Member,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)

_LOCAL_SUBNET = "172.30.0.0/26"


class _StubBackend:
    """Records the semantic calls the server dispatches to a backend."""

    def __init__(
        self,
        *,
        recovery_error: Exception | None = None,
        teardown_failures: int = 0,
        security_failures: int = 0,
    ) -> None:
        self.security_failures = security_failures
        self.setup_calls: list[str] = []
        self.adopt_calls: list[str] = []
        self.teardown_calls: list[str] = []
        self.ensure_calls: list[tuple[str, tuple[str, ...]]] = []
        self.restore_peer_calls: list[tuple[str, tuple[str, ...]]] = []
        self.lifecycle_calls: list[tuple[str, str]] = []
        self._known_sessions: set[str] = set()
        self.peers: list[tuple[str, str, str | None]] = []  # (op, session_id, vtep_ip)
        self.endpoints: list[tuple[str, str, str, str, str]] = []  # (op, sid, ip, mac, vtep)
        self.attach_kernel_configs: list[Any] = []  # kernel_config each attach_endpoint received
        self.self_members: list[Any] = []  # the membership the server publishes for this node
        self.withdraw_calls: list[str] = []
        self.unclosed: frozenset[str] = frozenset()
        self.recovery_preparations = 0
        self.recovery_error = recovery_error
        self.teardown_failures = teardown_failures

    async def withdraw_session_network(self, session_id: str) -> None:
        self.withdraw_calls.append(session_id)
        self._known_sessions.discard(session_id)

    def unclosed_devices(self) -> frozenset[str]:
        return self.unclosed

    async def prepare_recovery(self) -> None:
        self.recovery_preparations += 1
        if self.recovery_error is not None:
            raise self.recovery_error

    async def setup_session_network(self, meta: Any, self_member: Any) -> None:
        self.setup_calls.append(meta.session_id)
        self.self_members.append(self_member)
        self._known_sessions.add(meta.session_id)
        self.lifecycle_calls.append(("setup", meta.session_id))

    async def adopt_session_network(self, meta: Any, self_member: Any) -> None:
        self.adopt_calls.append(meta.session_id)
        self._known_sessions.add(meta.session_id)
        self.lifecycle_calls.append(("adopt", meta.session_id))

    async def teardown_session_network(self, session_id: str) -> None:
        # The real VXLAN backend derives cleanup from its in-memory session registry. A teardown
        # before setup/adopt is an idempotent no-op, which is the restart bug this stub must model.
        if session_id not in self._known_sessions:
            return
        if self.teardown_failures:
            self.teardown_failures -= 1
            raise RuntimeError("link down failed")
        self.teardown_calls.append(session_id)
        self._known_sessions.discard(session_id)
        self.lifecycle_calls.append(("teardown", session_id))

    async def ensure_session_security(self, session_id: str, peers: Any) -> None:
        if self.security_failures:
            self.security_failures -= 1
            raise RuntimeError("the ESP pair could not be re-asserted")
        self.ensure_calls.append((
            session_id,
            tuple(peer.vtep_ip for peer in peers if peer.vtep_ip is not None),
        ))
        self.lifecycle_calls.append(("ensure", session_id))

    async def restore_session_peer_ownership(self, session_id: str, peers: Any) -> None:
        self.restore_peer_calls.append((
            session_id,
            tuple(peer.vtep_ip for peer in peers if peer.vtep_ip is not None),
        ))
        self.lifecycle_calls.append(("restore-peers", session_id))

    async def add_peer(self, session_id: str, peer: Any) -> None:
        self.peers.append(("add", session_id, peer.vtep_ip))

    async def del_peer(self, session_id: str, peer: Any) -> None:
        self.peers.append(("del", session_id, peer.vtep_ip))

    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        self.endpoints.append(("add", session_id, ip, mac, vtep_ip))

    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        self.endpoints.append(("del", session_id, ip, mac, vtep_ip))

    async def attach_endpoint(
        self, kernel_config: Any, cluster_info: Any, *, meta: Any
    ) -> EndpointPlan:
        self.attach_kernel_configs.append(kernel_config)
        # The LOCAL attachment the real backends always emit: it names the node-local subnet the
        # container's address was allocated from, which is how the privnet finds that address again
        # after a restart.
        return EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="eth0",
                    role=NetworkRole.LOCAL,
                    is_default_route=True,
                    cni_config={
                        "type": "bridge",
                        "bridge": "bailo0",
                        "ipam": {"type": "host-local", "subnet": _LOCAL_SUBNET},
                    },
                )
            ]
        )


class _StubRuntime(ContainerLocator):
    """The backend, as the privnet is allowed to see it: which containers are still running, their
    PIDs, and where a cgroup for one would go.

    Three methods is the whole interface, which is the point of it — this stub used to have to
    forge containerd ContainerInfo records to answer a question about session ids.
    """

    def __init__(
        self,
        pid: int | None = None,
        live: dict[str, str] | None = None,
        *,
        cgroup_root: Path | None = None,
    ) -> None:
        self._pid = pid
        self._live = live or {}  # container_id -> session_id
        self._cgroup_root = cgroup_root

    @override
    async def open(self) -> None:
        pass

    @override
    async def container_pid(self, container_id: str) -> int | None:
        return self._pid

    @override
    async def live_sessions(self) -> Mapping[str, LiveContainer]:
        return {
            cid: LiveContainer(session_id=sid, owner_agent_id="i-test")
            for cid, sid in self._live.items()
        }

    @override
    def cgroup_path(self, container_id: str) -> Path:
        if self._cgroup_root is None:
            # A backend that places its own cgroups refuses, exactly as Docker's locator does.
            return super().cgroup_path(container_id)
        return self._cgroup_root / "backendai" / container_id


_socket_counter = itertools.count()


def _short_socket_path() -> str:
    # Unix socket paths are capped near 108 bytes; keep it short. Unique per DAEMON, not per
    # process: two harnesses alive at once are two co-located agents, and sharing the path made
    # the second one's bind unlink the first's socket -- after which both clients reached
    # whichever server happened to be bound.
    return f"/tmp/bai-nh-test-{os.getpid()}-{next(_socket_counter)}.sock"


class _RecordingForwarder:
    """Stands in for the real iptables PortForwarder inside the privnet."""

    def __init__(self, *, remove_failures: int = 0) -> None:
        self.installed: list[Any] = []
        self.removed: list[str] = []
        self.remove_failures = remove_failures

    async def install(self, forwards: Any) -> None:
        self.installed.extend(forwards)

    async def remove_container(self, container_id: str) -> list[int]:
        if self.remove_failures:
            self.remove_failures -= 1
            raise RuntimeError("iptables was busy")
        self.removed.append(container_id)
        return sorted(f.host_port for f in self.installed if f.container_id == container_id)

    async def list_forwards(self, *, container_id: str | None = None) -> list[Any]:
        if container_id is None:
            return list(self.installed)
        return [f for f in self.installed if f.container_id == container_id]


class _RecordingCni:
    """Stands in for the native attach runner, without a netns to move a veth into.

    It allocates from the same durable IPAM store the real runner does, because that store is
    precisely what recovery reads back to find the address a pre-restart attach assigned — a stub
    that skipped it would leave nothing to recover and the test would pass on an empty store.
    """

    def __init__(self, ipam: HostLocalIpam) -> None:
        self._ipam = ipam
        self.calls: list[tuple[str, str, str]] = []  # (command, ifname, container_id)

    async def __call__(
        self,
        command: str,
        *,
        ifname: str = "",
        container_id: str = "",
        config: Any = None,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        self.calls.append((command, ifname, container_id))
        ipam_cfg = (config or {}).get("ipam") or {}
        subnet = ipam_cfg.get("subnet")
        if ipam_cfg.get("type") != "host-local" or not subnet:
            return {}  # a static (overlay) address: nothing to allocate
        if command == "ADD":
            # The real runner reserves the gateway (the first host) for the bridge itself.
            gateway = str(next(iter(ipaddress.ip_network(subnet).hosts())))
            ip = await self._ipam.allocate(subnet, container_id, ifname, reserve=[gateway])
            return {"ips": [{"address": f"{ip}/{subnet.split('/')[1]}"}]}
        if command == "DEL":
            await self._ipam.release(subnet, container_id, ifname)
        return {}

    def dels(self) -> list[str]:
        return [container_id for cmd, _if, container_id in self.calls if cmd == "DEL"]


class _FakeNetns:
    """Pins nothing. A real pin needs a live process in a non-host netns, which a unit test cannot
    produce; the TOCTOU logic it guards is the module's own (netns.py), not the attach path's.

    It does record the owner uid it was asked to require, so a test can assert the server passed
    one (see netns.py for why it matters on a rootless backend)."""

    def __init__(self) -> None:
        self.expected_owner_uids: list[int | None] = []

    def open(self, pid: int, *, expected_owner_uid: int | None = None) -> PinnedNetns:
        self.expected_owner_uids.append(expected_owner_uid)
        return PinnedNetns(netns_fd=-1, pidfd=-1, pid=pid)  # close() tolerates a bad fd

    def alive(self, pinned: PinnedNetns) -> bool:
        return True


class _Harness:
    """One privnet daemon. ``state_dir`` is its journal + IPAM store: pass the same one twice to
    restart the daemon over the state its predecessor left behind."""

    def __init__(
        self,
        runtime: _StubRuntime | None = None,
        *,
        state_dir: Path | None = None,
        forwarder: _RecordingForwarder | None = None,
        vtep_ip: str | None = "192.168.0.10",
        allowed_uid: int | None = None,
        agent_id: str = "i-test",
        recovery_error: Exception | None = None,
        teardown_failures: int = 0,
        security_failures: int = 0,
    ) -> None:
        self.backend = _StubBackend(
            recovery_error=recovery_error,
            teardown_failures=teardown_failures,
            security_failures=security_failures,
        )
        self.forwarder = forwarder or _RecordingForwarder()
        self._tmp = None if state_dir is not None else tempfile.TemporaryDirectory()
        root = state_dir if state_dir is not None else Path(cast(Any, self._tmp).name)
        self.state_dir = root
        self.journal = PrivNetJournal(root / "journal")
        self.ipam = HostLocalIpam(root / "ipam")
        # An allocator on the harness's own state dir, not the process-global one, so LOCAL_SUBNET
        # queries are isolated between tests (and survive a same-state_dir restart, like the real
        # journal does).
        self.local_subnets = LocalSubnetAllocator(root / "local-subnet")
        # Node-wide: every harness in one test shares it, which is what makes two of them
        # co-located agents. Redirected away from the real node-global path by
        # `_isolated_vni_registry`.
        self.vni_registry = VniRegistry()
        self.cni = _RecordingCni(self.ipam)
        self.server = PrivNetServer(
            socket_path=_short_socket_path(),
            allowed_uid=os.getuid() if allowed_uid is None else allowed_uid,
            agent_id=agent_id,
            host_ip="127.0.0.1",
            # The entry point validates the real address; a test injects one so it does not depend
            # on what the machine running it happens to hold. None exercises the refusal path.
            vtep_ip=vtep_ip,
            runtime=cast(Any, runtime or _StubRuntime()),
            cni_runner=self.cni,
            backends=cast(Any, {"bridge": self.backend, "vxlan": self.backend}),
            forwarder=cast(Any, self.forwarder),
            journal=self.journal,
            ipam=self.ipam,
            local_subnets=self.local_subnets,
            vni_registry=self.vni_registry,
            netns_pinner=cast(Any, _FakeNetns()),
        )
        self._task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> _Harness:
        self._task = asyncio.create_task(self.server.serve_forever())
        for _ in range(50):
            if os.path.exists(self.server._socket_path):
                break
            await asyncio.sleep(0.02)
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._task is not None:
            self._task.cancel()
        try:
            os.unlink(self.server._socket_path)
        except OSError:
            pass
        if self._tmp is not None:
            self._tmp.cleanup()

    async def setup(self, session_id: str, **config: object) -> None:
        """Set one session up through the RPC, as an agent would."""
        resp = await self.client().call(
            PrivNetRequest(
                PrivNetOp.SETUP_SESSION,
                session_id,
                network_config={"backend": "bridge", "subnet": "172.30.9.0/24", **config},
            )
        )
        assert resp.ok, resp.error

    def client(self) -> PrivNetClient:
        return PrivNetClient(self.server._socket_path)


async def _hand_the_vni_back(
    h: _Harness, session_id: str, config: dict[str, Any], agent_id: str = "i-test"
) -> None:
    """Model the manager handing a VNI back out.

    The session ended, so this node's binding on its VNI went with it -- while the privnet's own
    journal record of it survived, which is the state a crash between the two leaves behind and
    the reason a dead session and a live one can be journalled on one VNI at all.
    """
    async with h.vni_registry.releasing(
        int(config["vni"]), agent_id, session_id, config_digest(config)
    ):
        pass


@pytest.fixture(autouse=True)
def _isolated_vni_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the node-wide VNI registry at this test's own directory.

    Its real home is a node-global path shared by every agent on the host, which is the point --
    and exactly why a test must never use it: the bindings would outlive the test and the next one
    would be refused a VNI by a session that does not exist.
    """
    monkeypatch.setattr(
        "ai.backend.agent.network.vni_registry.DEFAULT_VNI_REGISTRY_DIR",
        tmp_path / "vni",
    )


class TestProtocol:
    def test_request_roundtrip(self) -> None:
        req = PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config={"backend": "bridge"})
        assert PrivNetRequest.decode(req.encode()) == req

    def test_response_roundtrip(self) -> None:
        resp = PrivNetResponse(ok=True, assigned={"local": "172.30.0.3"})
        assert PrivNetResponse.decode(resp.encode()) == resp

    def test_subnet_field_roundtrips(self) -> None:
        resp = PrivNetResponse(ok=True, subnet="172.30.0.64/26")
        assert PrivNetResponse.decode(resp.encode()) == resp

    def test_attach_local_ip_roundtrips(self) -> None:
        # The single-node cluster LOCAL pin must survive the wire, or the privnet cannot honour it.
        req = PrivNetRequest(
            PrivNetOp.ATTACH_CONTAINER, "s1", container_id="c1", local_ip="172.30.0.9"
        )
        decoded = PrivNetRequest.decode(req.encode())
        assert decoded == req and decoded.local_ip == "172.30.0.9"

    def test_absent_local_ip_stays_none(self) -> None:
        req = PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "s1", container_id="c1")
        assert PrivNetRequest.decode(req.encode()).local_ip is None

    def test_absent_subnet_stays_none(self) -> None:
        assert PrivNetResponse.decode(PrivNetResponse(ok=True).encode()).subnet is None


class TestPolicy:
    def test_rejects_public_subnet(self) -> None:
        with pytest.raises(PolicyViolation):
            validate_network_config({"backend": "bridge", "subnet": "8.8.8.0/24"})

    def test_accepts_private_subnet(self) -> None:
        cfg = validate_network_config({"backend": "bridge", "subnet": "172.30.5.0/24"})
        assert cfg.subnet == "172.30.5.0/24"

    def test_overlay_ip_accepts_in_subnet_host(self) -> None:
        assert validate_overlay_ip("10.0.0.5", "10.0.0.0/24") == "10.0.0.5"

    def test_overlay_ip_rejects_out_of_subnet(self) -> None:
        # confinement to the session subnet is the trust boundary — a foreign address is refused
        with pytest.raises(PolicyViolation):
            validate_overlay_ip("10.9.9.9", "10.0.0.0/24")

    def test_overlay_ip_rejects_network_and_broadcast(self) -> None:
        with pytest.raises(PolicyViolation):
            validate_overlay_ip("10.0.0.0", "10.0.0.0/24")
        with pytest.raises(PolicyViolation):
            validate_overlay_ip("10.0.0.255", "10.0.0.0/24")

    def test_overlay_ip_rejects_garbage_and_none(self) -> None:
        with pytest.raises(PolicyViolation):
            validate_overlay_ip("not-an-ip", "10.0.0.0/24")
        with pytest.raises(PolicyViolation):
            validate_overlay_ip(None, "10.0.0.0/24")


class TestPrivNetRpc:
    async def test_recovery_preflight_failure_does_not_kill_the_privnet(self) -> None:
        async with _Harness(recovery_error=RuntimeError("link down failed")) as h:
            assert await h.client().local_subnet_of("unknown") is None
            assert h.backend.recovery_preparations == 1

    async def test_setup_dispatches_to_backend(self) -> None:
        async with _Harness() as h:
            resp = await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-1",
                    network_config={"backend": "bridge", "subnet": "172.30.1.0/24"},
                )
            )
            assert resp.ok
            assert h.backend.setup_calls == ["sess-1"]

    async def test_teardown_dispatches_to_backend(self) -> None:
        async with _Harness() as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-2",
                    network_config={"backend": "bridge", "subnet": "172.30.2.0/24"},
                )
            )
            await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "sess-2"))
            assert h.backend.teardown_calls == ["sess-2"]

    async def test_failed_teardown_retains_the_session_and_journal_for_retry(self) -> None:
        async with _Harness(teardown_failures=1) as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-retry",
                    network_config={"backend": "bridge", "subnet": "172.30.2.0/24"},
                )
            )

            with pytest.raises(PrivNetClientError):
                await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "sess-retry"))

            assert "sess-retry" in h.server._sessions
            assert "sess-retry" in await h.journal.sessions()

            await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "sess-retry"))
            assert "sess-retry" not in h.server._sessions
            assert "sess-retry" not in await h.journal.sessions()

    async def test_local_subnet_returns_the_block_the_privnet_assigned(self) -> None:
        """The read-only query single-node cluster peer resolution rests on: the agent has no LOCAL
        journal in privnet mode, so it asks the privnet which /26 a session holds."""
        async with _Harness() as h:
            subnet = await h.local_subnets.allocate_subnet("sess-local")
            assert await h.client().local_subnet_of("sess-local") == subnet

    async def test_local_subnet_of_an_unknown_session_is_none(self) -> None:
        """Never allocates, so a query for a session the privnet holds no block for returns None
        rather than minting one a stray kernel could strand."""
        async with _Harness() as h:
            assert await h.client().local_subnet_of("never-seen") is None

    async def test_local_subnet_query_does_not_allocate(self) -> None:
        """Querying an unknown session must leave the pool untouched — otherwise a repeated lookup
        would hand out blocks."""
        async with _Harness() as h:
            await h.client().local_subnet_of("ghost")
            assert await h.local_subnets.subnet_of("ghost") is None

    async def test_local_subnet_degrades_to_none_when_the_privnet_is_unreachable(self) -> None:
        """This lookup is on the kernel-creation path, so a failed query must degrade, not raise:
        an unreachable or too-old privnet loses the peer /etc/hosts entries (the pre-existing gap)
        rather than aborting the kernel. A raising query would break every single-node cluster in
        a deploy where the agent leads the privnet in version."""
        client = PrivNetClient("/nonexistent/privnet.sock")
        assert await client.local_subnet_of("sess-x") is None

    async def test_rejects_unsafe_session_id(self) -> None:
        async with _Harness() as h:
            with pytest.raises(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.SETUP_SESSION,
                        "bad;rm -rf /",
                        network_config={"backend": "bridge"},
                    )
                )
            assert h.backend.setup_calls == []

    async def test_attach_without_running_task_errors(self) -> None:
        async with _Harness(runtime=_StubRuntime(pid=None)) as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-3",
                    network_config={"backend": "bridge", "subnet": "172.30.3.0/24"},
                )
            )
            with pytest.raises(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "sess-3", container_id="c1")
                )

    async def _setup_vxlan(self, h: _Harness, sid: str) -> None:
        await h.client().call(
            PrivNetRequest(
                PrivNetOp.SETUP_SESSION,
                sid,
                network_config={"backend": "vxlan", "subnet": "10.0.0.0/24", "vni": 100},
            )
        )

    async def test_attach_rejects_overlay_ip_outside_session_subnet(self) -> None:
        # An agent-supplied overlay IP is validated against the session subnet BEFORE any netns
        # work; a foreign address is refused and never reaches the backend attach.
        async with _Harness(runtime=_StubRuntime(pid=None)) as h:
            await self._setup_vxlan(h, "sess-ip")
            with pytest.raises(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.ATTACH_CONTAINER, "sess-ip", container_id="c1", ip="10.9.9.9"
                    )
                )
            assert h.backend.attach_kernel_configs == []  # rejected before building the plan

    async def test_attach_pins_the_single_node_cluster_local_ip(self) -> None:
        # The deterministic LOCAL address the agent computed for /etc/hosts must reach the backend's
        # attach as local_static_ip, or the privnet allocates a dynamic address that does not match
        # the map and single-node cluster peer resolution is wrong (privnet-mode only bug).
        async with _Harness(runtime=_StubRuntime(pid=4242)) as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-pin",
                    network_config={"backend": "bridge", "subnet": "172.30.5.0/24"},
                )
            )
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.ATTACH_CONTAINER,
                    "sess-pin",
                    container_id="c1",
                    local_ip="172.30.5.9",
                )
            )
            assert h.backend.attach_kernel_configs  # attach reached the backend
            assert h.backend.attach_kernel_configs[-1].get("local_static_ip") == "172.30.5.9"

    async def test_attach_rejects_a_garbage_local_ip(self) -> None:
        async with _Harness(runtime=_StubRuntime(pid=4242)) as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-badpin",
                    network_config={"backend": "bridge", "subnet": "172.30.6.0/24"},
                )
            )
            with pytest.raises(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.ATTACH_CONTAINER,
                        "sess-badpin",
                        container_id="c1",
                        local_ip="not-an-ip",
                    )
                )
            assert h.backend.attach_kernel_configs == []  # rejected before the plan

    async def test_self_member_advertises_the_validated_vtep(self) -> None:
        # It is the privnet, not the agent, that publishes membership when it runs — so the address
        # peers program into their FDB comes from here, and must be the validated one.
        async with _Harness() as h:
            await self._setup_vxlan(h, "sess-v")
            assert h.backend.self_members[-1].vtep_ip == "192.168.0.10"

    async def test_a_vxlan_session_is_refused_without_a_usable_vtep(self) -> None:
        # Setting it up anyway would publish an unusable VTEP; peers guard on `is None` alone, so
        # they would program "" / 0.0.0.0 and the session would hang at rendezvous with no error.
        async with _Harness(vtep_ip=None) as h:
            with pytest.raises(PrivNetClientError):
                await self._setup_vxlan(h, "sess-novtep")
            assert h.backend.setup_calls == []  # refused before anything was journalled or built

    async def test_a_bridge_session_still_works_without_a_vtep(self) -> None:
        async with _Harness(vtep_ip=None) as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION, "sess-b", network_config={"backend": "bridge"}
                )
            )
            assert h.backend.setup_calls == ["sess-b"]

    async def test_add_peer_dispatches_vtep(self) -> None:
        async with _Harness() as h:
            await self._setup_vxlan(h, "sess-p")
            await h.client().call(
                PrivNetRequest(PrivNetOp.ADD_PEER, "sess-p", vtep_ip="192.168.1.9")
            )
            assert h.backend.peers == [("add", "sess-p", "192.168.1.9")]
            assert await h.journal.peers() == {"sess-p": ("192.168.1.9",)}

            await h.client().call(
                PrivNetRequest(PrivNetOp.DEL_PEER, "sess-p", vtep_ip="192.168.1.9")
            )
            assert await h.journal.peers() == {"sess-p": ()}

    async def test_add_endpoint_dispatches_ip_mac_vtep(self) -> None:
        async with _Harness() as h:
            await self._setup_vxlan(h, "sess-e")
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.ADD_ENDPOINT,
                    "sess-e",
                    ip="10.0.0.5",
                    mac="02:42:0a:00:00:05",
                    vtep_ip="192.168.1.9",
                )
            )
            assert h.backend.endpoints == [
                ("add", "sess-e", "10.0.0.5", "02:42:0a:00:00:05", "192.168.1.9")
            ]

    async def test_rejects_bad_mac_and_vtep(self) -> None:
        async with _Harness() as h:
            await self._setup_vxlan(h, "sess-b")
            with pytest.raises(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(PrivNetOp.ADD_PEER, "sess-b", vtep_ip="not-an-ip")
                )
            with pytest.raises(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.ADD_ENDPOINT,
                        "sess-b",
                        ip="10.0.0.5",
                        mac="zz:zz",
                        vtep_ip="192.168.1.9",
                    )
                )
            assert h.backend.peers == [] and h.backend.endpoints == []

    async def test_peer_before_setup_errors(self) -> None:
        async with _Harness() as h:
            with pytest.raises(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(PrivNetOp.ADD_PEER, "no-session", vtep_ip="192.168.1.9")
                )


class TestSessionLock:
    """The per-session lock is refcounted, so it is never dropped from the registry while a holder
    or waiter still references it. Popping it mid-hold (the old ``_teardown`` behaviour) would let
    the next arrival mint a fresh lock and enter the critical section alongside the current holder --
    e.g. a SETUP_SESSION racing a TEARDOWN_SESSION of the same session, building and deleting the
    same-named bridge at once (BEP-1062)."""

    def _server(self, tmp_path: Path) -> PrivNetServer:
        return _Harness(state_dir=tmp_path).server

    async def test_same_session_ops_serialize_on_one_shared_lock(self, tmp_path: Path) -> None:
        server = self._server(tmp_path)
        order: list[str] = []
        release_first = asyncio.Event()

        async def first() -> None:
            async with server._session_locked("s1"):
                order.append("first-enter")
                await release_first.wait()
                order.append("first-exit")

        async def second() -> None:
            async with server._session_locked("s1"):
                order.append("second-enter")

        t1 = asyncio.create_task(first())
        await asyncio.sleep(0)  # let `first` acquire the lock
        held = server._locks["s1"]
        t2 = asyncio.create_task(second())
        await asyncio.sleep(0.02)  # give `second` every chance to (wrongly) run concurrently
        # `second` is blocked behind `first`, on the SAME lock object -- not a freshly minted one.
        assert order == ["first-enter"]
        assert server._locks["s1"] is held
        assert server._lock_users["s1"] == 2
        release_first.set()
        await asyncio.gather(t1, t2)
        assert order == ["first-enter", "first-exit", "second-enter"]
        # The registry shrinks back to empty once the last user leaves.
        assert "s1" not in server._locks
        assert "s1" not in server._lock_users

    async def test_lock_survives_a_holder_that_pops_no_entry(self, tmp_path: Path) -> None:
        # Even if the body does teardown-like work, the lock entry stays until the context exits.
        server = self._server(tmp_path)
        async with server._session_locked("s1"):
            assert "s1" in server._locks
            server._sessions.pop("s1", None)  # what _teardown does; must not touch _locks
            assert "s1" in server._locks
        assert "s1" not in server._locks

    """The privnet outlives the agent, but not every crash. Its session registry is memory while the
    node's bridges, veths and DNAT rules are not — so a restarted privnet that did not rebuild it
    would hold a node it refuses to talk about: a new kernel could not join a running session, and
    a teardown would report success while leaking the session's devices and its subnet block.
    """

    _CONFIG = {"backend": "bridge", "subnet": "172.30.0.0/16"}

    async def _first_life(self, state_dir: Path, *, live: dict[str, str]) -> _RecordingForwarder:
        """A privnet that set a session up and attached its container, then died."""
        forwarder = _RecordingForwarder()
        async with _Harness(
            runtime=_StubRuntime(pid=4242, live=live),
            state_dir=state_dir,
            forwarder=forwarder,
        ) as h:
            await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._CONFIG))
            )
            for container_id in live:
                await h.client().call(
                    PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "s1", container_id=container_id)
                )
        return forwarder

    async def test_a_live_session_is_re_adopted_not_set_up_again(self, tmp_path: Path) -> None:
        # setup_session_network deletes a stale device of the session's name before CNI recreates
        # it — right for a fresh session, fatal for this one: its bridge is up and carrying the
        # kernels' traffic. Recovery must adopt, never set up.
        await self._first_life(tmp_path, live={"c1": "s1"})

        async with _Harness(
            runtime=_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path
        ) as restarted:
            assert restarted.backend.adopt_calls == ["s1"]
            assert restarted.backend.setup_calls == []
            assert restarted.backend.teardown_calls == []

    async def test_a_pre_restart_session_still_serves_its_verbs(self, tmp_path: Path) -> None:
        # Before this, every verb about a session that predates the restart was refused with
        # "before session setup" — a second kernel could not join it, and its peers went unprogrammed.
        await self._first_life(tmp_path, live={"c1": "s1"})

        async with _Harness(
            runtime=_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path
        ) as restarted:
            resp = await restarted.client().call(
                PrivNetRequest(PrivNetOp.ADD_PEER, "s1", vtep_ip="192.168.1.9")
            )
            assert resp.ok
            assert restarted.backend.peers == [("add", "s1", "192.168.1.9")]

    async def test_a_pre_restart_container_publishes_to_the_address_it_actually_holds(
        self, tmp_path: Path
    ) -> None:
        # The DNAT destination is the LOCAL address the privnet assigned at attach — never one the
        # agent sends. After a restart that address is only in the IPAM store, so recovery reads it
        # back from there; without it, publishing for a surviving kernel would be refused.
        await self._first_life(tmp_path, live={"c1": "s1"})
        assigned = (await HostLocalIpam(tmp_path / "ipam").owners(_LOCAL_SUBNET))["c1/eth0"]

        async with _Harness(
            runtime=_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path
        ) as restarted:
            await restarted.client().call(
                PrivNetRequest(
                    PrivNetOp.PUBLISH_PORTS,
                    "s1",
                    container_id="c1",
                    ports=((30001, 8070, None, "tcp"),),
                )
            )
            assert [f.container_ip for f in restarted.forwarder.installed] == [assigned]

    async def test_a_session_whose_containers_all_died_is_torn_down(self, tmp_path: Path) -> None:
        # Its subnet block is finite and nobody else will ever name these devices: the agent
        # already believes the session gone (or is gone itself), so only this pass can give
        # them back.
        await self._first_life(tmp_path, live={"c1": "s1"})

        async with _Harness(runtime=_StubRuntime(live={}), state_dir=tmp_path) as restarted:
            assert restarted.backend.teardown_calls == ["s1"]
            assert restarted.backend.adopt_calls == ["s1"]
            assert restarted.backend.lifecycle_calls == [
                ("adopt", "s1"),
                ("restore-peers", "s1"),
                ("teardown", "s1"),
            ]
            assert await restarted.journal.sessions() == {}

    async def test_a_dead_session_is_not_reclaimed_while_a_live_one_holds_its_vni(
        self, tmp_path: Path
    ) -> None:
        """Devices are named after the VNI and the manager hands VNIs back out, so reclaiming a
        dead session whose VNI a live one now holds deletes the LIVE session's devices. Measured on
        three nodes: a terminated session and a running one both held VNI 4138, and reclaiming the
        dead one left the running session RUNNING with its kernels up, its vxlan device gone and no
        cross-node traffic."""
        vxlan = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}
        async with _Harness(
            runtime=_StubRuntime(pid=4242, live={"c-old": "dead"}), state_dir=tmp_path
        ) as first:
            await first.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "dead", network_config=dict(vxlan))
            )
            await first.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "dead", container_id="c-old")
            )
            await _hand_the_vni_back(first, "dead", vxlan)
            await first.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "live", network_config=dict(vxlan))
            )
            await first.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "live", container_id="c-new")
            )

        # Only "live" still has a container; both journalled sessions claim VNI 4138.
        async with _Harness(
            runtime=_StubRuntime(live={"c-new": "live"}), state_dir=tmp_path
        ) as restarted:
            assert "dead" not in restarted.backend.teardown_calls
            # and it stays in the journal, so a later recovery reclaims it once "live" has ended
            assert "dead" in await restarted.journal.sessions()

    async def test_a_dead_session_on_its_own_vni_is_still_reclaimed(self, tmp_path: Path) -> None:
        vxlan = {"backend": "vxlan", "subnet": "10.128.5.0/24", "mtu": 1412}
        async with _Harness(
            runtime=_StubRuntime(pid=4242, live={"c-old": "dead"}), state_dir=tmp_path
        ) as first:
            await first.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION, "dead", network_config={**vxlan, "vni": 4138}
                )
            )
            await first.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "dead", container_id="c-old")
            )
            await first.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION, "live", network_config={**vxlan, "vni": 4139}
                )
            )
            await first.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "live", container_id="c-new")
            )

        async with _Harness(
            runtime=_StubRuntime(live={"c-new": "live"}), state_dir=tmp_path
        ) as restarted:
            assert "dead" in restarted.backend.teardown_calls
            assert "dead" not in await restarted.journal.sessions()

    async def test_live_security_is_restored_before_dead_sessions_are_reclaimed(
        self, tmp_path: Path
    ) -> None:
        live = {"c-live-a": "s-live-a", "c-live-b": "s-live-b"}
        async with _Harness(runtime=_StubRuntime(pid=4242, live=live), state_dir=tmp_path) as first:
            # Insert the dead record first so dictionary order cannot accidentally satisfy the
            # contract. Shared XFRM refcounts must know every live user before dead cleanup runs.
            for vni, sid in enumerate(("s-dead", "s-live-b", "s-live-a"), start=100):
                await first.client().call(
                    PrivNetRequest(
                        PrivNetOp.SETUP_SESSION,
                        sid,
                        network_config={
                            "backend": "vxlan",
                            "subnet": "10.0.0.0/24",
                            "vni": vni,
                        },
                    )
                )
                await first.client().call(
                    PrivNetRequest(PrivNetOp.ADD_PEER, sid, vtep_ip="192.168.1.9")
                )
            for container_id, session_id in live.items():
                await first.client().call(
                    PrivNetRequest(
                        PrivNetOp.ATTACH_CONTAINER, session_id, container_id=container_id
                    )
                )

        async with _Harness(
            runtime=_StubRuntime(pid=4242, live=live), state_dir=tmp_path
        ) as restarted:
            assert restarted.backend.ensure_calls == [
                ("s-live-a", ("192.168.1.9",)),
                ("s-live-b", ("192.168.1.9",)),
            ]
            assert restarted.backend.restore_peer_calls == [
                ("s-live-a", ("192.168.1.9",)),
                ("s-live-b", ("192.168.1.9",)),
                ("s-dead", ("192.168.1.9",)),
            ]
            last_live_restore = max(
                restarted.backend.lifecycle_calls.index(("restore-peers", sid))
                for sid in ("s-live-a", "s-live-b")
            )
            first_live_ensure = min(
                restarted.backend.lifecycle_calls.index(("ensure", sid))
                for sid in ("s-live-a", "s-live-b")
            )
            assert last_live_restore < first_live_ensure
            assert restarted.backend.lifecycle_calls.index(("ensure", "s-live-b")) < (
                restarted.backend.lifecycle_calls.index(("teardown", "s-dead"))
            )

    async def test_a_container_that_died_gives_back_its_veth_and_address(
        self, tmp_path: Path
    ) -> None:
        # The container's netns took its end of the veth with it; the host side, its address and
        # its DNAT rules are the privnet's to release.
        await self._first_life(tmp_path, live={"c1": "s1"})

        async with _Harness(runtime=_StubRuntime(live={}), state_dir=tmp_path) as restarted:
            assert restarted.cni.dels() == ["c1"]
            assert restarted.forwarder.removed == ["c1"]
            assert await restarted.journal.attachments() == {}

    async def test_teardown_after_a_restart_actually_tears_down(self, tmp_path: Path) -> None:
        # The worst of the old failures: with no session entry, teardown returned ok while the
        # bridge stayed up and the block stayed claimed. Nothing said so.
        await self._first_life(tmp_path, live={"c1": "s1"})

        async with _Harness(
            runtime=_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path
        ) as restarted:
            resp = await restarted.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            assert resp.ok
            assert restarted.backend.teardown_calls == ["s1"]
            assert await restarted.journal.sessions() == {}

    async def test_a_surviving_container_can_still_be_detached(self, tmp_path: Path) -> None:
        # Its plan is re-derived from the journal, so the detach gives back the same host veth and
        # address the pre-restart attach took.
        await self._first_life(tmp_path, live={"c1": "s1"})

        async with _Harness(
            runtime=_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path
        ) as restarted:
            await restarted.client().call(
                PrivNetRequest(PrivNetOp.DETACH_CONTAINER, "s1", container_id="c1")
            )
            assert restarted.cni.dels() == ["c1"]
            assert await restarted.journal.attachments() == {}

    async def test_a_privnet_with_no_journal_starts_clean(self, tmp_path: Path) -> None:
        # A first-ever boot must not be a special case.
        async with _Harness(runtime=_StubRuntime(live={}), state_dir=tmp_path) as h:
            assert h.backend.recovery_preparations == 1
            assert h.backend.adopt_calls == [] and h.backend.teardown_calls == []
            resp = await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._CONFIG))
            )
            assert resp.ok


class _RecordingClient:
    """Captures the requests PrivNetProvisioner sends, returning a benign ATTACH response."""

    def __init__(self) -> None:
        self.requests: list[PrivNetRequest] = []

    async def call(self, req: PrivNetRequest) -> PrivNetResponse:
        self.requests.append(req)
        return PrivNetResponse(ok=True, assigned={})


class TestPrivNetProvisioner:
    async def test_attach_forwards_manager_overlay_ip(self) -> None:
        # The agent relays the manager-assigned cluster_network_ip to the privnet so a multi-node
        # container attaches at its central, disjoint overlay address (the privnet re-validates it).
        client = _RecordingClient()
        prov = PrivNetProvisioner(cast(Any, client), "s1")
        meta = SessionNetMeta(
            session_id="s1",
            subnet="10.0.0.0/24",
            backend=NetworkBackendKind.VXLAN,
            mtu=1500,
            vni=100,
        )
        await prov.attach(
            cast(Any, {"cluster_network_ip": "10.0.0.5"}),
            cast(Any, {}),
            meta=meta,
            container_id="c1",
            task_pid=1,
        )
        assert client.requests[0].op is PrivNetOp.ATTACH_CONTAINER
        assert client.requests[0].ip == "10.0.0.5"

    async def test_attach_sends_no_ip_for_single_node(self) -> None:
        # Single-node sessions have no manager overlay IP; the privnet keeps its host-local path.
        client = _RecordingClient()
        prov = PrivNetProvisioner(cast(Any, client), "s1")
        meta = SessionNetMeta(
            session_id="s2",
            subnet="10.0.1.0/24",
            backend=NetworkBackendKind.BRIDGE,
            mtu=1500,
            vni=None,
        )
        await prov.attach(cast(Any, {}), cast(Any, {}), meta=meta, container_id="c2", task_pid=1)
        assert client.requests[0].ip is None


_NC = {"backend": "bridge", "subnet": "172.30.0.0/24"}
_LOCAL_IP = "172.30.0.5"


async def _publish(h: _Harness, ports: tuple[tuple[int, int, str | None, str], ...]) -> None:
    await h.client().call(
        PrivNetRequest(op=PrivNetOp.PUBLISH_PORTS, session_id="s1", container_id="c1", ports=ports)
    )


class TestPublishPorts:
    """Host-port ingress under privilege separation: the agent chooses the ports, the privnet
    chooses the destination."""

    async def _setup(self, h: _Harness, *, attached: bool = True) -> None:
        await h.client().call(
            PrivNetRequest(op=PrivNetOp.SETUP_SESSION, session_id="s1", network_config=_NC)
        )
        if attached:
            # what a successful ATTACH_CONTAINER records; re-testing attach here would only
            # re-test netns pinning, which has its own tests
            h.server._sessions["s1"].local_ips["c1"] = _LOCAL_IP

    async def test_publishes_to_the_address_the_privnet_assigned(self) -> None:
        async with _Harness() as h:
            await self._setup(h)
            await _publish(h, ((30001, 8070, None, "tcp"),))
            assert [(f.host_port, f.container_port) for f in h.forwarder.installed] == [
                (30001, 8070)
            ]
            # the destination is the privnet's own attach record, never anything the agent sent
            assert {f.container_ip for f in h.forwarder.installed} == {_LOCAL_IP}

    async def test_a_udp_port_publishes_as_udp(self) -> None:
        # The protocol survives the wire (encode -> decode -> validate) and reaches the installed
        # PortForward, so the privnet emits a -p udp DNAT.
        async with _Harness() as h:
            await self._setup(h)
            await _publish(h, ((30001, 8070, None, "udp"),))
            assert [f.protocol for f in h.forwarder.installed] == ["udp"]

    async def test_publish_before_attach_is_refused(self) -> None:
        async with _Harness() as h:
            await self._setup(h, attached=False)
            with pytest.raises(PrivNetClientError):
                await _publish(h, ((30001, 8070, None, "tcp"),))
            assert h.forwarder.installed == []

    async def test_a_privileged_host_port_is_refused(self) -> None:
        # the privnet runs as root: publishing on 22 would hijack the node's own sshd
        async with _Harness() as h:
            await self._setup(h)
            with pytest.raises(PrivNetClientError):
                await _publish(h, ((22, 22, None, "tcp"),))
            assert h.forwarder.installed == []

    async def test_a_duplicate_host_port_is_refused(self) -> None:
        async with _Harness() as h:
            await self._setup(h)
            with pytest.raises(PrivNetClientError):
                await _publish(h, ((30001, 8070, None, "tcp"), (30001, 7681, None, "tcp")))
            assert h.forwarder.installed == []

    async def test_unpublish_returns_the_host_ports_and_needs_no_session(self) -> None:
        async with _Harness() as h:
            await self._setup(h)
            await _publish(h, ((30001, 8070, None, "tcp"), (30002, 7681, None, "tcp")))
            # a session the privnet never heard of: the rules still name their own container
            resp = await h.client().call(
                PrivNetRequest(op=PrivNetOp.UNPUBLISH_PORTS, session_id="c1", container_id="c1")
            )
            assert sorted(resp.host_ports or ()) == [30001, 30002]
            assert h.forwarder.removed == ["c1"]

    async def test_detach_withdraws_the_published_ports(self) -> None:
        # a DNAT rule outliving its container would point the next holder of that host port at
        # an address that is gone
        async with _Harness() as h:
            await self._setup(h)
            await _publish(h, ((30001, 8070, None, "tcp"),))
            await h.client().call(
                PrivNetRequest(op=PrivNetOp.DETACH_CONTAINER, session_id="s1", container_id="c1")
            )
            assert h.forwarder.removed == ["c1"]

    async def test_list_ports_reports_every_published_rule(self) -> None:
        async with _Harness() as h:
            await self._setup(h)
            await _publish(h, ((30001, 8070, None, "tcp"),))
            resp = await h.client().call(
                PrivNetRequest(op=PrivNetOp.LIST_PORTS, session_id="list-ports")
            )
            assert resp.forwards == (("c1", 30001, _LOCAL_IP, 8070),)


class TestSessionBinding:
    """The overlay address is confined to the session's subnet and the netns owner check bounds
    which namespaces may be named, but neither says the container is *this session's*. Without the
    binding, naming a sibling session's container attaches a veth from the wrong bridge into a
    kernel that is not part of that session."""

    async def test_a_container_of_another_session_is_refused(self) -> None:
        runtime = _StubRuntime(pid=4242, live={"c-of-s2": "sess-b"})
        async with _Harness(runtime=runtime) as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-a",
                    network_config={"backend": "bridge", "subnet": "172.30.6.0/24"},
                )
            )
            with pytest.raises(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "sess-a", container_id="c-of-s2")
                )

    async def test_its_own_container_still_attaches(self) -> None:
        runtime = _StubRuntime(pid=4242, live={"c-of-a": "sess-a"})
        async with _Harness(runtime=runtime) as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-a",
                    network_config={"backend": "bridge", "subnet": "172.30.7.0/24"},
                )
            )
            await h.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "sess-a", container_id="c-of-a")
            )

    async def test_a_container_we_cannot_place_is_allowed(self) -> None:
        """The label is set on every path we know of; refusing on its absence would turn an
        unknown into a broken session. It is warned about instead."""
        async with _Harness(runtime=_StubRuntime(pid=4242)) as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-a",
                    network_config={"backend": "bridge", "subnet": "172.30.8.0/24"},
                )
            )
            await h.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "sess-a", container_id="c-unknown")
            )


def _a_pid_owned_by_someone_else() -> int | None:
    """Any live PID > 1 that does not run as this uid — what the agent must not be able to name."""
    me = os.getuid()
    for entry in sorted(Path("/proc").iterdir()):
        if not entry.name.isdigit() or int(entry.name) <= 1:
            continue
        try:
            uid = int(entry.joinpath("status").read_text().split("Uid:")[1].split()[0])
        except (OSError, IndexError, ValueError):
            continue
        if uid != me:
            return int(entry.name)
    return None


@contextlib.contextmanager
def _a_leaf_process() -> Iterator[int]:
    """A live child of ours with no children of its own, so the pid set written is deterministic."""
    proc = subprocess.Popen(["sleep", "60"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        yield proc.pid
    finally:
        proc.kill()
        proc.wait()


class TestConfiningAContainer:
    """The cgroup delegation, driven through the daemon rather than through its wire format.

    The only coverage this had was a `PrivNetRequest` JSON round-trip, which is why `_make_cgroup`
    and `_require_agents_process` could both be replaced by `return` with the whole suite still
    green (verified by mutation). What the delegation exists to do is put numbers in cgroup files,
    so that is what is asserted here.
    """

    @pytest.fixture
    def cgroup_root(self, tmp_path: Path) -> Path:
        """Redirect the cgroup tree into tmp: the real one is /sys/fs/cgroup and root-owned. The
        locator is what says where a container's cgroup lives, so the redirect goes through it."""
        return tmp_path / "cgroup"

    async def test_the_limits_actually_land_in_the_cgroup(self, cgroup_root: Path) -> None:
        async with _Harness(_StubRuntime(cgroup_root=cgroup_root)) as h:
            with _a_leaf_process() as pid:
                await h.client().confine_container(
                    "sess-a", "c1", pid, {"memory.max": "8589934592", "cpuset.cpus": "0-3"}
                )

            leaf = cgroup_root / "backendai" / "c1"
            assert (leaf / "memory.max").read_text() == "8589934592"
            assert (leaf / "cpuset.cpus").read_text() == "0-3"

    async def test_the_process_tree_is_moved_in(self, cgroup_root: Path) -> None:
        """A cgroup with the right numbers and nobody in it limits nothing."""
        async with _Harness(_StubRuntime(cgroup_root=cgroup_root)) as h:
            with _a_leaf_process() as pid:
                await h.client().confine_container("sess-a", "c1", pid, {"memory.max": "1024"})

                assert (cgroup_root / "backendai" / "c1" / "cgroup.procs").read_text() == str(pid)

    async def test_a_pid_that_is_not_the_agents_is_refused(self, cgroup_root: Path) -> None:
        """The one privilege boundary on this path: an unprivileged agent may only hand over its
        own processes, or it could have a root daemon moved into a cgroup it controls."""
        other = _a_pid_owned_by_someone_else()
        if other is None:
            pytest.skip("no process of another uid on this host")
        async with _Harness(_StubRuntime(cgroup_root=cgroup_root)) as h:
            with pytest.raises(PrivNetClientError, match="not the agent's"):
                await h.client().confine_container("sess-a", "c1", other, {"memory.max": "1024"})

            assert not (cgroup_root / "backendai" / "c1").exists()

    async def test_a_pid_that_has_exited_is_refused(self, cgroup_root: Path) -> None:
        with _a_leaf_process() as pid:
            pass  # killed and reaped on the way out
        async with _Harness(_StubRuntime(cgroup_root=cgroup_root)) as h:
            with pytest.raises(PrivNetClientError, match="no such process"):
                await h.client().confine_container("sess-a", "c1", pid, {"memory.max": "1024"})

    async def test_releasing_removes_the_cgroup(self, cgroup_root: Path) -> None:
        async with _Harness(_StubRuntime(cgroup_root=cgroup_root)) as h:
            with _a_leaf_process() as pid:
                await h.client().confine_container("sess-a", "c1", pid, {"memory.max": "1024"})
            leaf = cgroup_root / "backendai" / "c1"
            # cgroupfs interface files are not ordinary files and do not block rmdir; the tmp tree
            # standing in for it has to be emptied for the same rmdir to succeed.
            for f in leaf.iterdir():
                f.unlink()

            await h.client().release_container("sess-a", "c1")

            assert not leaf.exists()

    async def test_a_container_id_that_is_not_one_cannot_name_a_path(
        self, cgroup_root: Path
    ) -> None:
        """`_kernel_cgroup` composes a filesystem path out of the id, so the id is validated."""
        async with _Harness(_StubRuntime(cgroup_root=cgroup_root)) as h:
            with _a_leaf_process() as pid:
                with pytest.raises(PrivNetClientError):
                    await h.client().confine_container(
                        "sess-a", "../../../escape", pid, {"memory.max": "1024"}
                    )

    @pytest.mark.skipif(os.geteuid() == 0, reason="root ignores the directory permission")
    async def test_a_limit_that_could_not_be_written_is_reported(self, cgroup_root: Path) -> None:
        """The failure mode this whole delegation exists to remove, on the delegation itself.

        Writing the limits used to be wrapped in `suppress(OSError)`: an undelegated controller or
        a read-only leaf produced a kernel running with `memory.max = max`, no exception, no log —
        exactly what was measured before the delegation existed. Modelled here by a leaf that
        accepts no new files.
        """
        leaf = cgroup_root / "backendai" / "c1"
        leaf.mkdir(parents=True)
        leaf.chmod(0o500)
        try:
            async with _Harness(_StubRuntime(cgroup_root=cgroup_root)) as h:
                with _a_leaf_process() as pid:
                    with pytest.raises(PrivNetClientError, match=r"memory\.max"):
                        await h.client().confine_container(
                            "sess-a", "c1", pid, {"memory.max": "8589934592"}
                        )
        finally:
            leaf.chmod(0o700)

    async def test_a_cgroup_nobody_could_be_moved_into_is_reported(
        self, cgroup_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Limits on an empty cgroup confine nothing, so writing them all is not success."""
        monkeypatch.setattr(server_mod, "_descendants", lambda pid: [], raising=True)
        async with _Harness(_StubRuntime(cgroup_root=cgroup_root)) as h:
            with _a_leaf_process() as pid:
                leaf = cgroup_root / "backendai" / "c1"
                leaf.mkdir(parents=True)
                (leaf / "cgroup.procs").mkdir()  # a directory cannot be written to

                with pytest.raises(PrivNetClientError, match="could be moved in"):
                    await h.client().confine_container("sess-a", "c1", pid, {"memory.max": "1024"})


class TestPeerAuthentication:
    """Only the configured agent uid may drive the privnet.

    This is the first line of the daemon's trust model and it had no test at all: the harness
    always passed its own uid, so the refusal branch was never taken. Everything else in that model
    — session binding, the netns owner, the cgroup PID check — assumes the caller already got past
    here.
    """

    async def test_a_connection_from_another_uid_is_refused(self) -> None:
        """SO_PEERCRED is the kernel's answer, not the caller's claim, so a wrong uid cannot be
        talked around. Modelled by a daemon that expects somebody else."""
        async with _Harness(allowed_uid=os.getuid() + 1) as h:
            with pytest.raises(PrivNetClientError, match="unauthorized"):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.SETUP_SESSION,
                        "sess-a",
                        network_config={"backend": "bridge", "subnet": "172.30.9.0/24"},
                    )
                )

    async def test_the_refused_request_is_not_performed(self) -> None:
        """A refusal that still ran the verb would be no refusal. The backend is the thing that
        would have touched the host."""
        async with _Harness(allowed_uid=os.getuid() + 1) as h:
            with contextlib.suppress(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.SETUP_SESSION,
                        "sess-a",
                        network_config={"backend": "bridge", "subnet": "172.30.9.0/24"},
                    )
                )

            assert h.backend.setup_calls == []

    async def test_nothing_is_journalled_for_a_refused_caller(self) -> None:
        """The journal is replayed at the next boot; a record written for a caller we refused would
        outlive the refusal."""
        async with _Harness(allowed_uid=os.getuid() + 1) as h:
            with contextlib.suppress(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.SETUP_SESSION,
                        "sess-a",
                        network_config={"backend": "bridge", "subnet": "172.30.9.0/24"},
                    )
                )

            assert await h.journal.sessions() == {}

    async def test_the_configured_uid_is_accepted(self) -> None:
        """The positive control: without it the tests above also pass on a daemon that refuses
        everyone."""
        async with _Harness() as h:
            await h.client().call(
                PrivNetRequest(
                    PrivNetOp.SETUP_SESSION,
                    "sess-a",
                    network_config={"backend": "bridge", "subnet": "172.30.9.0/24"},
                )
            )

            assert h.backend.setup_calls == ["sess-a"]

    async def test_the_socket_is_not_reachable_by_other_users(self) -> None:
        """Peer auth answers who is calling; the mode is what stops them connecting at all. Both,
        because a socket anyone may open is a refusal path anyone may exercise."""
        async with _Harness() as h:
            mode = os.stat(h.server._socket_path).st_mode & 0o777

            assert mode == 0o600, oct(mode)


class TestDeferredRecovery:
    """A privnet that could not read its inputs stays up on purpose -- refusing every verb for
    every session would be worse -- but "stays up" is not "recovers". These pin what the retry has
    to do afterwards, which is everything the first pass did not."""

    async def test_a_read_failure_arms_the_retry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        runtime = _StubRuntime(live={"c1": "s1"})
        async with _Harness(runtime, state_dir=tmp_path) as h:
            await h.setup("s1")

        async def _boom() -> dict[str, str]:
            raise RuntimeError("containerd was unreachable")

        # A second daemon over the same state, whose first inventory read fails.
        async with _Harness(_StubRuntime(live={"c1": "s1"}), state_dir=tmp_path) as h2:
            monkeypatch.setattr(h2.server, "_live_containers", _boom)
            await h2.server.recover()
            assert h2.server._recovery_failed is not None

    async def test_the_retry_adopts_every_live_session_after_a_read_failure(
        self, tmp_path: Path
    ) -> None:
        # The first pass adopted nothing, so there are no per-session marks to work from: the
        # retry must take the whole live set, or it iterates an empty set and leaves the node
        # with every tunnel down and an empty registry.
        runtime = _StubRuntime(live={"c1": "s1"})
        async with _Harness(runtime, state_dir=tmp_path) as h:
            await h.setup("s1")

        async with _Harness(_StubRuntime(live={"c1": "s1"}), state_dir=tmp_path) as h2:
            h2.server._recovery_failed = "containerd was unreachable"
            h2.backend.adopt_calls.clear()
            await h2.server._retry_recovery()
            assert h2.backend.adopt_calls == ["s1"]

    async def test_the_retry_restores_security_so_the_tunnel_is_not_left_dark(
        self, tmp_path: Path
    ) -> None:
        # Adoption holds an encrypted tunnel DOWN. A retry that stopped there "recovered" every
        # session into darkness.
        runtime = _StubRuntime(live={"c1": "s1"})
        async with _Harness(runtime, state_dir=tmp_path) as h:
            await h.setup("s1")

        async with _Harness(_StubRuntime(live={"c1": "s1"}), state_dir=tmp_path) as h2:
            h2.server._recovery_failed = "containerd was unreachable"
            h2.backend.ensure_calls.clear()
            await h2.server._retry_recovery()
            assert [sid for sid, _ in h2.backend.ensure_calls] == ["s1"]

    async def test_a_session_gone_from_the_journal_stops_being_retried(
        self, tmp_path: Path
    ) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            h.server._unrecovered_sessions["ghost"] = "was failing"
            await h.server._retry_recovery()
            assert "ghost" not in h.server._unrecovered_sessions


class TestWithdrawingASession:
    """The agent whose last kernel of a session leaves while a co-located agent still has one.
    The devices are the node's and stay; this node's CLAIM on the session must not."""

    async def test_the_journal_record_goes_with_it(self, tmp_path: Path) -> None:
        # Left behind, the next restart reads it and re-adopts a session this node gave up --
        # taking its ESP pair claim and its watchdog responsibility back with it.
        async with _Harness(_StubRuntime(live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            assert "s1" in await h.journal.sessions()
            resp = await h.client().call(PrivNetRequest(PrivNetOp.WITHDRAW_SESSION, "s1"))
            assert resp.ok
            assert "s1" not in await h.journal.sessions()

    async def test_the_backend_is_told_to_let_go(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            await h.client().call(PrivNetRequest(PrivNetOp.WITHDRAW_SESSION, "s1"))
            assert h.backend.withdraw_calls == ["s1"]
            assert h.backend.teardown_calls == [], "withdrawal must not tear the data plane down"

    async def test_withdrawing_an_unknown_session_is_harmless(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            resp = await h.client().call(PrivNetRequest(PrivNetOp.WITHDRAW_SESSION, "nope"))
            assert resp.ok
            assert h.backend.withdraw_calls == []


class TestReclaimingIsRetriedToo:
    """Reclaiming is the only pass that gives back a dead container's address and DNAT rules, and a
    dead session's devices and node-local subnet block. Nothing asks for them again -- the
    container and the session are gone -- so a failure that is only logged is a permanent leak."""

    async def test_a_failed_container_reclaim_is_marked_and_retried(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as first:
            await first.setup("s1")
            await first.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "s1", container_id="c1")
            )

        # c1 died while we were down, and the first reclaim of it fails.
        forwarder = _RecordingForwarder(remove_failures=1)
        async with _Harness(
            _StubRuntime(live={"c2": "s1"}), state_dir=tmp_path, forwarder=forwarder
        ) as restarted:
            assert restarted.server._unreclaimed_containers.keys() == {"c1"}
            assert "c1" in await restarted.journal.attachments()
            await restarted.server._retry_recovery()
            assert restarted.server._unreclaimed_containers == {}
            assert "c1" not in await restarted.journal.attachments()

    async def test_a_failed_dead_session_reclaim_is_marked_and_retried(
        self, tmp_path: Path
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as first:
            await first.setup("s1")

        async with _Harness(_StubRuntime(), state_dir=tmp_path, teardown_failures=1) as restarted:
            assert restarted.server._unreclaimed_sessions.keys() == {"s1"}
            assert "s1" in await restarted.journal.sessions()
            await restarted.server._retry_recovery()
            assert restarted.server._unreclaimed_sessions == {}
            assert restarted.backend.teardown_calls == ["s1"]
            assert "s1" not in await restarted.journal.sessions()

    async def test_a_session_deferred_behind_a_live_vni_is_reclaimed_once_that_vni_is_free(
        self, tmp_path: Path
    ) -> None:
        # Deferring is correct -- the devices are named after the VNI and belong to the live
        # session -- but only the timer makes "later" arrive. Without the marker the loop is never
        # armed, and the block waits for the next restart of this process.
        vxlan = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}
        async with _Harness(
            _StubRuntime(pid=4242, live={"c-old": "dead"}), state_dir=tmp_path
        ) as first:
            await first.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "dead", network_config=dict(vxlan))
            )
            await _hand_the_vni_back(first, "dead", vxlan)
            await first.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "live", network_config=dict(vxlan))
            )
            await first.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "live", container_id="c-new")
            )

        runtime = _StubRuntime(live={"c-new": "live"})
        async with _Harness(runtime, state_dir=tmp_path) as restarted:
            assert restarted.server._unreclaimed_sessions.keys() == {"dead"}
            assert "dead" not in restarted.backend.teardown_calls

            # "live" ends the ordinary way; its VNI is free now.
            await restarted.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "live"))
            runtime._live.clear()
            await restarted.server._retry_recovery()
            assert "dead" in restarted.backend.teardown_calls
            assert restarted.server._unreclaimed_sessions == {}

    async def test_a_reclaim_failure_arms_the_retry_timer(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as first:
            await first.setup("s1")

        async with _Harness(_StubRuntime(), state_dir=tmp_path, teardown_failures=1) as restarted:
            task = restarted.server._recovery_retry_task
            assert task is not None and not task.done()

    async def test_a_reclaim_that_something_else_finished_stops_being_retried(
        self, tmp_path: Path
    ) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            h.server._unreclaimed_containers["ghost-c"] = "was failing"
            h.server._unreclaimed_sessions["ghost-s"] = "was failing"
            await h.server._retry_recovery()
            assert h.server._unreclaimed_containers == {}
            assert h.server._unreclaimed_sessions == {}


class TestTheAgentFacingProxy:
    """The facade the agent's coordinator drives. Every verb here crosses the process boundary,
    so what it does with a failure is what the agent believes about the host."""

    def _proxy(self, calls: list[PrivNetRequest], *, fail: bool = False) -> PrivNetBackendProxy:
        class _Client:
            async def call(self, request: PrivNetRequest) -> PrivNetResponse:
                calls.append(request)
                if fail:
                    raise PrivNetClientError("privnet said no")
                return PrivNetResponse(ok=True)

        return PrivNetBackendProxy({}, {}, client=cast(Any, _Client()))

    def _meta(self) -> SessionNetMeta:
        return SessionNetMeta(
            session_id="s1",
            subnet="10.128.5.0/24",
            backend=NetworkBackendKind.VXLAN,
            mtu=1412,
            vni=4138,
            vxlan_port=4789,
            encryption_key="ab" * 32,
        )

    async def test_adoption_declares_the_session_to_this_agents_privnet(self) -> None:
        # "The privnet" is per agent. When a second agent on the same host joins a session the
        # first one's privnet built, its own privnet has no record of it and refuses every later
        # attach with "attach before setup" -- so adoption has to say so, not return quietly.
        #
        # ADOPT, never SETUP: setup deletes the session's devices before rebuilding them, so the
        # containers already running on them lose their network -- the ones this call is for.
        calls: list[PrivNetRequest] = []
        await self._proxy(calls).adopt_session_network(
            self._meta(), Member(agent_id="a1", host_ip="10.0.0.1", vtep_ip="10.0.0.1")
        )
        assert [c.op for c in calls] == [PrivNetOp.ADOPT_SESSION]
        assert calls[0].network_config == {
            "backend": "vxlan",
            "subnet": "10.128.5.0/24",
            "vni": 4138,
            "mtu": 1412,
            "vxlan_port": 4789,
            "encryption_key": "ab" * 32,
        }

    async def test_a_failed_withdrawal_is_not_reported_as_done(self) -> None:
        # The devices stay either way; what the withdrawal removes is this node's CLAIM -- the
        # journal record, the ESP pair claim, the watchdog responsibility. Reporting it as done
        # makes the caller drop the member key and the manager believe the VNI is free.
        calls: list[PrivNetRequest] = []
        with pytest.raises(PrivNetClientError):
            await self._proxy(calls, fail=True).withdraw_session_network("s1")
        assert [c.op for c in calls] == [PrivNetOp.WITHDRAW_SESSION]

    async def test_a_successful_withdrawal_names_the_session(self) -> None:
        calls: list[PrivNetRequest] = []
        await self._proxy(calls).withdraw_session_network("s1")
        assert [(c.op, c.session_id) for c in calls] == [(PrivNetOp.WITHDRAW_SESSION, "s1")]


class TestAdoptingALiveSession:
    """A session whose devices are already up and carrying containers. Whatever this does, it must
    not be what setup does: setup deletes the bridge, the VXLAN device and the LOCAL bridge before
    rebuilding them, and the surviving veths are not re-enslaved to the new bridge -- the kernels
    keep running with no network at all."""

    _CONFIG = {"backend": "bridge", "subnet": "172.30.9.0/24"}

    async def test_it_does_not_rebuild_the_data_plane(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            h.backend.lifecycle_calls.clear()
            resp = await h.client().call(
                PrivNetRequest(PrivNetOp.ADOPT_SESSION, "s1", network_config=dict(self._CONFIG))
            )
            assert resp.ok, resp.error
            assert h.backend.lifecycle_calls == [], "the session was already ours; nothing to do"

    async def test_it_keeps_the_attachment_plans_a_detach_needs(self, tmp_path: Path) -> None:
        # Rebuilding the entry loses them, and every later detach is derived from them -- the
        # container's veth, its LOCAL address and its DNAT rules would all be left behind.
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            await h.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "s1", container_id="c1")
            )
            await h.client().call(
                PrivNetRequest(PrivNetOp.ADOPT_SESSION, "s1", network_config=dict(self._CONFIG))
            )
            assert "c1" in h.server._sessions["s1"].attached

    async def test_a_privnet_that_never_saw_it_takes_it_over_without_setup(
        self, tmp_path: Path
    ) -> None:
        # The second agent on the host: its own privnet has no record of a session the first one's
        # built, and its kernels are about to join those very devices.
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as first:
            await first.setup("s1")

        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path / "second"
        ) as second:
            resp = await second.client().call(
                PrivNetRequest(PrivNetOp.ADOPT_SESSION, "s1", network_config=dict(self._CONFIG))
            )
            assert resp.ok, resp.error
            assert second.backend.adopt_calls == ["s1"]
            assert second.backend.setup_calls == [], "setup would delete the live devices"
            assert "s1" in second.server._sessions
            assert "s1" in await second.journal.sessions(), "or the next restart forgets it"

    async def test_a_later_attach_is_served(self, tmp_path: Path) -> None:
        # The point of adopting at all: without it the privnet refuses with "attach before setup".
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as first:
            await first.setup("s1")

        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path / "second"
        ) as second:
            await second.client().call(
                PrivNetRequest(PrivNetOp.ADOPT_SESSION, "s1", network_config=dict(self._CONFIG))
            )
            resp = await second.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "s1", container_id="c2")
            )
            assert resp.ok, resp.error

    async def test_redeclaring_a_live_session_differently_is_refused(self, tmp_path: Path) -> None:
        # An agent is not trusted to say what an existing session is. Accepting this would let one
        # agent's declaration silently change the subnet or the key of another's running session.
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            with pytest.raises(PrivNetClientError, match="different network configuration"):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.ADOPT_SESSION,
                        "s1",
                        network_config={"backend": "bridge", "subnet": "172.30.55.0/24"},
                    )
                )

    async def test_a_journalled_session_cannot_be_adopted_under_a_new_declaration(
        self, tmp_path: Path
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as first:
            await first.setup("s1")

        # A restart that could not re-adopt (no live container), so the journal still holds it.
        async with _Harness(_StubRuntime(), state_dir=tmp_path, teardown_failures=99) as h:
            with pytest.raises(PrivNetClientError, match="different network configuration"):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.ADOPT_SESSION,
                        "s1",
                        network_config={"backend": "bridge", "subnet": "172.30.55.0/24"},
                    )
                )


class TestAnAgentCannotNameAnotherSessionsVni:
    """The trust boundary the privnet exists for, applied to the declaration itself. Setup deletes
    `baivx<vni>`, `baibr<vni>` and the LOCAL bridge before rebuilding them, and the conflict check
    treats every `baivx*` as ours -- so a declaration naming a live session's VNI used to cut its
    containers off the network with no error anywhere."""

    _VXLAN = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}

    async def test_a_second_session_on_a_live_vni_is_refused(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            h.backend.lifecycle_calls.clear()
            with pytest.raises(PrivNetClientError, match="already held by session s1"):
                await h.client().call(
                    PrivNetRequest(
                        PrivNetOp.SETUP_SESSION, "evil", network_config=dict(self._VXLAN)
                    )
                )
            assert h.backend.lifecycle_calls == [], "nothing was built, so nothing was deleted"

    async def test_another_agents_live_vni_is_refused_too(self, tmp_path: Path) -> None:
        # The whole point of putting the binding on disk: two agents on one host each have their
        # own memory, and neither can see the other's sessions.
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(_StubRuntime(), state_dir=tmp_path / "b", agent_id="i-b") as b:
                with pytest.raises(PrivNetClientError, match="already held by session s1"):
                    await b.client().call(
                        PrivNetRequest(
                            PrivNetOp.SETUP_SESSION, "evil", network_config=dict(self._VXLAN)
                        )
                    )

    async def test_redeclaring_a_live_session_differently_is_refused(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(_StubRuntime(), state_dir=tmp_path / "b", agent_id="i-b") as b:
                with pytest.raises(PrivNetClientError, match="different network configuration"):
                    await b.client().call(
                        PrivNetRequest(
                            PrivNetOp.SETUP_SESSION,
                            "s1",
                            network_config={**self._VXLAN, "subnet": "10.128.99.0/24"},
                        )
                    )

    async def test_a_co_located_agent_setting_up_the_same_session_adopts_it(
        self, tmp_path: Path
    ) -> None:
        # Not a conflict and not a rebuild: the devices are up and carrying the first agent's
        # kernels, so the second agent takes them over.
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c1": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                resp = await b.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                assert resp.ok, resp.error
                assert b.backend.setup_calls == [], "setup would delete the live devices"
                assert b.backend.adopt_calls == ["s1"]

    async def test_the_vni_is_free_again_once_the_session_is_torn_down(
        self, tmp_path: Path
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            resp = await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s2", network_config=dict(self._VXLAN))
            )
            assert resp.ok, resp.error

    async def test_withdrawing_releases_only_this_agents_hold(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c1": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                await b.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                await b.client().call(PrivNetRequest(PrivNetOp.WITHDRAW_SESSION, "s1"))
                # a still has it, so the VNI is not free for anybody else.
                with pytest.raises(PrivNetClientError, match="already held by session s1"):
                    await b.client().call(
                        PrivNetRequest(
                            PrivNetOp.SETUP_SESSION, "other", network_config=dict(self._VXLAN)
                        )
                    )

    async def test_a_binding_left_by_a_crash_does_not_block_the_vni_forever(
        self, tmp_path: Path
    ) -> None:
        # The privnet died between binding the VNI and journalling anything, so its restart finds
        # a binding with no session behind it. Without the prune, that VNI is refused to every
        # later session on this node.
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            async with h.vni_registry.binding(4138, "i-test", "ghost", config_digest(self._VXLAN)):
                pass

        async with _Harness(_StubRuntime(), state_dir=tmp_path) as restarted:
            resp = await restarted.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            assert resp.ok, resp.error


class TestTearingDownASharedDataPlane:
    """`baivx*` and `baibr*` are the HOST's devices, and two agents on one host can share a
    session on them. Each agent's locator sees only its own runtime, so "no containers of mine are
    left" says nothing about the other agent's -- the node-wide binding is the only thing that can
    tell the two apart, and it has to be asked BEFORE the delete, not after."""

    _VXLAN = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}

    async def test_the_devices_survive_while_another_agent_holds_the_session(
        self, tmp_path: Path
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c2": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                await b.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                resp = await b.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
                assert resp.ok, resp.error
                assert b.backend.teardown_calls == [], (
                    "the shared bridge and VXLAN device were deleted while a co-located agent"
                    " still had kernels on them"
                )

    async def test_the_leaving_agent_still_gives_up_everything_of_its_own(
        self, tmp_path: Path
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c2": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                await b.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                await b.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
                # A withdrawal in all but name: the ESP pair claim and the watchdog go.
                assert b.backend.withdraw_calls == ["s1"]
                assert "s1" not in b.server._sessions
                assert "s1" not in await b.journal.sessions()

    async def test_the_last_agent_out_does_delete_them(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c2": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                await b.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                await b.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            await a.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            assert a.backend.teardown_calls == ["s1"]

    async def test_a_lone_agent_tears_down_normally(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            assert h.backend.teardown_calls == ["s1"]
            assert "s1" not in await h.journal.sessions()

    async def test_an_unanswerable_registry_refuses_rather_than_deletes(
        self, tmp_path: Path
    ) -> None:
        # Not knowing whether anyone else is on the devices is not permission to delete them. The
        # RPC fails so the agent retries, instead of reporting a teardown that took someone's
        # network with it.
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            h.server._vni_registry = VniRegistry(tmp_path / "gone" / "vni" / "unreachable")
            (tmp_path / "gone").write_text("not a directory")
            with pytest.raises(PrivNetClientError):
                await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            assert h.backend.teardown_calls == []
            assert "s1" in await h.journal.sessions(), "still ours, so still journalled"

    async def test_a_dead_session_is_not_reclaimed_out_from_under_another_agent(
        self, tmp_path: Path
    ) -> None:
        # The reclaim pass runs precisely because THIS node's runtime shows no containers -- which
        # is what a co-located agent's containers look like from here.
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c2": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                await b.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )

            # b restarts with no containers of its own: to it, s1 is a dead session.
            async with _Harness(
                _StubRuntime(), state_dir=tmp_path / "b", agent_id="i-b"
            ) as restarted:
                assert restarted.backend.teardown_calls == []
                assert "s1" not in await restarted.journal.sessions(), (
                    "it is no longer this agent's, so its record goes -- the devices do not"
                )


class TestRecoveryDoesNotAdoptAVniItCouldNotBind:
    """An encrypted adopt holds the VXLAN of that name DOWN, and a reclaim deletes it. Both act on
    the device by its name, so doing either for a VNI the registry says belongs to something else
    reaches straight into that session's data plane."""

    _VXLAN = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}

    async def test_a_conflicting_live_session_is_left_alone(self, tmp_path: Path) -> None:
        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path, agent_id="i-a"
        ) as first:
            await first.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            await _hand_the_vni_back(first, "s1", self._VXLAN, "i-a")

        # Another agent took VNI 4138 for a different session while this one was down.
        squatter = _Harness(_StubRuntime(), state_dir=tmp_path / "other", agent_id="i-other")
        async with squatter.vni_registry.binding(
            4138, "i-other", "other", config_digest(self._VXLAN)
        ) as bound:
            bound.mark_built()

        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path, agent_id="i-a"
        ) as restarted:
            assert restarted.backend.adopt_calls == [], "adopting holds that VXLAN down"
            assert restarted.backend.teardown_calls == [], "reclaiming deletes it"
            assert "s1" in restarted.server._unrecovered_sessions

    async def test_it_is_retried_once_the_conflict_clears(self, tmp_path: Path) -> None:
        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path, agent_id="i-a"
        ) as first:
            await first.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            await _hand_the_vni_back(first, "s1", self._VXLAN, "i-a")

        blocker = _Harness(_StubRuntime(), state_dir=tmp_path / "other", agent_id="i-other")
        async with blocker.vni_registry.binding(
            4138, "i-other", "other", config_digest(self._VXLAN)
        ) as bound:
            bound.mark_built()

        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path, agent_id="i-a"
        ) as restarted:
            assert restarted.backend.adopt_calls == []
            async with blocker.vni_registry.releasing(
                4138, "i-other", "other", config_digest(self._VXLAN)
            ):
                pass
            await restarted.server._retry_recovery()
            assert restarted.backend.adopt_calls == ["s1"]
            assert restarted.server._unrecovered_sessions == {}


class TestABuildTheRegistryWillNotVouchFor:
    """The devices exist and the store will not say so. Left there, a co-located agent's setup of
    this same session reads "not built", takes the build path, and deletes the devices out from
    under whatever is already on them."""

    _VXLAN = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}

    async def test_setup_gives_the_devices_back_and_fails(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            registry = h.server._vni_registry

            class _WontMark(VniRegistry):
                @override
                @contextlib.asynccontextmanager
                async def binding(
                    self, vni: int, owner: str, session_id: str, digest: str
                ) -> AsyncIterator[Binding]:
                    async with registry.binding(vni, owner, session_id, digest) as bound:
                        yield replace(bound, _claims=None)  # every mark_built() now fails

            h.server._vni_registry = _WontMark(tmp_path / "vni")
            with pytest.raises(PrivNetClientError, match="could not be recorded as built"):
                await h.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
            assert h.backend.teardown_calls == ["s1"], "the devices were left for someone to delete"
            assert "s1" not in await h.journal.sessions()
            assert "s1" not in h.server._sessions

    async def test_the_reservation_it_leaves_is_cleared_by_the_next_startup(
        self, tmp_path: Path
    ) -> None:
        # A store that will not take the "built" write will not take the removal either, so the
        # reservation stays -- which refuses the VNI rather than handing it out over devices that
        # may not be gone. The startup prune is what gives it back, having found no session
        # behind it.
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            registry = h.server._vni_registry

            class _WontMark(VniRegistry):
                @override
                @contextlib.asynccontextmanager
                async def binding(
                    self, vni: int, owner: str, session_id: str, digest: str
                ) -> AsyncIterator[Binding]:
                    async with registry.binding(vni, owner, session_id, digest) as bound:
                        yield replace(bound, _claims=None)

            h.server._vni_registry = _WontMark(tmp_path / "vni")
            with contextlib.suppress(PrivNetClientError):
                await h.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
            h.server._vni_registry = registry
            with pytest.raises(PrivNetClientError, match="already held by session s1"):
                await h.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s2", network_config=dict(self._VXLAN))
                )

        async with _Harness(_StubRuntime(), state_dir=tmp_path) as restarted:
            resp = await restarted.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s2", network_config=dict(self._VXLAN))
            )
            assert resp.ok, resp.error


class TestAnAnonymousPrivnetOwnsNothing:
    def test_the_server_refuses_to_start_without_an_agent_id(self, tmp_path: Path) -> None:
        # The agent id is the owner half of every node-wide claim. An empty one writes claims no
        # reader can attribute, and a VNI whose holders cannot be counted reads as free.
        with pytest.raises(ValueError, match="non-empty agent id"):
            _Harness(_StubRuntime(), state_dir=tmp_path, agent_id="  ")


class TestAFailedTeardownKeepsTheVni:
    """The claim is committed when the teardown returns, not before it runs. A device that would
    not go down is still carrying traffic, and a VNI already released is one the next session on
    this node is free to build over."""

    _VXLAN = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}

    async def test_the_next_session_cannot_take_it(self, tmp_path: Path) -> None:
        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path, teardown_failures=1
        ) as h:
            await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            with pytest.raises(PrivNetClientError):
                await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            with pytest.raises(PrivNetClientError, match="already held by session s1"):
                await h.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s2", network_config=dict(self._VXLAN))
                )

    async def test_the_retry_completes_it(self, tmp_path: Path) -> None:
        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path, teardown_failures=1
        ) as h:
            await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            with contextlib.suppress(PrivNetClientError):
                await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            await h.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            resp = await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s2", network_config=dict(self._VXLAN))
            )
            assert resp.ok, resp.error


class TestAnAdoptionTheRegistryWouldNotVouchFor:
    """The session entry lands before the registry is told the VNI is built. Returning early on
    the entry's mere presence made every retry of that ADOPT a no-op -- leaving the VNI recorded
    as a half-finished build that a co-located privnet may rebuild over these live devices."""

    _VXLAN = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}

    def _wont_mark(self, real: VniRegistry, root: Path) -> VniRegistry:
        class _WontMark(VniRegistry):
            @override
            @contextlib.asynccontextmanager
            async def binding(
                self, vni: int, owner: str, session_id: str, digest: str
            ) -> AsyncIterator[Binding]:
                async with real.binding(vni, owner, session_id, digest) as bound:
                    yield replace(bound, _claims=None)  # every mark_built() now fails

        return _WontMark(root)

    async def test_the_retry_runs_the_adoption_again(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c1": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                real = b.server._vni_registry
                b.server._vni_registry = self._wont_mark(real, tmp_path / "vni")
                with pytest.raises(PrivNetClientError, match="could not record its VNI as"):
                    await b.client().call(
                        PrivNetRequest(
                            PrivNetOp.ADOPT_SESSION, "s1", network_config=dict(self._VXLAN)
                        )
                    )
                assert b.server._sessions["s1"].built is False

                b.server._vni_registry = real
                resp = await b.client().call(
                    PrivNetRequest(PrivNetOp.ADOPT_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                assert resp.ok, resp.error
                assert b.server._sessions["s1"].built is True

    async def test_a_settled_adoption_is_still_idempotent(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c1": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                await b.client().call(
                    PrivNetRequest(PrivNetOp.ADOPT_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                b.backend.adopt_calls.clear()
                await b.client().call(
                    PrivNetRequest(PrivNetOp.ADOPT_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                assert b.backend.adopt_calls == []


class TestASessionRunningWithNoRecordOfIt:
    """A container of a session is on this node and this privnet journalled nothing about it. It
    cannot be adopted (the record is what says what it IS) and must not be reclaimed (nothing here
    names its devices) -- so the node must not report itself recovered over it."""

    async def test_the_node_reports_itself_unrecovered(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(live={"c1": "ghost"}), state_dir=tmp_path) as h:
            assert "ghost" in h.server._unrecovered_sessions

    async def test_a_journalled_session_does_not_count(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path
        ) as restarted:
            assert restarted.server._unrecovered_sessions == {}


class TestTheRetryCannotRunThroughARequest:
    """The retry reads a snapshot of the journal and the runtime and then acts on it -- pruning
    node-wide claims, reclaiming dead sessions. A SETUP that lands in the middle is absent from
    that snapshot, and the prune then deletes the VNI claim of a session built moments ago."""

    _VXLAN = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}

    async def test_a_setup_during_a_retry_keeps_its_claim(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            # A retry whose snapshot is taken before the setup and whose prune runs after it.
            reached = asyncio.Event()
            release = asyncio.Event()
            original = h.server._journal.sessions

            async def _slow_sessions() -> dict[str, dict[str, Any]]:
                out = await original()
                reached.set()
                await release.wait()
                return out

            monkeypatch.setattr(h.server._journal, "sessions", _slow_sessions)
            retry = asyncio.create_task(h.server._retry_recovery())
            await reached.wait()
            monkeypatch.setattr(h.server._journal, "sessions", original)

            setup = asyncio.create_task(
                h.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
            )
            await asyncio.sleep(0.05)
            assert not setup.done(), "the request ran while the retry held the barrier"
            release.set()
            await retry
            assert (await setup).ok
            assert {h.session_id for h in await h.vni_registry.holders(4138)} == {"s1"}

    async def test_a_retry_waits_for_a_request_in_flight(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            await h.server._mutation_lock.acquire()
            try:
                retry = asyncio.create_task(h.server._retry_recovery())
                await asyncio.sleep(0.05)
                assert not retry.done()
            finally:
                h.server._mutation_lock.release()
            await retry

    async def test_a_readiness_query_does_not_wait_on_it(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            await h.server._mutation_lock.acquire()
            try:
                resp = await asyncio.wait_for(
                    h.client().call(PrivNetRequest(PrivNetOp.RECOVERY_STATUS, "status")), 2
                )
                assert resp.ok
            finally:
                h.server._mutation_lock.release()


class TestATeardownOverAnUnreadableJournal:
    """After a restart there is no in-memory entry, so the journal is the only thing that says
    what the session is. A read that failed used to become "no record", and no record is what
    tells teardown there is nothing to release and nothing to remove."""

    async def test_it_is_refused_rather_than_reported_done(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")

        (tmp_path / "journal" / "sessions" / "damaged").write_text("{not json")
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as restarted:
            with pytest.raises(PrivNetClientError):
                await restarted.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
            assert "s1" in {p.name for p in (tmp_path / "journal" / "sessions").iterdir()}, (
                "the record went while the devices stayed"
            )


class TestTheNodeSaysWhatItCouldNotRecover:
    """A privnet that cannot take charge of something already running on it looks healthy from
    every other angle, and the manager goes on scheduling onto it."""

    async def test_an_orphaned_live_session_is_reported(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(live={"c1": "ghost"}), state_dir=tmp_path) as h:
            resp = await h.client().call(PrivNetRequest(PrivNetOp.RECOVERY_STATUS, "status"))
            assert resp.ok
            assert "privnet:session:ghost" in (resp.problems or {})

    async def test_a_healthy_node_reports_nothing(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            resp = await h.client().call(PrivNetRequest(PrivNetOp.RECOVERY_STATUS, "status"))
            assert resp.problems == {}

    async def test_the_mark_survives_the_next_retry(self, tmp_path: Path) -> None:
        # It used to be dropped for not being journalled -- which is the whole point of it.
        async with _Harness(_StubRuntime(live={"c1": "ghost"}), state_dir=tmp_path) as h:
            await h.server._retry_recovery()
            assert "ghost" in h.server._unrecovered_sessions

    async def test_an_orphan_stops_the_prune(self, tmp_path: Path) -> None:
        # The prune's premise is that the journal is the whole list of what this agent owns, and
        # an orphan is exactly a counterexample.
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            async with h.vni_registry.binding(4999, "i-test", "elsewhere", "deadbeef") as bound:
                bound.mark_built()

        async with _Harness(_StubRuntime(live={"c9": "ghost"}), state_dir=tmp_path) as restarted:
            assert restarted.server._unrecovered_sessions.keys() >= {"ghost"}
            assert await restarted.vni_registry.holders(4999)


class TestAWithdrawalWhoseClaimWouldNotGo:
    """`releasing` drops the claim when the caller's block RETURNS. Anything that drops this
    node's record of the session therefore belongs after that block, not inside it: done inside,
    a failed unlink leaves the retry with no entry and no journal record, so it returns success
    over a claim that is still there."""

    _VXLAN = {"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4138, "mtu": 1412}

    def _wedge(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Make the VNI claim files refuse to be unlinked, as a full or read-only tree would."""
        original = PairJournal._remove_claim

        def _refuse(journal: PairJournal, held: Any, owner: str, session_id: str) -> bool:
            if held.key.startswith("vni"):
                return False
            return original(journal, held, owner, session_id)

        monkeypatch.setattr(PairJournal, "_remove_claim", _refuse)

    async def test_the_record_survives_so_the_retry_has_something_to_use(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c1": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                await b.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                with monkeypatch.context() as wedged:
                    self._wedge(wedged)
                    with pytest.raises(PrivNetClientError):
                        await b.client().call(PrivNetRequest(PrivNetOp.WITHDRAW_SESSION, "s1"))
                    assert "s1" in b.server._sessions
                    assert "s1" in await b.journal.sessions()

                # And the retry finishes it, because it still has what it needs.
                await b.client().call(PrivNetRequest(PrivNetOp.WITHDRAW_SESSION, "s1"))
                assert "s1" not in b.server._sessions
                assert {h.agent_id for h in await b.vni_registry.holders(4138)} == {"i-test"}

    async def test_a_teardown_that_becomes_a_withdrawal_keeps_it_too(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as a:
            await a.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
            )
            async with _Harness(
                _StubRuntime(pid=4242, live={"c1": "s1"}),
                state_dir=tmp_path / "b",
                agent_id="i-b",
            ) as b:
                await b.client().call(
                    PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._VXLAN))
                )
                with monkeypatch.context() as wedged:
                    self._wedge(wedged)
                    with pytest.raises(PrivNetClientError):
                        await b.client().call(PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1"))
                    assert "s1" in await b.journal.sessions()
                    assert b.backend.teardown_calls == []


class TestTheNodeReportsWhatItCouldNotClose:
    """A tunnel the recovery preflight could not bring down makes `_require_closed` refuse every
    new session on that backend. A node advertising itself ready over one is advertising a lie."""

    async def test_an_unclosed_device_is_a_recovery_problem(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            h.backend.unclosed = frozenset({"baivx4097"})
            resp = await h.client().call(PrivNetRequest(PrivNetOp.RECOVERY_STATUS, "status"))
            assert "privnet:unclosed:baivx4097" in (resp.problems or {})

    async def test_a_node_with_nothing_left_open_reports_nothing(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(), state_dir=tmp_path) as h:
            resp = await h.client().call(PrivNetRequest(PrivNetOp.RECOVERY_STATUS, "status"))
            assert resp.problems == {}


class TestAReclaimReChecksTheRuntime:
    """The node-wide barrier holds off other privnet requests. It holds off nothing in containerd:
    a container can start between the snapshot this pass reads and the moment it deletes that
    container's veth and address."""

    async def test_a_container_that_came_back_is_not_reclaimed(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            await h.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "s1", container_id="c1")
            )

        runtime = _StubRuntime(pid=4242, live={"c1": "s1"})
        async with _Harness(runtime, state_dir=tmp_path, forwarder=_RecordingForwarder()) as h2:
            # Journalled as attached, absent from the snapshot the pass reads, back by the time
            # it acts.
            h2.server._unreclaimed_containers["c1"] = "was failing"
            await h2.server._retry_recovery()
            assert h2.forwarder.removed == []
            assert "c1" in await h2.journal.attachments()

    async def test_a_session_that_came_back_is_not_reclaimed(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")

        runtime = _StubRuntime(pid=4242, live={"c1": "s1"})
        async with _Harness(runtime, state_dir=tmp_path) as h2:
            h2.server._sessions.clear()  # as a failed adoption would leave it
            with pytest.raises(server_mod._ReclaimDeferred):
                await h2.server._reclaim_dead_session(
                    "s1", {"backend": "bridge", "subnet": "172.30.9.0/24"}, ()
                )
            assert h2.backend.teardown_calls == []
            assert "s1" in await h2.journal.sessions()


class TestAPrivnetThatStopsAnswering:
    """The far side runs privileged commands under a node-wide lock. One wedged there answers
    nothing and closes nothing, and the agent used to wait on it forever -- holding whatever it
    was doing for that session with no deadline and no log line."""

    async def test_a_call_gives_up(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        socket_path = _short_socket_path()
        stop = asyncio.Event()

        async def _never_answer(reader: Any, writer: Any) -> None:
            await reader.readline()
            await stop.wait()  # the wedged privnet: reads the request, answers nothing

        server = await asyncio.start_unix_server(_never_answer, path=socket_path)
        monkeypatch.setattr(client_mod, "_CALL_TIMEOUT_SEC", 0.2)
        try:
            with pytest.raises(PrivNetClientError, match="did not answer"):
                await PrivNetClient(socket_path).call(
                    PrivNetRequest(PrivNetOp.TEARDOWN_SESSION, "s1")
                )
        finally:
            stop.set()
            server.close()
            await server.wait_closed()
            with contextlib.suppress(OSError):
                os.unlink(socket_path)

    async def test_a_status_query_that_fails_is_not_a_clean_bill_of_health(
        self, tmp_path: Path
    ) -> None:
        # Empty means "asked, nothing outstanding", and readiness turns that into "may take
        # sessions". A privnet that cannot say must not be read as one with nothing to say.
        problems = await PrivNetClient(str(tmp_path / "gone.sock")).recovery_problems()
        assert "privnet:status" in problems

    async def test_a_daemon_too_old_to_answer_is_told_apart_by_its_version(
        self, tmp_path: Path
    ) -> None:
        socket_path = _short_socket_path()

        async def _old_daemon(reader: Any, writer: Any) -> None:
            await reader.readline()
            writer.write(PrivNetResponse(ok=True).encode())  # no version field
            await writer.drain()
            writer.close()

        server = await asyncio.start_unix_server(_old_daemon, path=socket_path)
        try:
            problems = await PrivNetClient(socket_path).recovery_problems()
            assert "protocol 1" in problems["privnet:status"]
        finally:
            server.close()
            await server.wait_closed()
            with contextlib.suppress(OSError):
                os.unlink(socket_path)


class TestARecheckThatSaysOtherwiseIsDebt:
    """The runtime re-check has three answers, not two. "It is back" and "I could not ask" are
    both reasons NOT to delete -- and treating either as a completed reclaim let the caller clear
    the marker that brings the retry back, leaving a live session journalled, unadopted, its
    tunnel held down, with nothing coming back to it."""

    def _comes_back(
        self, harness: _Harness, monkeypatch: pytest.MonkeyPatch, live: dict[str, str]
    ) -> None:
        """The runtime says nothing is running when the pass reads its snapshot, and says it is
        back by the time the pass acts on it."""
        calls = 0

        async def _changing() -> dict[str, str]:
            nonlocal calls
            calls += 1
            return {} if calls == 1 else dict(live)

        monkeypatch.setattr(harness.server, "_live_containers", _changing)

    async def test_a_container_that_came_back_stays_on_the_books(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            await h.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "s1", container_id="c1")
            )

        # Its first reclaim fails, so the attachment is still journalled and still owed when the
        # retry runs -- which is the only way to reach the re-check at all.
        async with _Harness(
            _StubRuntime(),
            state_dir=tmp_path,
            forwarder=_RecordingForwarder(remove_failures=1),
        ) as h2:
            assert "c1" in h2.server._unreclaimed_containers
            self._comes_back(h2, monkeypatch, {"c1": "s1"})
            await h2.server._retry_recovery()
            assert "c1" in h2.server._unreclaimed_containers
            assert h2.forwarder.removed == [], "it was reclaimed while it was running again"

    async def test_a_runtime_that_cannot_be_asked_stays_on_the_books(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")
            await h.client().call(
                PrivNetRequest(PrivNetOp.ATTACH_CONTAINER, "s1", container_id="c1")
            )

        async with _Harness(
            _StubRuntime(),
            state_dir=tmp_path,
            forwarder=_RecordingForwarder(remove_failures=1),
        ) as h2:
            calls = 0

            async def _fails_the_second_time() -> dict[str, str]:
                nonlocal calls
                calls += 1
                if calls > 1:
                    raise RuntimeError("containerd went away")
                return {}

            monkeypatch.setattr(h2.server, "_live_containers", _fails_the_second_time)
            await h2.server._retry_recovery()
            assert "c1" in h2.server._unreclaimed_containers

    async def test_a_session_that_came_back_is_queued_for_adoption(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.setup("s1")

        # Its first reclaim fails, so it is still journalled and still owed when the retry runs.
        async with _Harness(_StubRuntime(), state_dir=tmp_path, teardown_failures=1) as h2:
            assert "s1" in h2.server._unreclaimed_sessions
            h2.backend.teardown_calls.clear()
            self._comes_back(h2, monkeypatch, {"c1": "s1"})
            await h2.server._retry_recovery()
            assert "s1" in h2.server._unrecovered_sessions, "nothing will ever adopt it"
            assert h2.backend.teardown_calls == [], "it was reclaimed while it was running again"


class TestASecurityRestoreThatFailed:
    """Adoption holds an encrypted tunnel DOWN and the restore is what raises it again. Only
    logged, the session stayed dark for the life of the process: the node reported itself
    recovered, the retry timer never started, and nothing else asks."""

    _ENC = {
        "backend": "vxlan",
        "subnet": "10.128.5.0/24",
        "vni": 4138,
        "mtu": 1412,
        "encryption_key": "ab" * 32,
    }

    async def _set_up_with_a_peer(self, tmp_path: Path) -> None:
        async with _Harness(_StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path) as h:
            await h.client().call(
                PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config=dict(self._ENC))
            )
            # A journalled peer, or the restore declines before it starts: an unknown peer set is
            # the one case it will not reopen a tunnel for.
            await h.client().call(PrivNetRequest(PrivNetOp.ADD_PEER, "s1", vtep_ip="10.0.0.2"))

    async def test_it_becomes_recovery_debt(self, tmp_path: Path) -> None:
        await self._set_up_with_a_peer(tmp_path)

        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}), state_dir=tmp_path
        ) as restarted:
            pass  # a clean restart: nothing outstanding
        assert restarted.server._unrecovered_sessions == {}

        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}),
            state_dir=tmp_path,
            security_failures=1,
        ) as broken:
            assert "s1" in broken.server._unrecovered_sessions
            assert "protection was not restored" in broken.server._unrecovered_sessions["s1"]

    async def test_the_timer_is_armed_for_it(self, tmp_path: Path) -> None:
        await self._set_up_with_a_peer(tmp_path)

        async with _Harness(
            _StubRuntime(pid=4242, live={"c1": "s1"}),
            state_dir=tmp_path,
            security_failures=1,
        ) as broken:
            task = broken.server._recovery_retry_task
            assert task is not None and not task.done()
            # And the retry raises the tunnel once the restore works.
            await broken.server._retry_recovery()
            assert broken.server._unrecovered_sessions == {}
            assert "s1" in [sid for sid, _ in broken.backend.ensure_calls]


class TestAnAnswerThatCannotBeParsed:
    """A truncated line (the daemon died mid-answer) and a corrupt frame both mean this node
    cannot say what it has not recovered. Reading either as "nothing to report" is the same
    fail-open as an empty answer."""

    async def _serving(self, reply: bytes) -> tuple[asyncio.AbstractServer, str]:
        socket_path = _short_socket_path()

        async def _handler(reader: Any, writer: Any) -> None:
            await reader.readline()
            writer.write(reply)
            await writer.drain()
            writer.close()

        return await asyncio.start_unix_server(_handler, path=socket_path), socket_path

    async def test_a_truncated_answer_is_a_problem(self) -> None:
        server, socket_path = await self._serving(b"")
        try:
            problems = await PrivNetClient(socket_path).recovery_problems()
            assert "privnet:status" in problems
        finally:
            server.close()
            await server.wait_closed()
            with contextlib.suppress(OSError):
                os.unlink(socket_path)

    async def test_a_corrupt_frame_is_a_problem(self) -> None:
        server, socket_path = await self._serving(b"{not json\n")
        try:
            problems = await PrivNetClient(socket_path).recovery_problems()
            assert "privnet:status" in problems
        finally:
            server.close()
            await server.wait_closed()
            with contextlib.suppress(OSError):
                os.unlink(socket_path)
