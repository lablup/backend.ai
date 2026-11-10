import logging
from collections.abc import Iterator
from contextvars import ContextVar

import pytest

from ai.backend.common.asyncio import ConsecutiveFailures, run_in_executor_with_context
from ai.backend.logging.structured import StructuredLogger, with_log_context

LOGGER_NAME = "tests.common.asyncio"

_marker: ContextVar[str] = ContextVar("marker", default="unset")


@pytest.fixture
def logger() -> StructuredLogger:
    return StructuredLogger(logging.getLogger(LOGGER_NAME))


@pytest.fixture
def capture_info(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        yield caplog


class TestRunInExecutorWithContext:
    async def test_scope_fields_reach_logs_in_executor(
        self, logger: StructuredLogger, capture_info: pytest.LogCaptureFixture
    ) -> None:
        def work() -> None:
            logger.info("executor work done")

        with with_log_context(session_id="sess-1"):
            await run_in_executor_with_context(None, work)

        [record] = capture_info.records
        assert record.__dict__["log_tag_session_id"] == "sess-1"

    async def test_passes_args_and_returns_result(self) -> None:
        def add(a: int, b: int) -> int:
            return a + b

        assert await run_in_executor_with_context(None, add, 1, 2) == 3

    async def test_changes_in_executor_do_not_leak_to_caller(self) -> None:
        def mark() -> str:
            _marker.set("executor")
            return _marker.get()

        token = _marker.set("caller")
        try:
            assert await run_in_executor_with_context(None, mark) == "executor"
            assert _marker.get() == "caller"
        finally:
            _marker.reset(token)


class TestConsecutiveFailures:
    def test_only_the_first_failure_starts_a_streak(self) -> None:
        failures = ConsecutiveFailures()

        assert [failures.record_failure() for _ in range(3)] == [True, False, False]
        assert failures.record_success() == 3
        assert failures.record_failure() is True

    def test_success_without_a_streak_reports_zero(self) -> None:
        assert ConsecutiveFailures().record_success() == 0

    def test_delay_doubles_up_to_the_cap(self) -> None:
        failures = ConsecutiveFailures(initial_delay_sec=1.0, max_delay_sec=30.0)
        delays = [failures.delay_sec()]
        for _ in range(7):
            failures.record_failure()
            delays.append(failures.delay_sec())

        assert delays == [1.0, 1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 30.0]
