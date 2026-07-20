"""Info types for the expiry-sweep reconcile stage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.idle_checker.types import ExpiredIdleCheckBatchData
from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerInfo,
    BaseReconcilerResult,
    ReconcilerDecision,
)


@dataclass
class IdleCheckSweepReconcileInfo(BaseReconcilerInfo):
    batch: ExpiredIdleCheckBatchData

    @override
    def entity_ids(self) -> Sequence[UUID]:
        # A session with multiple expired checks is transitioned at most once.
        return list(dict.fromkeys(check.session_id for check in self.batch.checks))

    @override
    def now(self) -> datetime:
        return self.batch.now


@dataclass(frozen=True)
class IdleCheckSweepReason:
    """One elapsed checker result retained for the termination history."""

    checker_id: IdleCheckerID
    expire_at: datetime
    last_message: str


@dataclass(frozen=True)
class IdleCheckSweepReport:
    """All elapsed checker results for one session."""

    session_id: SessionId
    reasons: Sequence[IdleCheckSweepReason]


@dataclass
class IdleCheckSweepResult(BaseReconcilerResult):
    reports: list[IdleCheckSweepReport] = field(default_factory=list)

    @override
    def processed_count(self) -> int:
        return len(self.reports)

    @override
    def failed_count(self) -> int:
        return 0

    @override
    def decisions(self) -> Sequence[ReconcilerDecision]:
        return ()
