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
from ai.backend.manager.repositories.idle_checker.types import IdleCheckSnapshot
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
    snapshot: IdleCheckSnapshot
    current_time: datetime

    @override
    def entity_ids(self) -> Sequence[UUID]:
        return list(self.snapshot.session_views_by_id.keys())

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
    idle_session_ids: list[SessionId] = field(default_factory=list)

    @override
    def processed_count(self) -> int:
        return len(self.idle_session_ids)

    @override
    def failed_count(self) -> int:
        return 0

    @override
    def decisions(self) -> Sequence[ReconcilerDecision]:
        # Idle output is a termination list, not per-entity retryable outcomes.
        return ()
