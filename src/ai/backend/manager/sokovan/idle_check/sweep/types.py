"""Info types for the expiry-sweep reconcile stage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import override
from uuid import UUID

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


@dataclass
class IdleCheckSweepResult(BaseReconcilerResult):
    session_ids: list[SessionId] = field(default_factory=list)

    @override
    def processed_count(self) -> int:
        return len(self.session_ids)

    @override
    def failed_count(self) -> int:
        return 0

    @override
    def decisions(self) -> Sequence[ReconcilerDecision]:
        return ()
