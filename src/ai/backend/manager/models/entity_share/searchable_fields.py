"""What an entity share search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.entity_share.types import EntityShareData, EntityShareStatus
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField

__all__ = ("EntityShareSearchableFields",)


class _EntityShareOwnFields(RowDataConverter[EntityShareRow, EntityShareData]):
    """The share's own columns.

    Both ends name a graph node by a type and an id, so each pair is read as two
    columns and handed to the data type as one node.
    """

    id = SearchableField(
        EntityShareRow.id, UUIDConditions(EntityShareRow.id), ColumnOrder(EntityShareRow.id)
    )
    sharer_user_id = SearchableField(
        EntityShareRow.sharer_user_id,
        UUIDConditions(EntityShareRow.sharer_user_id),
        ColumnOrder(EntityShareRow.sharer_user_id),
    )
    recipient_entity_type = SearchableField(
        EntityShareRow.recipient_entity_type,
        StringConditions(EntityShareRow.recipient_entity_type),
        ColumnOrder(EntityShareRow.recipient_entity_type),
    )
    recipient_entity_id = SearchableField(
        EntityShareRow.recipient_entity_id,
        UUIDConditions(EntityShareRow.recipient_entity_id),
        ColumnOrder(EntityShareRow.recipient_entity_id),
    )
    recipient_email = SearchableField(
        EntityShareRow.recipient_email,
        StringConditions(EntityShareRow.recipient_email),
        ColumnOrder(EntityShareRow.recipient_email),
    )
    target_entity_type = SearchableField(
        EntityShareRow.target_entity_type,
        StringConditions(EntityShareRow.target_entity_type),
        ColumnOrder(EntityShareRow.target_entity_type),
    )
    target_entity_id = SearchableField(
        EntityShareRow.target_entity_id,
        UUIDConditions(EntityShareRow.target_entity_id),
        ColumnOrder(EntityShareRow.target_entity_id),
    )
    permission_cap = SearchableField(
        EntityShareRow.permission_cap,
        EnumConditions(EntityShareRow.permission_cap, Permission),
        ColumnOrder(EntityShareRow.permission_cap),
    )
    expires_at = SearchableField(
        EntityShareRow.expires_at,
        DateTimeConditions(EntityShareRow.expires_at),
        ColumnOrder(EntityShareRow.expires_at),
    )
    status = SearchableField(
        EntityShareRow.status,
        EnumConditions(EntityShareRow.status, EntityShareStatus),
        ColumnOrder(EntityShareRow.status),
    )
    created_at = SearchableField(
        EntityShareRow.created_at,
        DateTimeConditions(EntityShareRow.created_at),
        ColumnOrder(EntityShareRow.created_at),
    )
    updated_at = SearchableField(
        EntityShareRow.updated_at,
        DateTimeConditions(EntityShareRow.updated_at),
        ColumnOrder(EntityShareRow.updated_at),
    )

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return EntityShareData(
            id=self.id.read(row),
            sharer_user_id=self.sharer_user_id.read(row),
            recipient=self._recipient(row),
            recipient_email=self.recipient_email.read(row),
            target=RuntimeEntityID(
                self.target_entity_type.read(row), self.target_entity_id.read(row)
            ),
            permission_cap=self.permission_cap.read(row),
            expires_at=self.expires_at.read(row),
            status=self.status.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )

    def _recipient(self, row: EntityShareRow) -> RuntimeEntityID | None:
        """A recipient still addressed by an email alone holds no node yet."""
        entity_type = self.recipient_entity_type.read(row)
        entity_id = self.recipient_entity_id.read(row)
        if entity_type is None or entity_id is None:
            return None
        return RuntimeEntityID(entity_type, entity_id)


class EntityShareSearchableFields:
    own = _EntityShareOwnFields()
