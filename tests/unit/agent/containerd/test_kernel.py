from __future__ import annotations

import asyncio
import datetime
import ipaddress
import ssl
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any, override
from unittest.mock import MagicMock

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from pytest_mock import MockerFixture
from tenacity import AsyncRetrying, TryAgain, retry_if_exception_type, stop_after_attempt, wait_none

from ai.backend.agent.containerd import kernel as kernel_module
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.profile.base import LaunchPlan, TlsConnectReadiness
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.containerd.rpc.types import TaskInfo, TaskState
from ai.backend.agent.errors.containerd import (
    ContainerdOperationFailed,
    KernelTaskExited,
    KernelVerbNotSupported,
    ReadinessTimeout,
)
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import KernelId, ServicePort, ServicePortProtocols

from .fakes import FakeContainerd


@pytest.fixture
def kernel(ownership_data: KernelOwnershipData, fake: FakeContainerd) -> ContainerdKernel:
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
        client=fake,
    )


class _NamingProfile(RuncProfile):
    @override
    def describe_failure(self, exit_status: int | None, error_text: str) -> str | None:
        return f"named {exit_status}"


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

    async def test_check_status_reports_ready(self, kernel: ContainerdKernel) -> None:
        assert await kernel.check_status() == {}

    async def test_service_stubs(self, kernel: ContainerdKernel) -> None:
        assert await kernel.get_service_apps() == {"status": "ok", "data": []}
        assert await kernel.start_service("jupyter", {}) == {"status": "started"}
        assert await kernel.start_model_service({}) == {"status": "started"}


PORT_NAME = "8080"
CONTAINER_ID = "kid-1234abcd"


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
    cert_path, key_path = tmp_path / "cert.pem", tmp_path / "key.pem"
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


def _publish(kernel: ContainerdKernel, host_port: int | None) -> None:
    kernel.service_ports = [
        ServicePort(
            name=PORT_NAME,
            protocol=ServicePortProtocols.HTTP,
            container_ports=(8080,),
            host_ports=(host_port,),
            is_inference=False,
        )
    ]


class RefusingConnect:
    """An asyncio.open_connection stand-in that always refuses."""

    calls: int

    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        raise ConnectionRefusedError("refused")


@pytest.fixture
def tls_kernel(kernel: ContainerdKernel, fake: FakeContainerd) -> ContainerdKernel:
    kernel.launch_plan = LaunchPlan(
        runtime_handler="io.example.v1",
        readiness=TlsConnectReadiness(port_name=PORT_NAME, timeout_s=60.0),
    )
    kernel.data["published_host"] = "127.0.0.1"
    kernel.data["container_id"] = CONTAINER_ID
    fake.tasks[CONTAINER_ID] = TaskInfo(pid=1000, state=TaskState.RUNNING, exit_status=0)
    return kernel


@pytest.fixture
def fast_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(kernel_module, "_TLS_PROBE_WINDOW_SEC", 0.3)
    monkeypatch.setattr(kernel_module, "_TLS_RETRY_INTERVAL_SEC", 0.05)


@pytest.fixture
def refused(monkeypatch: pytest.MonkeyPatch) -> RefusingConnect:
    connect = RefusingConnect()
    monkeypatch.setattr("asyncio.open_connection", connect)
    return connect


@pytest.fixture
async def tls_server(tmp_path: Path) -> AsyncIterator[int]:
    server = await asyncio.start_server(
        lambda r, w: w.close(), "127.0.0.1", 0, ssl=_self_signed_context(tmp_path)
    )
    try:
        yield int(server.sockets[0].getsockname()[1])
    finally:
        server.close()
        await server.wait_closed()


