from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair
from ai.backend.manager.sokovan.reconciler.base import BaseReconcilerInfo


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
