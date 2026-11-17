"""Lookup implementations for the entity shares table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.entity_share import EntityShareEntityType, EntityShareID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

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
class EntityShareAnsweringScopeLookup(DataLookup[VirtualEntityRow, RuntimeEntityID]):
    """Resolves a share into the scope that answers it: the node it is addressed to.

    A share addressed by an email holds no node until it is answered, so the user holding
    that address answers it.
    """

    share_id: EntityShareID

    @override
    def row_class(self) -> type[VirtualEntityRow]:
        return VirtualEntityRow

    @override
    def entity_type(self) -> EntityType:
        return EntityShareEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        share_id = self.share_id

        def addressed() -> sa.sql.expression.ColumnElement[bool]:
            named = sa.tuple_(VirtualEntityRow.entity_type, VirtualEntityRow.entity_id).in_(
                sa.select(
                    EntityShareRow.recipient_entity_type, EntityShareRow.recipient_entity_id
                ).where(
                    EntityShareRow.id == share_id,
                    EntityShareRow.recipient_entity_type.is_not(None),
                )
            )
            by_email = sa.and_(
                VirtualEntityRow.entity_type == UserEntityType(),
                VirtualEntityRow.entity_id.in_(
                    sa.select(UserRow.uuid)
                    .join(EntityShareRow, EntityShareRow.recipient_email == UserRow.email)
                    .where(
                        EntityShareRow.id == share_id,
                        EntityShareRow.recipient_entity_type.is_(None),
                    )
                ),
            )
            return sa.or_(named, by_email)

        return [addressed]

    @override
    def to_entity_id(self, row: VirtualEntityRow) -> RuntimeEntityID:
        return RuntimeEntityID(row.entity_type, row.entity_id)
