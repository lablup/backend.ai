"""Info types for the expiry-sweep reconcile stage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.manager.repositories.idle_checker.types import ExpiredIdleCheckBatchData
from ai.backend.manager.sokovan.reconciler.base import BaseReconcilerInfo


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
