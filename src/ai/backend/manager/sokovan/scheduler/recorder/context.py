"""Session-specific recorder context for scheduler coordinator."""

from __future__ import annotations

from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.recorder.context import RecorderContext

# Session-specific type alias
SessionRecorderContext = RecorderContext[SessionId]

__all__ = [
    "SessionRecorderContext",
]
