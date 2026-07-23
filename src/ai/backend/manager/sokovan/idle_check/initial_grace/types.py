from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.manager.repositories.idle_checker.types import (
    InitialGracePeriodBatchData,
)
from ai.backend.manager.sokovan.reconciler.base import BaseReconcilerInfo


@dataclass
class IdleCheckInitialGraceReconcileInfo(BaseReconcilerInfo):
    batch: InitialGracePeriodBatchData

    @override
    def entity_ids(self) -> Sequence[UUID]:
        return list(dict.fromkeys(check.pair.session_id for check in self.batch.checks))

    @override
    def now(self) -> datetime:
        return self.batch.now
