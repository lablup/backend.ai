from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.models.idle_checker.row import SessionIdleCheckRow
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair


@dataclass
class SessionIdleCheckCreatorSpec(CreatorSpec[SessionIdleCheckRow]):
    pair: SessionIdleCheckPair
    now: datetime

    @override
    def build_row(self) -> SessionIdleCheckRow:
        return SessionIdleCheckRow(
            session_id=self.pair.session_id,
            idle_checker_id=self.pair.checker_id,
            expire_at=self.now,
            last_status=IdleCheckPhase.NOT_CHECKED,
            last_message="Not checked yet.",
        )
