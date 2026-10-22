"""Adapter surfacing the session lifecycle handlers as DTOs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.common.dto.manager.v2.session_lifecycle_handler.response import (
    ListSessionLifecycleHandlersPayload,
    SessionLifecycleHandlerNode,
)

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
    """Expose the lifecycle handlers the schedule coordinator runs as DTO nodes."""

    _handlers: tuple[SessionLifecycleHandler, ...]

    def __init__(self, handlers: Sequence[SessionLifecycleHandler]) -> None:
        self._handlers = tuple(sorted(handlers, key=lambda handler: handler.name()))

    async def list_session_lifecycle_handlers(self) -> ListSessionLifecycleHandlersPayload:
        """Return every lifecycle handler the schedule coordinator runs, in name order."""
        items = [
            SessionLifecycleHandlerNode(
                name=handler.name(),
                description=_first_docstring_line(type(handler)),
            )
            for handler in self._handlers
        ]
        return ListSessionLifecycleHandlersPayload(items=items)
