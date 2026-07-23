from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair
from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerInfo,
    BaseReconcilerResult,
    ReconcilerDecision,
)


@dataclass
class IdleCheckAssignmentSyncReconcileInfo(BaseReconcilerInfo):
    desired_pairs: Sequence[SessionIdleCheckPair]
    current_pairs: Sequence[SessionIdleCheckPair]
    current_time: datetime

    @override
    def entity_ids(self) -> Sequence[UUID]:
        all_pairs = (*self.desired_pairs, *self.current_pairs)
        session_ids = (pair.session_id for pair in all_pairs)
        return list(dict.fromkeys(session_ids))

    @override
    def now(self) -> datetime:
        return self.current_time


@dataclass
class IdleCheckAssignmentSyncResult(BaseReconcilerResult):
    current_time: datetime
    pairs_to_create: list[SessionIdleCheckPair] = field(default_factory=list)
    pairs_to_delete: list[SessionIdleCheckPair] = field(default_factory=list)

    @override
    def processed_count(self) -> int:
        return len(self.pairs_to_create) + len(self.pairs_to_delete)

    @override
    def failed_count(self) -> int:
        return 0

    @override
    def decisions(self) -> Sequence[ReconcilerDecision]:
        return ()
