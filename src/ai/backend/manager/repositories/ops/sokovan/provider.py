"""Sokovan DB ops: the reconcile transition+history primitive on top of the RBAC ops.

``apply_transition`` is the single shared way every reconcile entity (session,
deployment, route, replica group) advances a status and records it in history, so the
two never diverge per category. It reads the latest history within the same scope
(``match_conditions``) FOR UPDATE, then merges the recurrence onto it or inserts a new
row — all in one transaction. Generic over the status and history row types.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import final

import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.mixins.history import ReconcileHistoryMixin
from ai.backend.manager.repositories.base import Creator, Updater, execute_updater
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider, RBACWriteOps


@dataclass
class Transition[TStatusRow: Base, THistoryRow: ReconcileHistoryMixin]:
    """One status transition plus the new history row to record it.

    ``match_conditions`` scope the search for the latest prior history (same entity and
    category); the new history creator carries this transition's sub_steps.
    """

    new_history: Creator[THistoryRow]
    match_conditions: Sequence[QueryCondition]
    status_updater: Updater[TStatusRow] | None = None


@final
class SokovanWriteOps(RBACWriteOps):
    """RBAC write ops plus the reconcile transition+history primitive."""

    async def bulk_apply_transitions[TStatusRow: Base, THistoryRow: ReconcileHistoryMixin](
        self,
        transitions: Sequence[Transition[TStatusRow, THistoryRow]],
    ) -> None:
        for transition in transitions:
            if transition.status_updater is not None:
                await execute_updater(self._sess, transition.status_updater)
            new_row = transition.new_history.spec.build_row()
            history_class = type(new_row)
            query = sa.select(history_class)
            for condition in transition.match_conditions:
                query = query.where(condition())
            query = query.order_by(history_class.created_at.desc()).limit(1).with_for_update()
            last = (await self._sess.execute(query)).scalars().first()
            if last is not None and last.should_merge_with(new_row):
                await self._sess.execute(
                    sa.update(history_class)
                    .where(history_class.id == last.id)
                    .values(attempts=last.attempts + 1)
                )
            else:
                self._sess.add(new_row)
                await self._sess.flush()


@final
class SokovanOpsProvider(RBACOpsProvider):
    """Hands out :class:`SokovanWriteOps` for the read-write surface."""

    @asynccontextmanager
    async def write_ops(self) -> AsyncIterator[SokovanWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield SokovanWriteOps(sess)
