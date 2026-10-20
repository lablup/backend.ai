from __future__ import annotations

import asyncio
import dataclasses
import datetime
import ipaddress
import socket
import ssl
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from pytest_mock import MockerFixture
from tenacity import TryAgain

from ai.backend.agent.containerd import kernel as kernel_module
from ai.backend.agent.containerd.client import TaskInfo, TaskState
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.profile.base import LaunchPlan, TlsConnectReadiness
from ai.backend.agent.errors.containerd import (
    ContainerdOperationFailed,
    KernelTaskExited,
    KernelVerbNotSupported,
    ReadinessTimeout,
)
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import KernelId, ServicePortProtocols

from .fakes import FakeContainerd


@pytest.fixture
def kernel(
    ownership_data: KernelOwnershipData, launch_plan: LaunchPlan, fake: FakeContainerd
) -> ContainerdKernel:
    return ContainerdKernel(
        ownership_data,
        "net-1",
        MagicMock(),
        1,
        agent_config={},
        resource_spec=MagicMock(),
        service_ports=[],
        environ={},
        data={},
        launch_plan=launch_plan,
        client=fake,
    )


class TestContainerdKernelInit:
    async def test_init_leaves_no_runner(
        self, kernel: ContainerdKernel, mocker: MockerFixture
    ) -> None:
        create = mocker.patch.object(
            ContainerdKernel, "create_code_runner", side_effect=AssertionError("must not run")
        )

        await kernel.init(MagicMock())

        assert kernel.runner is None
        create.assert_not_called()

    async def test_close_is_a_noop(self, kernel: ContainerdKernel) -> None:
        await kernel.close()

    async def test_launch_plan_is_kept(
        self, kernel: ContainerdKernel, launch_plan: LaunchPlan
    ) -> None:
        assert kernel.launch_plan is launch_plan


_RAISING: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = [
    ("create_code_runner", (MagicMock(),), {"client_features": frozenset(), "api_version": 2}),
    ("get_completions", ("", {}), {}),
    ("get_logs", (), {}),
    ("interrupt_kernel", (), {}),
    ("shutdown_service", ("sshd",), {}),
    ("check_duplicate_commit", (KernelId(uuid.uuid4()), "sub"), {}),
    ("commit", (KernelId(uuid.uuid4()), "sub"), {}),
    ("accept_file", ("/home/work/a", b""), {}),
    ("download_file", ("/home/work/a",), {}),
    ("download_single", ("/home/work/a",), {}),
    ("list_files", ("/home/work",), {}),
    ("notify_event", (MagicMock(),), {}),
]


class TestContainerdKernelVerbs:
    @pytest.mark.parametrize(("method", "args", "kwargs"), _RAISING, ids=[r[0] for r in _RAISING])
    async def test_unsupported_verbs_raise(
        self,
        kernel: ContainerdKernel,
        method: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        verb: Callable[..., Awaitable[Any]] = getattr(kernel, method)

        with pytest.raises(KernelVerbNotSupported, match=method):
            await verb(*args, **kwargs)

    async def test_get_service_apps_stub(self, kernel: ContainerdKernel) -> None:
        assert await kernel.get_service_apps() == {"status": "ok", "data": []}

    async def test_start_service_stub(self, kernel: ContainerdKernel) -> None:
        assert await kernel.start_service("jupyter", {}) == {"status": "started"}

    async def test_start_model_service_stub(self, kernel: ContainerdKernel) -> None:
        assert await kernel.start_model_service({}) == {"status": "started"}


def _unused_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class TestCheckStatus:
    """The runc readiness probe: a TCP connect to the REPL-in port of the kernel IP."""

    async def test_listening_port_is_ready(
        self, kernel: ContainerdKernel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        monkeypatch.setattr(kernel_module, "REPL_IN_PORT", server.sockets[0].getsockname()[1])
        kernel.data["kernel_ip"] = "127.0.0.1"

        try:
            assert await kernel.check_status() == {}
        finally:
            server.close()
            await server.wait_closed()

    async def test_refused_connection_asks_the_create_loop_to_retry(
        self, kernel: ContainerdKernel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(kernel_module, "REPL_IN_PORT", _unused_port())
        kernel.data["kernel_ip"] = "127.0.0.1"

        with pytest.raises(TryAgain):
            await kernel.check_status()

    async def test_probes_the_kernel_ip_on_the_repl_port(
        self, kernel: ContainerdKernel, mocker: MockerFixture
    ) -> None:
        connect = mocker.patch("asyncio.open_connection", side_effect=OSError("refused"))
        kernel.data["kernel_ip"] = "172.30.9.2"

        with pytest.raises(TryAgain):
            await kernel.check_status()

        connect.assert_called_once_with("172.30.9.2", 2000)

    async def test_missing_kernel_ip_is_a_typed_error(self, kernel: ContainerdKernel) -> None:
        with pytest.raises(ContainerdOperationFailed, match="kernel IP"):
            await kernel.check_status()


TLS_PORT_NAME = "8080"


def _self_signed_context(tmp_path: Path) -> ssl.SSLContext:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "td.example")])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)
    return context


