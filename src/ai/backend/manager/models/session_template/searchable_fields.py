"""What a session template search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session_template.types import SessionTemplateData, TemplateType
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _SessionTemplateOwnFields(RowDataConverter[SessionTemplateRow, SessionTemplateData]):
    """The session template's own columns. ``template`` is JSONB."""

    id = SearchableField(
        SessionTemplateRow.id,
        UUIDConditions(SessionTemplateRow.id),
        ColumnOrder(SessionTemplateRow.id),
    )
    created_at = SearchableField(
        SessionTemplateRow.created_at,
        DateTimeConditions(SessionTemplateRow.created_at),
        ColumnOrder(SessionTemplateRow.created_at),
    )
    is_active = SearchableField(
        SessionTemplateRow.is_active,
        BoolConditions(SessionTemplateRow.is_active),
        ColumnOrder(SessionTemplateRow.is_active),
    )
    domain_name = SearchableField(
        SessionTemplateRow.domain_name,
        StringConditions(SessionTemplateRow.domain_name),
        ColumnOrder(SessionTemplateRow.domain_name),
    )
    group_id = SearchableField(
        SessionTemplateRow.group_id,
        UUIDConditions(SessionTemplateRow.group_id),
        ColumnOrder(SessionTemplateRow.group_id),
    )
    user_uuid = SearchableField(
        SessionTemplateRow.user_uuid,
        UUIDConditions(SessionTemplateRow.user_uuid),
        ColumnOrder(SessionTemplateRow.user_uuid),
    )
    type = SearchableField(
        SessionTemplateRow.type,
        EnumConditions(SessionTemplateRow.type, TemplateType),
        ColumnOrder(SessionTemplateRow.type),
    )
    name = SearchableField(
        SessionTemplateRow.name,
        StringConditions(SessionTemplateRow.name),
        ColumnOrder(SessionTemplateRow.name),
    )
    template = SearchableField(SessionTemplateRow.template, None, None)

    @override
    def to_data(self, row: SessionTemplateRow) -> SessionTemplateData:
        return SessionTemplateData(
            id=self.id.read(row),
            created_at=self.created_at.read(row),
            is_active=self.is_active.read(row),
            domain_name=self.domain_name.read(row),
            group_id=self.group_id.read(row),
            user_uuid=self.user_uuid.read(row),
            type=self.type.read(row),
            name=self.name.read(row),
            template=self.template.read(row),
        )


class SessionTemplateSearchableFields:
    own = _SessionTemplateOwnFields()
