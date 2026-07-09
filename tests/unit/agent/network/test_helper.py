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

from ai.backend.agent.network.helper.client import HelperClient, HelperClientError
from ai.backend.agent.network.helper.policy import PolicyViolation, validate_network_config
from ai.backend.agent.network.helper.protocol import HelperOp, HelperRequest, HelperResponse
from ai.backend.agent.network.helper.server import NetworkHelperServer
from ai.backend.common.network.types import EndpointPlan


class _StubBackend:
    """Records the semantic calls the server dispatches to a backend."""

    def __init__(self) -> None:
        self.setup_calls: list[str] = []
        self.teardown_calls: list[str] = []

    async def setup_session_network(self, meta: Any, self_member: Any) -> None:
        self.setup_calls.append(meta.session_id)

    async def teardown_session_network(self, session_id: str) -> None:
        self.teardown_calls.append(session_id)

    async def attach_endpoint(
        self, kernel_config: Any, cluster_info: Any, *, meta: Any
    ) -> EndpointPlan:
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
