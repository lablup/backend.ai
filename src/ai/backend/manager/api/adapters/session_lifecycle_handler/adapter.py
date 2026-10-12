"""Adapter surfacing the registered session lifecycle handlers as DTOs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.dto.manager.v2.session_lifecycle_handler.response import (
    ListSessionLifecycleHandlersPayload,
    SessionLifecycleHandlerNode,
)

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
    from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler


def _first_docstring_line(cls: type[SessionLifecycleHandler]) -> str | None:
    doc = cls.__doc__
    if doc is None:
        return None
    for raw_line in doc.splitlines():
        stripped = raw_line.strip()
        if stripped:
            return stripped
    return None


class SessionLifecycleHandlerAdapter:
    """Expose the schedule coordinator's live lifecycle handler registry as DTO nodes.

    Reads the same registry that validates ``handler_options.by_handler`` keys when a
    resource group's default session options are replaced.
    """

    _schedule_coordinator: ScheduleCoordinator

    def __init__(self, schedule_coordinator: ScheduleCoordinator) -> None:
        self._schedule_coordinator = schedule_coordinator

    async def list_session_lifecycle_handlers(self) -> ListSessionLifecycleHandlersPayload:
        """Return all lifecycle handlers currently registered on the coordinator."""
        items = [
            SessionLifecycleHandlerNode(
                name=handler.name(),
                description=_first_docstring_line(type(handler)),
            )
            for handler in self._schedule_coordinator.registered_lifecycle_handlers()
        ]
        return ListSessionLifecycleHandlersPayload(items=items)
