"""What an audit log search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogScopeData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField


class _AuditLogScopeOwnFields(RowDataConverter[AuditLogScopeRow, AuditLogScopeData]):
    """A scope row's own columns."""

    field_id = SearchableField(
        AuditLogScopeRow.id,
        UUIDConditions(AuditLogScopeRow.id),
        ColumnOrder(AuditLogScopeRow.id),
    )
    audit_log_id = SearchableField(
        AuditLogScopeRow.audit_log_id,
        UUIDConditions(AuditLogScopeRow.audit_log_id),
        ColumnOrder(AuditLogScopeRow.audit_log_id),
    )
    scope_type = SearchableField(
        AuditLogScopeRow.scope_type,
        StringConditions(AuditLogScopeRow.scope_type),
        ColumnOrder(AuditLogScopeRow.scope_type),
    )
    scope_id = SearchableField(
        AuditLogScopeRow.scope_id,
        StringConditions(AuditLogScopeRow.scope_id),
        ColumnOrder(AuditLogScopeRow.scope_id),
    )

    @override
    def to_data(self, row: AuditLogScopeRow) -> AuditLogScopeData:
        return AuditLogScopeData(
            audit_log_id=AuditLogID(self.audit_log_id.read(row)),
            scope_type=self.scope_type.read(row),
            scope_id=self.scope_id.read(row),
        )


class AuditLogScopeSearchableFields:
    own = _AuditLogScopeOwnFields()


class _AuditLogOwnFields(RowDataConverter[AuditLogRow, AuditLogData]):
    """The audit record's own columns."""

    id = SearchableField(
        AuditLogRow.id, UUIDConditions(AuditLogRow.id), ColumnOrder(AuditLogRow.id)
    )
    action_id = SearchableField(
        AuditLogRow.action_id,
        UUIDConditions(AuditLogRow.action_id),
        ColumnOrder(AuditLogRow.action_id),
    )
    action_kind = SearchableField(
        AuditLogRow.action_kind,
        EnumConditions(AuditLogRow.action_kind, ActionKind),
        ColumnOrder(AuditLogRow.action_kind),
    )
    action_name = SearchableField(
        AuditLogRow.action_name,
        StringConditions(AuditLogRow.action_name),
        ColumnOrder(AuditLogRow.action_name),
    )
    entity_type = SearchableField(
        AuditLogRow.entity_type,
        StringConditions(AuditLogRow.entity_type),
        ColumnOrder(AuditLogRow.entity_type),
    )
    operation = SearchableField(
        AuditLogRow.operation,
        StringConditions(AuditLogRow.operation),
        ColumnOrder(AuditLogRow.operation),
    )
    created_at = SearchableField(
        AuditLogRow.created_at,
        DateTimeConditions(AuditLogRow.created_at),
        ColumnOrder(AuditLogRow.created_at),
    )
    description = SearchableField(
        AuditLogRow.description,
        StringConditions(AuditLogRow.description),
        ColumnOrder(AuditLogRow.description),
    )
    status = SearchableField(
        AuditLogRow.status,
        EnumConditions(AuditLogRow.status, OperationStatus),
        ColumnOrder(AuditLogRow.status),
    )
    target_entity_id = SearchableField(
        AuditLogRow.entity_id,
        StringConditions(AuditLogRow.entity_id),
        ColumnOrder(AuditLogRow.entity_id),
    )
    lookup_kind = SearchableField(
        AuditLogRow.lookup_kind,
        StringConditions(AuditLogRow.lookup_kind),
        ColumnOrder(AuditLogRow.lookup_kind),
    )
    lookup_key = SearchableField(
        AuditLogRow.lookup_key,
        StringConditions(AuditLogRow.lookup_key),
        ColumnOrder(AuditLogRow.lookup_key),
    )
    request_id = SearchableField(
        AuditLogRow.request_id,
        StringConditions(AuditLogRow.request_id),
        ColumnOrder(AuditLogRow.request_id),
    )
    triggered_by = SearchableField(
        AuditLogRow.triggered_by,
        StringConditions(AuditLogRow.triggered_by),
        ColumnOrder(AuditLogRow.triggered_by),
    )
    acted_as = SearchableField(
        AuditLogRow.acted_as,
        UUIDConditions(AuditLogRow.acted_as),
        ColumnOrder(AuditLogRow.acted_as),
    )
    duration = SearchableField(AuditLogRow.duration, None, ColumnOrder(AuditLogRow.duration))
    """No shared condition class covers ``sa.Interval``, so the filter slot stays empty."""
    client_ip = SearchableField(AuditLogRow.client_ip, None, None)
    """Sensitive: the address the request came from. Repeating a filter or an order
    recovers it even though the response carries it only for a reader allowed the row."""

    @override
    def to_data(self, row: AuditLogRow) -> AuditLogData:
        return AuditLogData(
            id=AuditLogID(self.id.read(row)),
            action_id=self.action_id.read(row),
            action_kind=self.action_kind.read(row),
            action_name=self.action_name.read(row),
            entity_type=self.entity_type.read(row),
            operation=self.operation.read(row),
            created_at=self.created_at.read(row),
            description=self.description.read(row),
            status=self.status.read(row),
            target_entity_id=self.target_entity_id.read(row),
            lookup_kind=self.lookup_kind.read(row),
            lookup_key=self.lookup_key.read(row),
            request_id=self.request_id.read(row),
            triggered_by=self.triggered_by.read(row),
            acted_as=self.acted_as.read(row),
            duration=self.duration.read(row),
            client_ip=self.client_ip.read(row),
        )


class _AuditLogNestedFields:
    """The scopes the audited run covered."""

    scopes = NestedSearchableField(
        AuditLogScopeSearchableFields.own,
        ToManyCorrelation(
            AuditLogScopeRow, AuditLogRow, AuditLogScopeRow.audit_log_id == AuditLogRow.id
        ),
    )


class AuditLogSearchableFields:
    own = _AuditLogOwnFields()
    nested = _AuditLogNestedFields
