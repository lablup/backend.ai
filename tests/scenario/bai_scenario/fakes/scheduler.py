"""Stand-in for the schedule coordinator a resource group call reaches.

It is asked only which session lifecycle handlers are registered, when the default
session options are replaced. It answers with what it was built from, so a scenario can
name a registered handler and an unregistered one.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler


class FakeScheduleCoordinator(ScheduleCoordinator):
    """등록된 세션 처리기만 답한다."""

    _registered: tuple[SessionLifecycleHandler, ...]

    def __init__(self, handlers: Sequence[SessionLifecycleHandler]) -> None:
        self._registered = tuple(handlers)

    @override
    def registered_lifecycle_handlers(self) -> tuple[SessionLifecycleHandler, ...]:
        return self._registered
