"""Session-specific recorder for scheduler coordinator."""

from __future__ import annotations

from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.recorder.recorder import TransitionRecorder

# Session-specific type alias
SessionTransitionRecorder = TransitionRecorder[SessionId]

__all__ = [
    "SessionTransitionRecorder",
]
