from __future__ import annotations

import inspect
import json
from typing import Any, override
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

import ai.backend.agent.kernel as agent_kernel
from ai.backend.agent.kernel import AbstractCodeRunner
from ai.backend.common.types import KernelId, SessionId
from ai.backend.kernel.base import BaseRunner

# The budget the kernel runner grants a service port. Its package cannot be imported the other
# way round -- it ships inside the container -- so the ordering is only ever checked here.
KRUNNER_LAUNCH_BUDGET_SEC: float = (
    inspect.signature(BaseRunner._start_service).parameters["launch_timeout"].default
)


class _SocketlessCodeRunner(AbstractCodeRunner):
    @override
    async def get_repl_in_addr(self) -> str:
        return "inproc://test"

    @override
    async def get_repl_out_addr(self) -> str:
        return "inproc://test"


@pytest.fixture
def code_runner() -> _SocketlessCodeRunner:
    runner = _SocketlessCodeRunner(KernelId(uuid4()), SessionId(uuid4()), Mock())
    runner._sockets = Mock(send_multipart=AsyncMock())
    runner.service_queue.put_nowait(json.dumps({"status": "started"}).encode())
    return runner


@pytest.fixture
def installed_budgets(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records the budget the call installs, leaving it otherwise in force."""
    recorded: list[float] = []
    real_timeout = agent_kernel.timeout

    def record(delay: float) -> Any:
        recorded.append(delay)
        return real_timeout(delay)

    monkeypatch.setattr(agent_kernel, "timeout", record)
    return recorded


async def test_the_reply_budget_outlasts_the_kernel_runner(
    code_runner: _SocketlessCodeRunner,
    installed_budgets: list[float],
) -> None:
    result = await code_runner.feed_start_service({"name": "jupyter"})

    assert result == {"status": "started"}
    assert installed_budgets[0] > KRUNNER_LAUNCH_BUDGET_SEC