class TestCheckStatusTls:
    async def test_handshake_with_a_self_signed_cert_is_ready(
        self, tls_kernel: ContainerdKernel, tls_server: int
    ) -> None:
        _publish(tls_kernel, tls_server)

        assert await tls_kernel.check_status() == {}

    async def test_refused_connection_retries_then_asks_to_try_again(
        self, tls_kernel: ContainerdKernel, fast_probe: None, refused: RefusingConnect
    ) -> None:
        _publish(tls_kernel, 30001)

        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

        assert refused.calls >= 2

    async def test_probes_the_published_host_and_host_port(
        self, tls_kernel: ContainerdKernel, mocker: MockerFixture, fast_probe: None
    ) -> None:
        connect = mocker.patch("asyncio.open_connection", side_effect=OSError("refused"))
        tls_kernel.data["published_host"] = "10.0.0.5"
        _publish(tls_kernel, 30001)

        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

        assert connect.call_args.args == ("10.0.0.5", 30001)

    async def test_call_after_the_deadline_times_out_without_probing(
        self, tls_kernel: ContainerdKernel, refused: RefusingConnect
    ) -> None:
        tls_kernel.launch_plan = LaunchPlan(
            runtime_handler="io.example.v1",
            readiness=TlsConnectReadiness(port_name=PORT_NAME, timeout_s=0.0),
        )
        _publish(tls_kernel, 30001)

        with pytest.raises(ReadinessTimeout):
            await tls_kernel.check_status()

        assert refused.calls == 0

    async def test_deadline_passing_during_a_call_times_out(
        self,
        tls_kernel: ContainerdKernel,
        monkeypatch: pytest.MonkeyPatch,
        refused: RefusingConnect,
    ) -> None:
        monkeypatch.setattr(kernel_module, "_TLS_RETRY_INTERVAL_SEC", 0.02)
        tls_kernel.launch_plan = LaunchPlan(
            runtime_handler="io.example.v1",
            readiness=TlsConnectReadiness(port_name=PORT_NAME, timeout_s=0.2),
        )
        _publish(tls_kernel, 30001)

        with pytest.raises(ReadinessTimeout):
            await tls_kernel.check_status()

    async def test_readiness_timeout_is_not_retried_by_the_create_loop(
        self, tls_kernel: ContainerdKernel, refused: RefusingConnect
    ) -> None:
        tls_kernel.launch_plan = LaunchPlan(
            runtime_handler="io.example.v1",
            readiness=TlsConnectReadiness(port_name=PORT_NAME, timeout_s=0.0),
        )
        _publish(tls_kernel, 30001)
        attempts = 0

        with pytest.raises(ReadinessTimeout):
            async for attempt in AsyncRetrying(
                wait=wait_none(),
                stop=stop_after_attempt(5),
                retry=retry_if_exception_type(TryAgain),
            ):
                with attempt:
                    attempts += 1
                    await tls_kernel.check_status()

        assert attempts == 1

    async def test_deadline_lasts_across_calls(
        self,
        tls_kernel: ContainerdKernel,
        monkeypatch: pytest.MonkeyPatch,
        refused: RefusingConnect,
    ) -> None:
        monkeypatch.setattr(kernel_module, "_TLS_PROBE_WINDOW_SEC", 0.1)
        monkeypatch.setattr(kernel_module, "_TLS_RETRY_INTERVAL_SEC", 0.02)
        tls_kernel.launch_plan = LaunchPlan(
            runtime_handler="io.example.v1",
            readiness=TlsConnectReadiness(port_name=PORT_NAME, timeout_s=0.25),
        )
        _publish(tls_kernel, 30001)

        with pytest.raises(TryAgain):
            await tls_kernel.check_status()
        with pytest.raises(TryAgain):
            await tls_kernel.check_status()
        with pytest.raises(ReadinessTimeout):
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
    @pytest.fixture
    def running(self, tls_kernel: ContainerdKernel) -> None:
        _publish(tls_kernel, 30001)

    async def test_running_task_keeps_retrying(
        self,
        tls_kernel: ContainerdKernel,
        running: None,
        fast_probe: None,
        refused: RefusingConnect,
    ) -> None:
        with pytest.raises(TryAgain):
            await tls_kernel.check_status()

    async def test_stopped_task_ends_the_wait_with_its_exit_status(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        running: None,
        fast_probe: None,
        refused: RefusingConnect,
    ) -> None:
        tls_kernel._profile = _NamingProfile()
        fake.tasks[CONTAINER_ID] = TaskInfo(pid=1000, state=TaskState.STOPPED, exit_status=137)

        with pytest.raises(KernelTaskExited, match=r"named 137: .*status 137") as exc_info:
            await tls_kernel.check_status()

        assert exc_info.value.exit_status == 137
        assert not isinstance(exc_info.value, TryAgain)
        assert refused.calls == 1

    async def test_missing_task_ends_the_wait(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        running: None,
        fast_probe: None,
        refused: RefusingConnect,
    ) -> None:
        del fake.tasks[CONTAINER_ID]

        with pytest.raises(KernelTaskExited, match="gone"):
            await tls_kernel.check_status()

    async def test_failed_task_lookup_keeps_retrying(
        self,
        tls_kernel: ContainerdKernel,
        fake: FakeContainerd,
        running: None,
        fast_probe: None,
        refused: RefusingConnect,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(fake, "get_task", side_effect=ContainerdOperationFailed("rpc"))

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
        _publish(tls_kernel, tls_server)

        assert await tls_kernel.check_status() == {}
