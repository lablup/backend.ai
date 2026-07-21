"""Info/decision/result types for the idle-check reconcile stage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.types import SessionId
from ai.backend.manager.data.reconciler.types import (
    BaseReconcilerCategory,
    HandlerOutcome,
    LastHistory,
)
from ai.backend.manager.data.session.options import HandlerPolicyResolver
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.types import IdleCheckBatchData
from ai.backend.manager.sokovan.idle_check.checkers.base import IdleJudgment
from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerInfo,
    BaseReconcilerKind,
    BaseReconcilerResult,
    BaseReconcilerTargetStatuses,
    ReconcilerDecision,
)


class IdleCheckCategory(BaseReconcilerCategory):
    IDLE = "idle"


class IdleCheckKind(BaseReconcilerKind):
    SESSION = "session"


@dataclass(frozen=True)
class IdleCheckTargetStatuses(BaseReconcilerTargetStatuses):
    session_statuses: frozenset[SessionStatus]


@dataclass
class IdleCheckReconcileInfo(BaseReconcilerInfo):
    batch: IdleCheckBatchData
    current_time: datetime

    @override
    def entity_ids(self) -> Sequence[UUID]:
        session_ids = (assignment.session.session_id for assignment in self.batch.assignments)
        return list(dict.fromkeys(session_ids))

    @override
    def now(self) -> datetime:
        return self.current_time


@dataclass
class IdleCheckDecision(ReconcilerDecision):
    session_id: SessionId
    handler_outcome: HandlerOutcome
    prior_history: LastHistory | None
    handler_policy: HandlerPolicyResolver

    @override
    def entity_id(self) -> UUID:
        return self.session_id

    @override
    def outcome(self) -> HandlerOutcome:
        return self.handler_outcome

    @override
    def last_history(self) -> LastHistory | None:
        return self.prior_history

    @override
    def policy_resolver(self) -> HandlerPolicyResolver:
        return self.handler_policy


@dataclass
class IdleCheckResult(BaseReconcilerResult):
    judgments: list[IdleJudgment] = field(default_factory=list)

    @override
    def processed_count(self) -> int:
        return len(self.judgments)

    @override
    def failed_count(self) -> int:
        return 0

    @override
    def decisions(self) -> Sequence[ReconcilerDecision]:
        return ()
