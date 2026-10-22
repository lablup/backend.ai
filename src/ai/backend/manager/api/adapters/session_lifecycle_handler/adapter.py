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


class SessionLifecycleHandlerAdapter:
    """Expose the lifecycle handlers the schedule coordinator runs as DTO nodes."""

    _handlers: tuple[SessionLifecycleHandler, ...]

    def __init__(self, handlers: Sequence[SessionLifecycleHandler]) -> None:
        self._handlers = tuple(handlers)

    async def list_session_lifecycle_handlers(self) -> ListSessionLifecycleHandlersPayload:
        """Return every lifecycle handler the schedule coordinator runs."""
        items = [
            SessionLifecycleHandlerNode(
                name=handler.name(),
                description=handler.description(),
            )
            for handler in self._handlers
        ]
        return ListSessionLifecycleHandlersPayload(items=items)
