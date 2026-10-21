"""The session lifecycle handler adapter, assembled for one row.

The adapter answers from the schedule coordinator's registry alone, so each fixture is
the adapter over a fake coordinator built from the handlers that row stands on.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from ai.backend.manager.api.adapters.session_lifecycle_handler.adapter import (
    SessionLifecycleHandlerAdapter,
)
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.terminate_sessions import (
    TerminateSessionsLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator
from bai_scenario.fakes.scheduler import FakeScheduleCoordinator
from bai_scenario.runner.unwired import unwired


@pytest.fixture
def lifecycle_handlers() -> Sequence[SessionLifecycleHandler]:
    """등록된 세션 처리기. 이름과 클래스 설명만 읽으므로 안쪽은 배선하지 않는다."""
    return (
        TerminateSessionsLifecycleHandler(
            terminator=unwired(SessionTerminator, "처리기의 이름과 설명만 읽는다"),
            repository=unwired(SchedulerRepository, "처리기의 이름과 설명만 읽는다"),
        ),
    )


@pytest.fixture
def adapter(
    lifecycle_handlers: Sequence[SessionLifecycleHandler],
) -> SessionLifecycleHandlerAdapter:
    return SessionLifecycleHandlerAdapter(FakeScheduleCoordinator(lifecycle_handlers))


@pytest.fixture
def adapter_with_no_handler_registered() -> SessionLifecycleHandlerAdapter:
    return SessionLifecycleHandlerAdapter(FakeScheduleCoordinator(()))
