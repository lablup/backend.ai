"""Integration tests for the privileged network helper's RPC layer (BEP-1058).

These exercise the real client<->server round trip over a unix socket in-process (no
privileges required): peer auth, protocol framing, input policy, and semantic dispatch
to a stub backend. The privileged veth/netns execution is covered by the native attacher
tests and requires a real container namespace, so it is out of scope here.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, cast

import pytest

from ai.backend.agent.network.helper.client import (
    HelperClient,
    HelperClientError,
    HelperProvisioner,
)
from ai.backend.agent.network.helper.policy import (
    PolicyViolation,
    validate_network_config,
    validate_overlay_ip,
)
from ai.backend.agent.network.helper.protocol import HelperOp, HelperRequest, HelperResponse
from ai.backend.agent.network.helper.server import NetworkHelperServer
from ai.backend.common.network.types import EndpointPlan, NetworkBackendKind, SessionNetMeta


class _StubBackend:
    """Records the semantic calls the server dispatches to a backend."""

    def __init__(self) -> None:
        self.setup_calls: list[str] = []
        self.teardown_calls: list[str] = []
        self.peers: list[tuple[str, str, str | None]] = []  # (op, session_id, vtep_ip)
        self.endpoints: list[tuple[str, str, str, str, str]] = []  # (op, sid, ip, mac, vtep)
        self.attach_kernel_configs: list[Any] = []  # kernel_config each attach_endpoint received

    async def setup_session_network(self, meta: Any, self_member: Any) -> None:
        self.setup_calls.append(meta.session_id)

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
        return EndpointPlan(attachments=[])


class _StubRuntime:
    def __init__(self, pid: int | None = None) -> None:
        self._pid = pid

    async def open(self) -> None:
        pass

    async def container_pid(self, container_id: str) -> int | None:
        return self._pid


async def _noop_cni(command: str, **kwargs: Any) -> dict[str, Any] | None:
    return {}


def _short_socket_path() -> str:
    # Unix socket paths are capped near 108 bytes; keep it short and unique per test process.
    return f"/tmp/bai-nh-test-{os.getpid()}.sock"


class _Harness:
    def __init__(self, runtime: _StubRuntime | None = None) -> None:
        self.backend = _StubBackend()
        self.server = NetworkHelperServer(
            socket_path=_short_socket_path(),
            allowed_uid=os.getuid(),
            agent_id="i-test",
            host_ip="127.0.0.1",
            runtime=cast(Any, runtime or _StubRuntime()),
            cni_runner=_noop_cni,
            backends=cast(Any, {"bridge": self.backend, "vxlan": self.backend}),
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

    def client(self) -> HelperClient:
        return HelperClient(self.server._socket_path)


class TestProtocol:
    def test_request_roundtrip(self) -> None:
        req = HelperRequest(HelperOp.SETUP_SESSION, "s1", network_config={"backend": "bridge"})
        assert HelperRequest.decode(req.encode()) == req

    def test_response_roundtrip(self) -> None:
        resp = HelperResponse(ok=True, assigned={"local": "172.30.0.3"})
        assert HelperResponse.decode(resp.encode()) == resp


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


class TestHelperRpc:
    async def test_setup_dispatches_to_backend(self) -> None:
        async with _Harness() as h:
            resp = await h.client().call(
                HelperRequest(
                    HelperOp.SETUP_SESSION,
                    "sess-1",
                    network_config={"backend": "bridge", "subnet": "172.30.1.0/24"},
                )
            )
            assert resp.ok
            assert h.backend.setup_calls == ["sess-1"]

    async def test_teardown_dispatches_to_backend(self) -> None:
        async with _Harness() as h:
            await h.client().call(
                HelperRequest(
                    HelperOp.SETUP_SESSION,
                    "sess-2",
                    network_config={"backend": "bridge", "subnet": "172.30.2.0/24"},
                )
            )
            await h.client().call(HelperRequest(HelperOp.TEARDOWN_SESSION, "sess-2"))
            assert h.backend.teardown_calls == ["sess-2"]

    async def test_rejects_unsafe_session_id(self) -> None:
        async with _Harness() as h:
            with pytest.raises(HelperClientError):
                await h.client().call(
                    HelperRequest(
                        HelperOp.SETUP_SESSION,
                        "bad;rm -rf /",
                        network_config={"backend": "bridge"},
                    )
                )
            assert h.backend.setup_calls == []

    async def test_attach_without_running_task_errors(self) -> None:
        async with _Harness(runtime=_StubRuntime(pid=None)) as h:
            await h.client().call(
                HelperRequest(
                    HelperOp.SETUP_SESSION,
                    "sess-3",
                    network_config={"backend": "bridge", "subnet": "172.30.3.0/24"},
                )
            )
            with pytest.raises(HelperClientError):
                await h.client().call(
                    HelperRequest(HelperOp.ATTACH_CONTAINER, "sess-3", container_id="c1")
                )

    async def _setup_vxlan(self, h: _Harness, sid: str) -> None:
        await h.client().call(
            HelperRequest(
                HelperOp.SETUP_SESSION,
                sid,
                network_config={"backend": "vxlan", "subnet": "10.0.0.0/24", "vni": 100},
            )
        )

    async def test_attach_rejects_overlay_ip_outside_session_subnet(self) -> None:
        # An agent-supplied overlay IP is validated against the session subnet BEFORE any netns
        # work; a foreign address is refused and never reaches the backend attach.
        async with _Harness(runtime=_StubRuntime(pid=None)) as h:
            await self._setup_vxlan(h, "sess-ip")
            with pytest.raises(HelperClientError):
                await h.client().call(
                    HelperRequest(
                        HelperOp.ATTACH_CONTAINER, "sess-ip", container_id="c1", ip="10.9.9.9"
                    )
                )
            assert h.backend.attach_kernel_configs == []  # rejected before building the plan

    async def test_add_peer_dispatches_vtep(self) -> None:
        async with _Harness() as h:
            await self._setup_vxlan(h, "sess-p")
            await h.client().call(HelperRequest(HelperOp.ADD_PEER, "sess-p", vtep_ip="192.168.1.9"))
            assert h.backend.peers == [("add", "sess-p", "192.168.1.9")]

    async def test_add_endpoint_dispatches_ip_mac_vtep(self) -> None:
        async with _Harness() as h:
            await self._setup_vxlan(h, "sess-e")
            await h.client().call(
                HelperRequest(
                    HelperOp.ADD_ENDPOINT,
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
            with pytest.raises(HelperClientError):
                await h.client().call(
                    HelperRequest(HelperOp.ADD_PEER, "sess-b", vtep_ip="not-an-ip")
                )
            with pytest.raises(HelperClientError):
                await h.client().call(
                    HelperRequest(
                        HelperOp.ADD_ENDPOINT,
                        "sess-b",
                        ip="10.0.0.5",
                        mac="zz:zz",
                        vtep_ip="192.168.1.9",
                    )
                )
            assert h.backend.peers == [] and h.backend.endpoints == []

    async def test_peer_before_setup_errors(self) -> None:
        async with _Harness() as h:
            with pytest.raises(HelperClientError):
                await h.client().call(
                    HelperRequest(HelperOp.ADD_PEER, "no-session", vtep_ip="192.168.1.9")
                )


class _RecordingClient:
    """Captures the requests HelperProvisioner sends, returning a benign ATTACH response."""

    def __init__(self) -> None:
        self.requests: list[HelperRequest] = []

    async def call(self, req: HelperRequest) -> HelperResponse:
        self.requests.append(req)
        return HelperResponse(ok=True, assigned={})


class TestHelperProvisioner:
    async def test_attach_forwards_manager_overlay_ip(self) -> None:
        # The agent relays the manager-assigned cluster_network_ip to the helper so a multi-node
        # container attaches at its central, disjoint overlay address (the helper re-validates it).
        client = _RecordingClient()
        prov = HelperProvisioner(cast(Any, client))
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
        assert client.requests[0].op is HelperOp.ATTACH_CONTAINER
        assert client.requests[0].ip == "10.0.0.5"

    async def test_attach_sends_no_ip_for_single_node(self) -> None:
        # Single-node sessions have no manager overlay IP; the helper keeps its host-local path.
        client = _RecordingClient()
        prov = HelperProvisioner(cast(Any, client))
        meta = SessionNetMeta(
            session_id="s2",
            subnet="10.0.1.0/24",
            backend=NetworkBackendKind.BRIDGE,
            mtu=1500,
            vni=None,
        )
        await prov.attach(cast(Any, {}), cast(Any, {}), meta=meta, container_id="c2", task_pid=1)
        assert client.requests[0].ip is None
