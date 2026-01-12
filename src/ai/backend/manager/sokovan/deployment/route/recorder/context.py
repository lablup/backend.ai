"""Route-specific recorder context for route coordinator."""

from __future__ import annotations

from uuid import UUID

from ai.backend.manager.sokovan.recorder.context import RecorderContext

# Route-specific type alias
RouteRecorderContext = RecorderContext[UUID]

__all__ = [
    "RouteRecorderContext",
]
