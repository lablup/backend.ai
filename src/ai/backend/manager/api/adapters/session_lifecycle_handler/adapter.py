"""Adapter surfacing the session lifecycle handlers as DTOs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.dto.manager.v2.session_lifecycle_handler.response import (
    ListSessionLifecycleHandlersPayload,
    SessionLifecycleHandlerNode,
)
from ai.backend.manager.sokovan.scheduler.factory import SESSION_LIFECYCLE_HANDLER_TYPES

if TYPE_CHECKING:
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
    """Expose the session lifecycle handler classes the scheduler is built with as DTO nodes."""

    async def list_session_lifecycle_handlers(self) -> ListSessionLifecycleHandlersPayload:
        """Return every lifecycle handler the schedule coordinator is built with."""
        items = [
            SessionLifecycleHandlerNode(
                name=handler_type.name(),
                description=_first_docstring_line(handler_type),
            )
            for handler_type in SESSION_LIFECYCLE_HANDLER_TYPES
        ]
        return ListSessionLifecycleHandlersPayload(items=items)
