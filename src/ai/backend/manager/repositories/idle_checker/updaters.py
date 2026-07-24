from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.models.idle_checker.row import SessionIdleCheckRow
from ai.backend.manager.repositories.base import BatchUpdaterSpec


@dataclass
class SessionIdleCheckPhaseBatchUpdaterSpec(BatchUpdaterSpec[SessionIdleCheckRow]):
    to_phase: IdleCheckPhase

    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {"last_status": self.to_phase}
