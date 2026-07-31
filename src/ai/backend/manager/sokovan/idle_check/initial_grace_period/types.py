from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.manager.repositories.idle_checker.types import (
    InitialGracePeriodBatchData,
    SessionIdleCheckPair,
)
from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerInfo,
    BaseReconcilerResult,
    ReconcilerDecision,
)


@dataclass
class IdleCheckInitialGracePeriodReconcileInfo(BaseReconcilerInfo):
    batch: InitialGracePeriodBatchData

    @override
    def entity_ids(self) -> Sequence[UUID]:
        return list(dict.fromkeys(check.pair.session_id for check in self.batch.checks))

    @override
    def now(self) -> datetime:
        return self.batch.now


@dataclass
class IdleCheckInitialGracePeriodResult(BaseReconcilerResult):
    pairs_to_ready: list[SessionIdleCheckPair] = field(default_factory=list)

    @override
    def processed_count(self) -> int:
        return len(self.pairs_to_ready)

    @override
    def failed_count(self) -> int:
        return 0

    @override
    def decisions(self) -> Sequence[ReconcilerDecision]:
        return ()
