from __future__ import annotations

import asyncio
import errno
from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai.backend.agent.agent import _observe_stat_task
from ai.backend.agent.metrics.metric import StatScope


class TestObserveStatTaskDecorator:
    """Tests for _observe_stat_task decorator error handling."""

    @pytest.fixture
    def mock_stat_task_observer(self) -> Generator[Mock, None, None]:
        with patch("ai.backend.agent.agent.StatTaskObserver") as mock_cls:
            mock_observer = Mock()
            mock_cls.instance.return_value = mock_observer
            yield mock_observer

    @pytest.fixture
    def mock_log(self) -> Generator[Mock, None, None]:
        with patch("ai.backend.agent.agent.log") as _mock_log:
            yield _mock_log

    @pytest.fixture
    def mock_agent(self) -> AsyncMock:
        agent = AsyncMock()
        agent.id = "test-agent-id"
        agent.produce_error_event = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_successful_execution_observes_success(
        self,
        mock_agent: AsyncMock,
        mock_stat_task_observer: Mock,
    ) -> None:
        @_observe_stat_task(stat_scope=StatScope.NODE)
        async def succeeding_task(self: object) -> None:
            pass

        await succeeding_task(mock_agent)

        mock_stat_task_observer.observe_stat_task_triggered.assert_called_once()
        mock_stat_task_observer.observe_stat_task_success.assert_called_once()
        mock_stat_task_observer.observe_stat_task_failure.assert_not_called()

    @pytest.mark.asyncio
    async def test_emfile_logs_warning_not_exception(
        self,
        mock_agent: AsyncMock,
        mock_stat_task_observer: Mock,
        mock_log: Mock,
    ) -> None:
        @_observe_stat_task(stat_scope=StatScope.CONTAINER)
        async def emfile_task(self: object) -> None:
            raise OSError(errno.EMFILE, "Too many open files")

        await emfile_task(mock_agent)

        mock_log.warning.assert_called_once()
        mock_log.exception.assert_not_called()
        mock_agent.produce_error_event.assert_awaited_once()
        mock_stat_task_observer.observe_stat_task_failure.assert_called_once()
        mock_stat_task_observer.observe_stat_task_success.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception",
        [
            OSError(errno.ENOENT, "No such file or directory"),
            RuntimeError("unexpected failure"),
        ],
    )
    async def test_non_emfile_error_logs_exception_and_produces_error_event(
        self,
        mock_agent: AsyncMock,
        mock_stat_task_observer: Mock,
        mock_log: Mock,
        exception: Exception,
    ) -> None:
        @_observe_stat_task(stat_scope=StatScope.NODE)
        async def failing_task(self: object) -> None:
            raise exception

        await failing_task(mock_agent)

        mock_log.exception.assert_called_once()
        mock_agent.produce_error_event.assert_awaited_once()
        mock_stat_task_observer.observe_stat_task_failure.assert_called_once()
        mock_stat_task_observer.observe_stat_task_success.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancelled_error_is_silently_swallowed(
        self,
        mock_agent: AsyncMock,
        mock_stat_task_observer: Mock,
        mock_log: Mock,
    ) -> None:
        @_observe_stat_task(stat_scope=StatScope.NODE)
        async def cancelled_task(self: object) -> None:
            raise asyncio.CancelledError()

        await cancelled_task(mock_agent)

        mock_log.warning.assert_not_called()
        mock_log.exception.assert_not_called()
        mock_agent.produce_error_event.assert_not_called()
        mock_stat_task_observer.observe_stat_task_failure.assert_not_called()
        mock_stat_task_observer.observe_stat_task_success.assert_not_called()
