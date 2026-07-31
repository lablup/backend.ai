from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.models.idle_checker.row import SessionIdleCheckRow
from ai.backend.manager.repositories.base import UpserterSpec
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair


@dataclass
class SessionIdleCheckExclusionUpserterSpec(UpserterSpec[SessionIdleCheckRow]):
    """Mark one (session, checker) pair EXCLUDED, creating the row if absent.

    Conflict target: (session_id, idle_checker_id). Any prior phase — including
    IDLE_EXPIRED — is overwritten; a pending expiry is voided by clearing expire_at.
    """

    pair: SessionIdleCheckPair

    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "session_id": self.pair.session_id,
            "idle_checker_id": self.pair.checker_id,
            "expire_at": None,
            "last_status": IdleCheckPhase.EXCLUDED,
            "last_message": "Excluded from idle checks.",
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "expire_at": None,
            "last_status": IdleCheckPhase.EXCLUDED,
            "last_message": "Excluded from idle checks.",
        }
