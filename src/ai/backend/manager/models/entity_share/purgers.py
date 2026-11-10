"""Delete specs for the entity shares table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.purger import EntityBatchPurger
from ai.backend.manager.models.specs.types import ConflictCheck

__all__ = ("EntitySharePendingOfferBatchPurger",)


@dataclass
class EntitySharePendingOfferBatchPurger(EntityBatchPurger[EntityShareRow, EntityShareID]):
    """Clears the open offers of the named entities to one address, each with its graph.

    Used when the address comes to own those entities.
    """

    entity_type: EntityType
    entity_ids: Sequence[UUID]
    recipient_email: str

    @override
    def entity_id(self, row: EntityShareRow) -> EntityShareID:
        return EntityShareID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[EntityShareRow]]:
        return sa.select(EntityShareRow).where(
            EntityShareRow.target_entity_type == self.entity_type,
            EntityShareRow.target_entity_id.in_(self.entity_ids),
            EntityShareRow.recipient_email == self.recipient_email,
            EntityShareRow.status == EntityShareStatus.PENDING,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareID:
        return EntityShareID(row.id)
