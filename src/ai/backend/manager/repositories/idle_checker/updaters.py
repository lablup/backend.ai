from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.models.idle_checker.row import SessionIdleCheckRow
from ai.backend.manager.repositories.base import BatchUpdaterSpec
from ai.backend.manager.repositories.idle_checker.types import IdleJudgmentData


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


@dataclass
class SessionIdleCheckJudgmentBatchUpdaterSpec(BatchUpdaterSpec[SessionIdleCheckRow]):
    judgments: Sequence[IdleJudgmentData]

    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {
            "last_status": sa.case(*[
                (
                    sa.and_(
                        SessionIdleCheckRow.session_id == judgment.session_id,
                        SessionIdleCheckRow.idle_checker_id == judgment.checker_id,
                    ),
                    judgment.status,
                )
                for judgment in self.judgments
            ]),
            "expire_at": sa.case(*[
                (
                    sa.and_(
                        SessionIdleCheckRow.session_id == judgment.session_id,
                        SessionIdleCheckRow.idle_checker_id == judgment.checker_id,
                    ),
                    judgment.expire_at,
                )
                for judgment in self.judgments
            ]),
            "last_message": sa.case(*[
                (
                    sa.and_(
                        SessionIdleCheckRow.session_id == judgment.session_id,
                        SessionIdleCheckRow.idle_checker_id == judgment.checker_id,
                    ),
                    judgment.message,
                )
                for judgment in self.judgments
            ]),
        }
