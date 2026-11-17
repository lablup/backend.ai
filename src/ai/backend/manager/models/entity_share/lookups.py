"""Lookup implementations for the entity shares table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType, EntityShareID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.lookup import DataLookup

__all__ = (
    "EntityShareAnsweringScopeLookup",
    "HeldShareLookup",
)


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


@dataclass
class EntityShareAnsweringScopeLookup(DataLookup[EntityShareRow, EntityIdentifier]):
    """Resolves a share into the scope that answers it.

    A share addressed to a project is answered by that project. Any other share names a
    person, by node or by address, and the person calling answers it.
    """

    share_id: EntityShareID
    caller_user_id: UserID

    @override
    def row_class(self) -> type[EntityShareRow]:
        return EntityShareRow

    @override
    def entity_type(self) -> EntityType:
        return EntityShareEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: EntityShareRow.id == self.share_id]

    @override
    def to_entity_id(self, row: EntityShareRow) -> EntityIdentifier:
        if row.recipient_entity_type == ProjectEntityType() and row.recipient_entity_id is not None:
            return ProjectID(row.recipient_entity_id)
        return self.caller_user_id
