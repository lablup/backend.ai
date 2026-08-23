"""Reconcile writes of the v2 ops: a status transition and the history it leaves.

Every reconciled row (deployment, replica, replica group) advances the same way — the
status is written and the transition is recorded — so the pair is one primitive rather
than two calls a caller could get out of step. A repeated transition merges onto the
latest history row within the same scope instead of inserting another.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier, FieldData
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.mixins.history import ReconcileHistoryMixin
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


@dataclass
class ReconcileTransition[
    TOwnerID: EntityIdentifier,
    TStatusRow: Base,
    TStatusData,
    THistoryRow: Base,
    THistoryData: FieldData,
]:
    """One status change plus the history row recording it.

    ``match_conditions`` scope the search for the latest prior history — the same
    entity and category — so a recurrence merges onto that row.
    """

    owner_id: TOwnerID
    history_creator: FieldCreator[TOwnerID, THistoryRow, THistoryData]
    match_conditions: Sequence[QueryCondition]
    status_updater: DataUpdater[TStatusRow, TStatusData] | None = None


class V2ReconcileWriteOps(V2WriteOpsBase):
    """Status-with-history writes, bound to a single session."""

    async def apply_transitions(
        self, transitions: Sequence[ReconcileTransition[Any, Any, Any, Any, Any]]
    ) -> None:
        """Write each transition's status and history in this transaction."""
        for transition in transitions:
            if transition.status_updater is not None:
                await self._update_row_returning(
                    transition.status_updater.row_class,
                    transition.status_updater.target_id_column(),
                    transition.status_updater.target_id_value(),
                    transition.status_updater.build_values(),
                    transition.status_updater.integrity_error_checks,
                )
            await self._record_history(transition)

    async def _record_history(
        self, transition: ReconcileTransition[Any, Any, Any, Any, Any]
    ) -> None:
        new_row = cast(
            ReconcileHistoryMixin, transition.history_creator.build_row(transition.owner_id)
        )
        history_class = type(new_row)
        last = await self._latest_history(history_class, transition.match_conditions)
        if last is not None and last.should_merge_with(new_row):
            await self._sess.execute(
                sa.update(history_class)
                .where(history_class.id == last.id)
                .values(attempts=last.attempts + 1)
            )
            return
        await self._insert_row(
            cast(Base, new_row), transition.history_creator.integrity_error_checks()
        )

    async def _latest_history(
        self,
        history_class: type[ReconcileHistoryMixin],
        conditions: Sequence[QueryCondition],
    ) -> ReconcileHistoryMixin | None:
        """The newest history row in the scope the conditions name, locked for update."""
        query = sa.select(history_class)
        for condition in conditions:
            query = query.where(condition())
        query = query.order_by(sa.desc(history_class.created_at)).limit(1).with_for_update()
        return (await self._sess.execute(query)).scalars().first()
