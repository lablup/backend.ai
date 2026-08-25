"""Reconcile writes: a status transition and the history it leaves.

Every reconciled row (deployment, replica, replica group, session) advances the same
way — the status is written and the transition is recorded — so the pair is one
primitive rather than two calls a caller could get out of step. A repeated transition
merges onto the latest history row within the same scope instead of inserting another.

Two shapes: one row named by its id, and a batch selected by conditions whose owners
share one history table. The batch reads every owner's latest row in one query, so a
scheduling cycle covering hundreds of sessions costs one read.

The primitive sits here rather than in the general write ops because reconciliation is
the only thing that has it: :class:`ReconcileWriteOps` extends the general ops, so a
repository handed the general ones never sees it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityIdentifier, FieldData
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.mixins.history import ReconcileHistoryMixin
from ai.backend.manager.models.specs.creator import FieldCreator, FieldToCreate
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


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


@dataclass
class BatchReconcileTransition[
    TOwnerID: EntityIdentifier,
    TStatusRow: Base,
    TStatusData,
    THistoryRow: Base,
    THistoryData: FieldData,
]:
    """One condition-selected status update plus the history each owner leaves.

    ``owner_column`` is the history column naming the owner, so the latest prior row
    of every owner is read in one query rather than one per transition.
    """

    histories: Sequence[FieldToCreate[TOwnerID, THistoryRow, THistoryData]]
    owner_column: InstrumentedAttribute[Any]
    status_updater: DataBatchUpdater[TStatusRow, TStatusData] | None = None


class ReconcileWriteOps(V2WriteOps):
    """The general v2 write ops plus the status-with-history transition."""

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

    async def apply_batch_transition[
        TOwnerID: EntityIdentifier,
        TStatusRow: Base,
        TStatusData,
        THistoryRow: Base,
        THistoryData: FieldData,
    ](
        self,
        transition: BatchReconcileTransition[
            TOwnerID, TStatusRow, TStatusData, THistoryRow, THistoryData
        ],
    ) -> list[TStatusData]:
        """Write the status of every row the spec selects and the history the
        transition leaves, in this transaction; a repeat merges onto each owner's
        latest row instead of inserting another.

        Returns what the status update wrote — empty when the transition carries none.
        """
        updated: list[TStatusData] = []
        if transition.status_updater is not None:
            updated = await self.batch_update_in_global(transition.status_updater)
        await self._record_batch_history(transition.histories, transition.owner_column)
        return updated

    async def _record_batch_history[TOwnerID: EntityIdentifier, TRow: Base, TData: FieldData](
        self,
        histories: Sequence[FieldToCreate[TOwnerID, TRow, TData]],
        owner_column: InstrumentedAttribute[Any],
    ) -> None:
        if not histories:
            return
        new_rows = [cast(ReconcileHistoryMixin, h.creator.build_row(h.owner_id)) for h in histories]
        history_class = type(new_rows[0])
        latest = await self._latest_history_per_owner(
            history_class, owner_column, [h.owner_id for h in histories]
        )
        merge_ids: list[UUID] = []
        rows_to_insert: list[Base] = []
        for new_row, history in zip(new_rows, histories, strict=True):
            last = latest.get(history.owner_id)
            if last is not None and last.should_merge_with(new_row):
                merge_ids.append(last.id)
            else:
                rows_to_insert.append(cast(Base, new_row))
        if merge_ids:
            await self._sess.execute(
                sa.update(history_class)
                .where(history_class.id.in_(merge_ids))
                .values(attempts=history_class.attempts + 1)
            )
        if rows_to_insert:
            await self._insert_rows(rows_to_insert, histories[0].creator.integrity_error_checks())

    async def _latest_history_per_owner(
        self,
        history_class: type[ReconcileHistoryMixin],
        owner_column: InstrumentedAttribute[Any],
        owner_ids: Sequence[EntityIdentifier],
    ) -> dict[Any, ReconcileHistoryMixin]:
        """The newest history row of each owner, in one query."""
        query = (
            sa.select(history_class)
            .where(owner_column.in_(owner_ids))
            .distinct(owner_column)
            .order_by(owner_column, sa.desc(history_class.created_at))
        )
        rows = (await self._sess.execute(query)).scalars().all()
        return {getattr(row, owner_column.key): row for row in rows}
