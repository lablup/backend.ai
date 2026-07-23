from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.models.idle_checker.row import SessionIdleCheckRow
from ai.backend.manager.repositories.base import BatchPurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair


@dataclass
class SessionIdleCheckBatchPurgerSpec(BatchPurgerSpec[SessionIdleCheckRow]):
    pairs: Sequence[SessionIdleCheckPair]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionIdleCheckRow]]:
        pair_values = [(pair.session_id, pair.checker_id) for pair in self.pairs]
        return sa.select(SessionIdleCheckRow).where(
            sa.tuple_(
                SessionIdleCheckRow.session_id,
                SessionIdleCheckRow.idle_checker_id,
            ).in_(pair_values),
            SessionIdleCheckRow.last_status != IdleCheckPhase.IDLE_EXPIRED,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
