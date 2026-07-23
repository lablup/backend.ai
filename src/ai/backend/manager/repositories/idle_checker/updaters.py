from __future__ import annotations

from typing import Any, override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.models.idle_checker.row import SessionIdleCheckRow
from ai.backend.manager.repositories.base import BatchUpdaterSpec


class SessionIdleCheckReadyBatchUpdaterSpec(BatchUpdaterSpec[SessionIdleCheckRow]):
    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {"last_status": IdleCheckPhase.READY_TO_CHECK}
