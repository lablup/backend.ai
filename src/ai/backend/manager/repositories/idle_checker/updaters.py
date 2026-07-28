from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.types import SessionTypes
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow, SessionIdleCheckRow
from ai.backend.manager.repositories.base import BatchUpdaterSpec, UpdaterSpec
from ai.backend.manager.repositories.idle_checker.types import IdleJudgmentData
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class IdleCheckerUpdaterSpec(UpdaterSpec[IdleCheckerRow]):
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    target_session_types: OptionalState[list[SessionTypes]] = field(
        default_factory=OptionalState[list[SessionTypes]].nop
    )
    initial_grace_period_seconds: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    spec: OptionalState[IdleCheckerSpec] = field(default_factory=OptionalState[IdleCheckerSpec].nop)

    @property
    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.target_session_types.update_dict(to_update, "target_session_types")
        self.initial_grace_period_seconds.update_dict(to_update, "initial_grace_period_seconds")
        self.spec.update_dict(to_update, "spec")
        return to_update


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
