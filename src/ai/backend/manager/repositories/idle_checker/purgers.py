from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow, SessionIdleCheckRow
from ai.backend.manager.repositories.base import BatchPurgerSpec
from ai.backend.manager.repositories.base.purger import PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair


@dataclass
class IdleCheckerPurgerSpec(PurgerSpec[IdleCheckerRow]):
    checker_id: IdleCheckerID

    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def pk_value(self) -> IdleCheckerID:
        return self.checker_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


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
