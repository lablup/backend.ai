"""Integration tests for the privnet daemon's RPC layer (BEP-1062).

These exercise the real client<->server round trip over a unix socket in-process (no
privileges required): peer auth, protocol framing, input policy, and semantic dispatch
to a stub backend. The privileged veth/netns execution is covered by the native attacher
tests and requires a real container namespace, so it is out of scope here.
"""

from __future__ import annotations

import asyncio
import ipaddress
import os
import tempfile
from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.oci import SESSION_ID_LABEL
from ai.backend.agent.containerd.runtime.interface import ContainerInfo
from ai.backend.agent.network.native_attacher import HostLocalIpam
from ai.backend.agent.network.privnet.client import (
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
from ai.backend.common.network.types import (
    AttachKind,
    EndpointPlan,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
)

_LOCAL_SUBNET = "172.30.0.0/26"


class _StubBackend:
    """Records the semantic calls the server dispatches to a backend."""

    def __init__(self) -> None:
        self.setup_calls: list[str] = []
        self.adopt_calls: list[str] = []
        self.teardown_calls: list[str] = []
        self.peers: list[tuple[str, str, str | None]] = []  # (op, session_id, vtep_ip)
        self.endpoints: list[tuple[str, str, str, str, str]] = []  # (op, sid, ip, mac, vtep)
        self.attach_kernel_configs: list[Any] = []  # kernel_config each attach_endpoint received
        self.self_members: list[Any] = []  # the membership the server publishes for this node

    async def setup_session_network(self, meta: Any, self_member: Any) -> None:
        self.setup_calls.append(meta.session_id)
        self.self_members.append(self_member)

    async def adopt_session_network(self, meta: Any, self_member: Any) -> None:
        self.adopt_calls.append(meta.session_id)

    async def teardown_session_network(self, session_id: str) -> None:
        self.teardown_calls.append(session_id)

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


class _StubRuntime:
    """containerd, as the privnet sees it: which containers are still running, and their PIDs."""

    def __init__(self, pid: int | None = None, live: dict[str, str] | None = None) -> None:
        self._pid = pid
        self._live = live or {}  # container_id -> session_id

    async def open(self) -> None:
        pass

    async def container_pid(self, container_id: str) -> int | None:
        return self._pid

    async def list_container_infos(self) -> list[ContainerInfo]:
        return [
            ContainerInfo(
                id=container_id,
                image="img:1",
                labels={SESSION_ID_LABEL: session_id},
                status="running",
            )
            for container_id, session_id in self._live.items()
        ]


def _short_socket_path() -> str:
    # Unix socket paths are capped near 108 bytes; keep it short and unique per test process.
    return f"/tmp/bai-nh-test-{os.getpid()}.sock"


class _RecordingForwarder:
    """Stands in for the real iptables PortForwarder inside the privnet."""

    def __init__(self) -> None:
        self.installed: list[Any] = []
        self.removed: list[str] = []

    async def install(self, forwards: Any) -> None:
        self.installed.extend(forwards)

    async def remove_container(self, container_id: str) -> list[int]:
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
    produce; the TOCTOU logic it guards is the module's own (netns.py), not the attach path's."""

    def open(self, pid: int) -> PinnedNetns:
        return PinnedNetns(netns_fd=-1, pidfd=-1)  # close() tolerates a bad fd

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
    ) -> None:
        self.backend = _StubBackend()
        self.forwarder = forwarder or _RecordingForwarder()
        self._tmp = None if state_dir is not None else tempfile.TemporaryDirectory()
        root = state_dir if state_dir is not None else Path(cast(Any, self._tmp).name)
        self.state_dir = root
        self.journal = PrivNetJournal(root / "journal")
        self.ipam = HostLocalIpam(root / "ipam")
        self.cni = _RecordingCni(self.ipam)
        self.server = PrivNetServer(
            socket_path=_short_socket_path(),
            allowed_uid=os.getuid(),
            agent_id="i-test",
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

    def client(self) -> PrivNetClient:
        return PrivNetClient(self.server._socket_path)


class TestProtocol:
    def test_request_roundtrip(self) -> None:
        req = PrivNetRequest(PrivNetOp.SETUP_SESSION, "s1", network_config={"backend": "bridge"})
        assert PrivNetRequest.decode(req.encode()) == req

    def test_response_roundtrip(self) -> None:
        resp = PrivNetResponse(ok=True, assigned={"local": "172.30.0.3"})
        assert PrivNetResponse.decode(resp.encode()) == resp


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


class TestRestartRecovery:
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
                    PrivNetOp.PUBLISH_PORTS, "s1", container_id="c1", ports=((30001, 8070, None),)
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
            assert restarted.backend.adopt_calls == []
            assert await restarted.journal.sessions() == {}

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


async def _publish(h: _Harness, ports: tuple[tuple[int, int, str | None], ...]) -> None:
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
            await _publish(h, ((30001, 8070, None),))
            assert [(f.host_port, f.container_port) for f in h.forwarder.installed] == [
                (30001, 8070)
            ]
            # the destination is the privnet's own attach record, never anything the agent sent
            assert {f.container_ip for f in h.forwarder.installed} == {_LOCAL_IP}

    async def test_publish_before_attach_is_refused(self) -> None:
        async with _Harness() as h:
            await self._setup(h, attached=False)
            with pytest.raises(PrivNetClientError):
                await _publish(h, ((30001, 8070, None),))
            assert h.forwarder.installed == []

    async def test_a_privileged_host_port_is_refused(self) -> None:
        # the privnet runs as root: publishing on 22 would hijack the node's own sshd
        async with _Harness() as h:
            await self._setup(h)
            with pytest.raises(PrivNetClientError):
                await _publish(h, ((22, 22, None),))
            assert h.forwarder.installed == []

    async def test_a_duplicate_host_port_is_refused(self) -> None:
        async with _Harness() as h:
            await self._setup(h)
            with pytest.raises(PrivNetClientError):
                await _publish(h, ((30001, 8070, None), (30001, 7681, None)))
            assert h.forwarder.installed == []

    async def test_unpublish_returns_the_host_ports_and_needs_no_session(self) -> None:
        async with _Harness() as h:
            await self._setup(h)
            await _publish(h, ((30001, 8070, None), (30002, 7681, None)))
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
            await _publish(h, ((30001, 8070, None),))
            await h.client().call(
                PrivNetRequest(op=PrivNetOp.DETACH_CONTAINER, session_id="s1", container_id="c1")
            )
            assert h.forwarder.removed == ["c1"]

    async def test_list_ports_reports_every_published_rule(self) -> None:
        async with _Harness() as h:
            await self._setup(h)
            await _publish(h, ((30001, 8070, None),))
            resp = await h.client().call(
                PrivNetRequest(op=PrivNetOp.LIST_PORTS, session_id="list-ports")
            )
            assert resp.forwards == (("c1", 30001, _LOCAL_IP, 8070),)
