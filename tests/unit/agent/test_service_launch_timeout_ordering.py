from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Callable
from typing import Any, override
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

import ai.backend.agent.kernel as agent_kernel
from ai.backend.agent.kernel import SERVICE_REPLY_TIMEOUT_MARGIN_SEC, AbstractCodeRunner
from ai.backend.common.types import KernelId, SessionId
from ai.backend.kernel.base import BaseRunner

# The budget the kernel runner falls back to for a payload that predates the configured key.
# It lives in a package that cannot be imported the other way round, since that one ships
# inside the container, so the ordering between the two is only ever checked here.
KRUNNER_FALLBACK_BUDGET_SEC: float = (
    inspect.signature(BaseRunner._start_service).parameters["launch_timeout"].default
)

_REPLY_DELAY_SEC = 0.2
_REPLY_BUDGET_SEC = KRUNNER_FALLBACK_BUDGET_SEC + SERVICE_REPLY_TIMEOUT_MARGIN_SEC


class _SocketlessCodeRunner(AbstractCodeRunner):
    """A code runner whose REPL addresses are never dialled, so the test can drive
    `feed_start_service` without a container on the other end."""

    @override
    async def get_repl_in_addr(self) -> str:
        return "inproc://test"

    @override
    async def get_repl_out_addr(self) -> str:
        return "inproc://test"


@pytest.fixture
def code_runner() -> _SocketlessCodeRunner:
    runner = _SocketlessCodeRunner(
        KernelId(uuid4()),
        SessionId(uuid4()),
        Mock(),
    )
    sockets = Mock()
    sockets.send_multipart = AsyncMock()
    runner._sockets = sockets
    return runner


@pytest.fixture
def installed_budgets(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records the budget `feed_start_service` installs, leaving it otherwise in force."""
    recorded: list[float] = []
    real_timeout: Callable[[float], Any] = agent_kernel.timeout

    def record(delay: float) -> Any:
        recorded.append(delay)
        return real_timeout(delay)

    monkeypatch.setattr(agent_kernel, "timeout", record)
    return recorded


class TestStartServiceReplyBudget:
    async def test_waits_out_a_runner_that_is_still_opening_the_port(
        self,
        code_runner: _SocketlessCodeRunner,
        installed_budgets: list[float],
    ) -> None:
        async def reply_late() -> None:
            await asyncio.sleep(_REPLY_DELAY_SEC)
            await code_runner.service_queue.put(json.dumps({"status": "started"}).encode())

        asyncio.create_task(reply_late())

        result = await code_runner.feed_start_service(
            {"name": "jupyter"}, reply_timeout=_REPLY_BUDGET_SEC
        )

        assert result == {"status": "started"}
        assert installed_budgets == [_REPLY_BUDGET_SEC]
        assert installed_budgets[0] > KRUNNER_FALLBACK_BUDGET_SEC

    async def test_reports_a_timeout_only_once_the_runner_has_had_its_full_budget(
        self,
        code_runner: _SocketlessCodeRunner,
        installed_budgets: list[float],
    ) -> None:
        result = await code_runner.feed_start_service(
            {"name": "jupyter"}, reply_timeout=_REPLY_DELAY_SEC
        )

        assert result == {"status": "failed", "error": "timeout"}
        assert installed_budgets == [_REPLY_DELAY_SEC]
