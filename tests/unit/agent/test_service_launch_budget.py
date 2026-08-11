from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from ai.backend.agent.config.unified import KernelLifecyclesConfig
from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId
from ai.backend.kernel.base import DEFAULT_SERVICE_LAUNCH_TIMEOUT_SEC, BaseRunner

_SERVICE_NAME = "jupyter"
_SERVICE_PORT = 8081
_CONFIG_SECTION = "kernel-lifecycles"
_CONFIG_KEY = "service-launch-timeout-sec"


@dataclass(frozen=True)
class _BudgetCase:
    configured_sec: float


@dataclass(frozen=True)
class _StartServiceCall:
    launch_timeout: float
    reply_timeout: float


class _RunnerSpy:
    """Records what the kernel object hands to the code runner."""

    call: _StartServiceCall | None

    def __init__(self) -> None:
        self.call = None

    async def feed_start_service(
        self,
        service_info: Mapping[str, Any],
        *,
        reply_timeout: float,
    ) -> dict[str, Any]:
        self.call = _StartServiceCall(
            launch_timeout=service_info["launch_timeout"],
            reply_timeout=reply_timeout,
        )
        return {"status": "started"}


class _KernelRunnerSpy(BaseRunner):
    """Records the budget the kernel runner derives from a start-service payload.

    ``BaseRunner.__init__`` is skipped on purpose: it reads ``/home/work`` and the container's
    environment, neither of which exists outside a kernel container.
    """

    launch_timeout: float | None

    def __init__(self) -> None:
        self.launch_timeout = None
        self.outsock = Mock()
        self.outsock.send_multipart = AsyncMock()

    @override
    async def _start_service(
        self,
        service_info: Mapping[str, Any],
        *,
        cwd: str | None = None,
        launch_timeout: float | None = DEFAULT_SERVICE_LAUNCH_TIMEOUT_SEC,
    ) -> dict[str, Any]:
        self.launch_timeout = launch_timeout
        return {"status": "started"}

    @override
    async def init_with_loop(self) -> None:
        raise NotImplementedError

    @override
    async def build_heuristic(self) -> int:
        raise NotImplementedError

    @override
    async def execute_heuristic(self) -> int:
        raise NotImplementedError

    @override
    async def start_service(
        self,
        service_info: Mapping[str, Any],
    ) -> tuple[list[str] | None, dict[str, str]] | None:
        raise NotImplementedError


@pytest.fixture
def kernel(request: pytest.FixtureRequest) -> DockerKernel:
    case: _BudgetCase = request.param
    return DockerKernel(
        ownership_data=KernelOwnershipData(
            kernel_id=KernelId(uuid4()),
            session_id=SessionId(uuid4()),
            agent_id=AgentId("test-agent-id"),
        ),
        network_id="test-network",
        image=ImageRef(
            name="test-image",
            project="test-project",
            registry="registry.local",
            tag="latest",
            architecture="x86_64",
            is_local=False,
        ),
        version=1,
        network_driver="bridge",
        agent_config={
            _CONFIG_SECTION: KernelLifecyclesConfig(
                service_launch_timeout_sec=case.configured_sec
            ).model_dump(by_alias=True),
        },
        resource_spec=Mock(),
        service_ports=[
            {
                "name": _SERVICE_NAME,
                "container_ports": [_SERVICE_PORT],
                "protocol": "http",
            },
        ],
        environ={},
        data={},
    )


@pytest.fixture
def kernel_runner() -> _KernelRunnerSpy:
    return _KernelRunnerSpy()


class TestServiceLaunchBudget:
    @pytest.mark.parametrize(
        "kernel",
        [
            _BudgetCase(configured_sec=DEFAULT_SERVICE_LAUNCH_TIMEOUT_SEC),
            _BudgetCase(configured_sec=5.0),
            _BudgetCase(configured_sec=120.0),
        ],
        indirect=True,
        ids=lambda case: f"{case.configured_sec:g}s",
    )
    async def test_agent_outlasts_the_kernel_runner(self, kernel: DockerKernel) -> None:
        spy = _RunnerSpy()
        kernel.runner = spy  # type: ignore[assignment]

        await kernel.start_service(_SERVICE_NAME, {})

        assert spy.call is not None
        assert spy.call.launch_timeout == kernel.agent_config[_CONFIG_SECTION][_CONFIG_KEY]
        assert spy.call.reply_timeout > spy.call.launch_timeout

    @pytest.mark.parametrize(
        "case",
        [
            _BudgetCase(configured_sec=DEFAULT_SERVICE_LAUNCH_TIMEOUT_SEC),
            _BudgetCase(configured_sec=5.0),
            _BudgetCase(configured_sec=120.0),
        ],
        ids=lambda case: f"{case.configured_sec:g}s",
    )
    async def test_kernel_runner_takes_the_budget_from_the_payload(
        self,
        kernel_runner: _KernelRunnerSpy,
        case: _BudgetCase,
    ) -> None:
        await kernel_runner._start_service_and_feed_result({
            "name": _SERVICE_NAME,
            "port": _SERVICE_PORT,
            "launch_timeout": case.configured_sec,
        })

        assert kernel_runner.launch_timeout == case.configured_sec

    async def test_kernel_runner_falls_back_for_a_payload_without_the_budget(
        self,
        kernel_runner: _KernelRunnerSpy,
    ) -> None:
        await kernel_runner._start_service_and_feed_result({
            "name": _SERVICE_NAME,
            "port": _SERVICE_PORT,
        })

        assert kernel_runner.launch_timeout == DEFAULT_SERVICE_LAUNCH_TIMEOUT_SEC
