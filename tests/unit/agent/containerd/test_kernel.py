from __future__ import annotations

import asyncio
import socket
import uuid
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from tenacity import TryAgain

from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.profile.base import LaunchPlan
from ai.backend.agent.errors.containerd import ContainerdOperationFailed, KernelVerbNotSupported
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import KernelId


@pytest.fixture
def kernel(ownership_data: KernelOwnershipData, launch_plan: LaunchPlan) -> ContainerdKernel:
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
    """The runc readiness probe: a TCP connect to the REPL-in port."""

    async def test_listening_port_is_ready(self, kernel: ContainerdKernel) -> None:
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        kernel.data["intrinsic_ports"] = {"replin": port, "replout": port + 1}

        try:
            assert await kernel.check_status() == {}
        finally:
            server.close()
            await server.wait_closed()

    async def test_refused_connection_asks_the_create_loop_to_retry(
        self, kernel: ContainerdKernel
    ) -> None:
        kernel.data["intrinsic_ports"] = {"replin": _unused_port(), "replout": 1}

        with pytest.raises(TryAgain):
            await kernel.check_status()

    async def test_ports_survive_a_recreated_kernel_object(
        self, kernel: ContainerdKernel, ownership_data: KernelOwnershipData, launch_plan: LaunchPlan
    ) -> None:
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        persisted = {"intrinsic_ports": {"replin": port, "replout": port + 1}}
        recreated = ContainerdKernel(
            ownership_data,
            "net-1",
            MagicMock(),
            1,
            agent_config={},
            resource_spec=MagicMock(),
            service_ports=[],
            environ={},
            data=dict(persisted),
            launch_plan=launch_plan,
        )

        try:
            assert await recreated.check_status() == {}
        finally:
            server.close()
            await server.wait_closed()

    async def test_missing_ports_is_a_typed_error(self, kernel: ContainerdKernel) -> None:
        with pytest.raises(ContainerdOperationFailed, match="REPL ports"):
            await kernel.check_status()
