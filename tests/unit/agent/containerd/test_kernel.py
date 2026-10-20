from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.profile.base import LaunchPlan
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
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

    async def test_check_status_is_a_placeholder(self, kernel: ContainerdKernel) -> None:
        with pytest.raises(KernelVerbNotSupported, match="check_status is not implemented yet"):
            await kernel.check_status()