@pytest.fixture
def tls_context(tmp_path: Path) -> ssl.SSLContext:
    return _self_signed_context(tmp_path)


@pytest.fixture
def tls_kernel(kernel: ContainerdKernel, launch_plan: LaunchPlan) -> ContainerdKernel:
    kernel.launch_plan = dataclasses.replace(
        launch_plan, readiness=TlsConnectReadiness(port_name=TLS_PORT_NAME, timeout_s=60.0)
    )
    kernel.data["published_host"] = "127.0.0.1"
    kernel.data["kernel_ip"] = "172.30.9.2"
    return kernel


def _publish(kernel: ContainerdKernel, host_port: int | None) -> None:
    kernel.service_ports = [
        {
            "name": TLS_PORT_NAME,
            "protocol": ServicePortProtocols.HTTP,
            "container_ports": (8080,),
            "host_ports": (host_port,),
            "is_inference": False,
        }
    ]


@pytest.fixture
def fast_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(kernel_module, "_TLS_PROBE_WINDOW_SEC", 0.3)
    monkeypatch.setattr(kernel_module, "_TLS_RETRY_INTERVAL_SEC", 0.05)


@pytest.fixture
def repl_spy(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("asyncio.open_connection", side_effect=asyncio.open_connection)


class FakeConnect:
    """An asyncio.open_connection stand-in: refuses `refuse` times (None: always), then delegates."""

    def __init__(self, refuse: int | None = None) -> None:
        self.refuse = refuse
        self.calls = 0
        self.real = asyncio.open_connection

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        if self.refuse is None or self.calls <= self.refuse:
            raise ConnectionRefusedError("refused")
        return await self.real(*args, **kwargs)


@pytest.fixture
def refused(monkeypatch: pytest.MonkeyPatch) -> FakeConnect:
    fake = FakeConnect()
    monkeypatch.setattr("asyncio.open_connection", fake)
    return fake


def _handshake_calls(spy: MagicMock) -> list[Any]:
    return [c for c in spy.call_args_list if c.kwargs.get("ssl") is not None]


@pytest.fixture
async def tls_server(tls_context: ssl.SSLContext) -> AsyncIterator[int]:
    server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0, ssl=tls_context)
    try:
        yield int(server.sockets[0].getsockname()[1])
    finally:
        server.close()
        await server.wait_closed()


