from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.session import SessionID
from ai.backend.manager.models.idle_checker.row import SessionIdleCheckRow
from ai.backend.manager.repositories.base import UpserterSpec


@dataclass
class SessionIdleCheckExcludeUpserterSpec(UpserterSpec[SessionIdleCheckRow]):
    """Mark a pair EXCLUDED, creating the row when assignment-sync has not yet."""

    session_id: SessionID
    checker_id: IdleCheckerID

    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "idle_checker_id": self.checker_id,
            "last_status": IdleCheckPhase.EXCLUDED,
            "expire_at": None,
            "last_message": "Excluded from idle checks.",
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "last_status": IdleCheckPhase.EXCLUDED,
            "expire_at": None,
            "last_message": "Excluded from idle checks.",
        }
