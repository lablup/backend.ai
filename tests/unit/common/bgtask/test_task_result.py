from __future__ import annotations

import pytest

from ai.backend.common.bgtask.task_result import (
    TaskCancelledResult,
    TaskFailedResult,
    TaskSuccessResult,
)
from ai.backend.common.bgtask.types import BgtaskStatus, TaskStatus


class TestBgtaskStatusToTaskStatus:
    """Regression tests for BgtaskStatus.to_task_status().

    A finished bgtask must map onto the *actual* TaskStatus recorded in the task
    store. Previously every finished subtask was unconditionally marked SUCCESS,
    so failed/cancelled commits were stored as SUCCESS (see PR #12168).
    """

    @pytest.mark.parametrize(
        ("bgtask_status", "expected"),
        [
            (BgtaskStatus.DONE, TaskStatus.SUCCESS),
            (BgtaskStatus.PARTIAL_SUCCESS, TaskStatus.SUCCESS),
            (BgtaskStatus.CANCELLED, TaskStatus.FAILURE),
            (BgtaskStatus.FAILED, TaskStatus.FAILURE),
            (BgtaskStatus.STARTED, TaskStatus.ONGOING),
            (BgtaskStatus.UPDATED, TaskStatus.ONGOING),
            (BgtaskStatus.UNKNOWN, TaskStatus.ONGOING),
        ],
    )
    def test_to_task_status_mapping(
        self, bgtask_status: BgtaskStatus, expected: TaskStatus
    ) -> None:
        assert bgtask_status.to_task_status() == expected


class TestTaskResultMessage:
    """Regression tests for TaskResult.result_message().

    The failure reason must be carried into the recorded task message instead of
    being discarded (see PR #12168).
    """

    def test_success_result_message(self) -> None:
        result = TaskSuccessResult(result=None)
        assert result.result_message() == "Task completed successfully"

    def test_cancelled_result_message(self) -> None:
        result = TaskCancelledResult(message="cancelled by user")
        assert result.result_message() == "cancelled by user"

    def test_failed_result_message_includes_exception(self) -> None:
        result = TaskFailedResult(exception=ZeroDivisionError("boom"))
        message = result.result_message()
        assert "boom" in message
        assert message != "Task completed successfully"
