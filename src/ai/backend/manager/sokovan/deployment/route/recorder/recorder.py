"""Route-specific recorder for route coordinator."""

from __future__ import annotations

from uuid import UUID

from ai.backend.manager.sokovan.recorder.recorder import TransitionRecorder

# Route-specific type alias
RouteTransitionRecorder = TransitionRecorder[UUID]

__all__ = [
    "RouteTransitionRecorder",
]
