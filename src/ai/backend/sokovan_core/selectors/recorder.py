"""Recording seam of the agent selection: the caller supplies the recorder."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from ai.backend.common.types import SessionId


class PlacementStepRecorder(Protocol):
    """Records one selection step (a filter) as a success or a failure."""

    def step(
        self,
        name: str,
        success_detail: str | None = None,
    ) -> AbstractContextManager[None]: ...


class PlacementRecorderProvider(Protocol):
    """Hands out the recorder of a session, or None outside a recording scope."""

    def recorder_for(self, session_id: SessionId) -> PlacementStepRecorder | None: ...