class TestCheckStatusTls:
    """The TLS readiness probe: a handshake through the DNAT path of the published port."""

    async def test_handshake_with_a_self_signed_cert_is_ready(
        self, tls_kernel: ContainerdKernel, tls_server: int
    ) -> None:
        _publish(tls_kernel, tls_server)

        assert await tls_kernel.check_status() == {}

    async def test_refused_connection_retries_in_the_window_then_asks_to_try_again(
        self, tls_kernel: ContainerdKernel, fast_probe: None, refused: FakeConnect
    ) -> None:
        _publish(tls_kernel, 30001)

        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

        assert refused.calls >= 2

    async def test_server_that_closes_before_the_handshake_asks_to_try_again(
        self, tls_kernel: ContainerdKernel, fast_probe: None
    ) -> None:
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        _publish(tls_kernel, server.sockets[0].getsockname()[1])

        try:
            with pytest.raises(TryAgain):
                await tls_kernel.check_status()
        finally:
            server.close()
            await server.wait_closed()

    async def test_call_after_the_deadline_times_out_without_probing(
        self, tls_kernel: ContainerdKernel, tls_server: int, repl_spy: MagicMock
    ) -> None:
        tls_kernel.launch_plan = dataclasses.replace(
            tls_kernel.launch_plan,
            readiness=TlsConnectReadiness(port_name=TLS_PORT_NAME, timeout_s=0.0),
        )
        _publish(tls_kernel, tls_server)

        with pytest.raises(ReadinessTimeout):
            await tls_kernel.check_status()

        repl_spy.assert_not_called()

    async def test_deadline_passing_during_a_call_times_out(
        self, tls_kernel: ContainerdKernel, monkeypatch: pytest.MonkeyPatch, refused: FakeConnect
    ) -> None:
        monkeypatch.setattr(kernel_module, "_TLS_RETRY_INTERVAL_SEC", 0.02)
        tls_kernel.launch_plan = dataclasses.replace(
            tls_kernel.launch_plan,
            readiness=TlsConnectReadiness(port_name=TLS_PORT_NAME, timeout_s=0.2),
        )
        _publish(tls_kernel, 30001)

        with pytest.raises(ReadinessTimeout):
            await tls_kernel.check_status()

    async def test_call_after_the_deadline_passed_between_calls_does_not_probe(
        self, tls_kernel: ContainerdKernel, fast_probe: None, refused: FakeConnect
    ) -> None:
        _publish(tls_kernel, 30001)
        with pytest.raises(TryAgain):
            await tls_kernel.check_status()
        calls = refused.calls
        tls_kernel._readiness_deadline = asyncio.get_running_loop().time() - 1

        with pytest.raises(ReadinessTimeout):
            await tls_kernel.check_status()

        assert refused.calls == calls

    def test_readiness_timeout_is_not_retried_by_the_create_loop(self) -> None:
        assert not issubclass(ReadinessTimeout, TryAgain)

    async def test_server_starting_late_is_found_by_a_later_call(
        self,
        tls_kernel: ContainerdKernel,
        tls_server: int,
        monkeypatch: pytest.MonkeyPatch,
        fast_probe: None,
    ) -> None:
        fake = FakeConnect(refuse=3)
        monkeypatch.setattr("asyncio.open_connection", fake)
        monkeypatch.setattr(kernel_module, "_TLS_PROBE_WINDOW_SEC", 0.0)
        _publish(tls_kernel, tls_server)
        for _ in range(3):
            with pytest.raises(TryAgain):
                await tls_kernel.check_status()

        assert await tls_kernel.check_status() == {}
        assert fake.calls == 4

    async def test_the_repl_port_is_never_touched(
        self,
        tls_kernel: ContainerdKernel,
        tls_server: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        accepted: list[int] = []
        repl = await asyncio.start_server(lambda r, w: accepted.append(1), "127.0.0.1", 0)
        monkeypatch.setattr(kernel_module, "REPL_IN_PORT", repl.sockets[0].getsockname()[1])
        _publish(tls_kernel, tls_server)

        try:
            assert await tls_kernel.check_status() == {}
            assert await tls_kernel.get_service_apps() == {"status": "ok", "data": []}
            assert await tls_kernel.start_service("jupyter", {}) == {"status": "started"}
            await asyncio.sleep(0.05)
        finally:
            repl.close()
            await repl.wait_closed()
        assert accepted == []

    async def test_probes_the_published_host_and_host_port(
        self, tls_kernel: ContainerdKernel, mocker: MockerFixture, fast_probe: None
    ) -> None:
        connect = mocker.patch("asyncio.open_connection", side_effect=OSError("refused"))
        tls_kernel.data["published_host"] = "10.0.0.5"
        _publish(tls_kernel, 30001)

        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

        assert connect.call_args.args == ("10.0.0.5", 30001)

    async def test_missing_service_port_is_a_typed_error(
        self, tls_kernel: ContainerdKernel
    ) -> None:
        tls_kernel.service_ports = []

        with pytest.raises(ContainerdOperationFailed, match="8080"):
            await tls_kernel.check_status()

    async def test_unpublished_service_port_is_a_typed_error(
        self, tls_kernel: ContainerdKernel
    ) -> None:
        _publish(tls_kernel, None)

        with pytest.raises(ContainerdOperationFailed, match="8080"):
            await tls_kernel.check_status()

    async def test_missing_published_host_is_a_typed_error(
        self, tls_kernel: ContainerdKernel
    ) -> None:
        _publish(tls_kernel, 30001)
        del tls_kernel.data["published_host"]

        with pytest.raises(ContainerdOperationFailed, match="published host"):
            await tls_kernel.check_status()


class TestCheckStatusTlsTaskExit:
    """A task that exited ends the TLS readiness wait instead of running it out."""

    @pytest.fixture
    def running(self, tls_kernel: ContainerdKernel, fake: FakeContainerd) -> str:
        container_id = "kid-1234abcd"
        tls_kernel.data["container_id"] = container_id
        fake.tasks[container_id] = TaskInfo(pid=1000, state=TaskState.RUNNING, exit_status=0)
        _publish(tls_kernel, 30001)
        return container_id

    async def test_running_task_keeps_retrying(
        self, tls_kernel: ContainerdKernel, running: str, fast_probe: None, refused: FakeConnect
    ) -> None:
        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

        assert refused.calls >= 2

    async def test_stopped_task_fails_with_its_exit_status(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        running: str,
        fast_probe: None,
        refused: FakeConnect,
    ) -> None:
        fake.tasks[running] = TaskInfo(pid=1000, state=TaskState.STOPPED, exit_status=137)

        with pytest.raises(KernelTaskExited, match="status 137") as exc_info:
            await tls_kernel.check_status()

        assert not isinstance(exc_info.value, TryAgain)
        assert refused.calls == 1
        assert exc_info.value.exit_status == 137

    async def test_task_exiting_between_calls_ends_the_wait(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        running: str,
        fast_probe: None,
        refused: FakeConnect,
    ) -> None:
        with pytest.raises(TryAgain):
            await tls_kernel.check_status()
        fake.tasks[running] = TaskInfo(pid=1000, state=TaskState.STOPPED, exit_status=1)

        with pytest.raises(KernelTaskExited):
            await tls_kernel.check_status()

    async def test_missing_task_fails(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        running: str,
        fast_probe: None,
        refused: FakeConnect,
    ) -> None:
        del fake.tasks[running]

        with pytest.raises(KernelTaskExited, match="gone"):
            await tls_kernel.check_status()

    async def test_failed_task_lookup_keeps_retrying(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        running: str,
        fast_probe: None,
        refused: FakeConnect,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(fake, "get_task", side_effect=ContainerdOperationFailed("rpc"))

        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

    async def test_unknown_container_id_skips_the_lookup(
        self, tls_kernel: ContainerdKernel, fast_probe: None, refused: FakeConnect
    ) -> None:
        _publish(tls_kernel, 30001)

        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

    async def test_ready_kernel_never_looks_up_the_task(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        tls_server: int,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(fake, "get_task", side_effect=AssertionError("must not run"))
        tls_kernel.data["container_id"] = "kid-1234abcd"
        _publish(tls_kernel, tls_server)

        assert await tls_kernel.check_status() == {}

    @pytest.mark.parametrize("state", [TaskState.CREATED, TaskState.UNKNOWN])
    async def test_not_yet_running_task_keeps_retrying(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        running: str,
        fast_probe: None,
        refused: FakeConnect,
        state: TaskState,
    ) -> None:
        fake.tasks[running] = TaskInfo(pid=0, state=state, exit_status=0)

        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

        assert refused.calls >= 2
