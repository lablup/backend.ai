"""Lookup implementations for the entity shares table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType, EntityShareID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.lookup import DataLookup

__all__ = ("HeldShareLookup",)


@dataclass
class HeldShareLookup(DataLookup[EntityShareRow, EntityShareID]):
    """Resolves a recipient and a target into the accepted share standing between them.

    A partial unique index holds one live row per pair.
    """

    recipient: EntityIdentifier
    target: EntityIdentifier

    @override
    def row_class(self) -> type[EntityShareRow]:
        return EntityShareRow

    @override
    def entity_type(self) -> EntityType:
        return EntityShareEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: EntityShareRow.recipient_entity_type == self.recipient.entity_type(),
            lambda: EntityShareRow.recipient_entity_id == self.recipient,
            lambda: EntityShareRow.target_entity_type == self.target.entity_type(),
            lambda: EntityShareRow.target_entity_id == self.target,
            lambda: EntityShareRow.status == EntityShareStatus.ACCEPTED,
        ]

    @override
    def to_entity_id(self, row: EntityShareRow) -> EntityShareID:
        return EntityShareID(row.id)
