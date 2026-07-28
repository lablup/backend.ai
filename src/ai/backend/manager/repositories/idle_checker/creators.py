from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.idle_checker.types import IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.types import SessionTypes
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow, SessionIdleCheckRow
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair


@dataclass
class IdleCheckerCreatorSpec(CreatorSpec[IdleCheckerRow]):
    name: str
    description: str | None
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpec

    @override
    def build_row(self) -> IdleCheckerRow:
        return IdleCheckerRow(
            name=self.name,
            description=self.description,
            target_session_types=self.target_session_types,
            initial_grace_period_seconds=self.initial_grace_period_seconds,
            spec=self.spec,
        )


@dataclass
class SessionIdleCheckCreatorSpec(CreatorSpec[SessionIdleCheckRow]):
    pair: SessionIdleCheckPair

    @override
    def build_row(self) -> SessionIdleCheckRow:
        return SessionIdleCheckRow(
            session_id=self.pair.session_id,
            idle_checker_id=self.pair.checker_id,
            expire_at=None,
            last_status=IdleCheckPhase.NOT_CHECKED,
            last_message="Not checked yet.",
        )
