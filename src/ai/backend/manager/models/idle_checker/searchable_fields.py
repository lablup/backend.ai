"""What an idle checker search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckPhase
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import (
    IdleCheckerAssignmentData,
    IdleCheckerData,
    SessionIdleCheckData,
)
from ai.backend.manager.models.base import StrEnumType
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.specs.conditions.array import ArrayConditions
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _IdleCheckerOwnFields(RowDataConverter[IdleCheckerRow, IdleCheckerData]):
    """The idle checker's own columns."""

    id = SearchableField(
        IdleCheckerRow.id, UUIDConditions(IdleCheckerRow.id), ColumnOrder(IdleCheckerRow.id)
    )
    name = SearchableField(
        IdleCheckerRow.name,
        StringConditions(IdleCheckerRow.name),
        ColumnOrder(IdleCheckerRow.name),
    )
    description = SearchableField(
        IdleCheckerRow.description,
        StringEqualityConditions(IdleCheckerRow.description),
        ColumnOrder(IdleCheckerRow.description),
    )
    checker_type = SearchableField(
        IdleCheckerRow.checker_type,
        EnumConditions(IdleCheckerRow.checker_type, CheckerType),
        ColumnOrder(IdleCheckerRow.checker_type),
    )
    target_session_types = SearchableField(
        IdleCheckerRow.target_session_types,
        ArrayConditions(
            IdleCheckerRow.target_session_types, StrEnumType(SessionTypes, use_name=True)
        ),
        None,
    )
    """Impossible to order: an array."""
    initial_grace_period_seconds = SearchableField(
        IdleCheckerRow.initial_grace_period_seconds,
        IntConditions(IdleCheckerRow.initial_grace_period_seconds),
        ColumnOrder(IdleCheckerRow.initial_grace_period_seconds),
    )
    spec = SearchableField(IdleCheckerRow.spec, None, None)
    """Impossible: a JSON document of the checker's settings."""
    created_at = SearchableField(
        IdleCheckerRow.created_at,
        DateTimeConditions(IdleCheckerRow.created_at),
        ColumnOrder(IdleCheckerRow.created_at),
    )
    updated_at = SearchableField(
        IdleCheckerRow.updated_at,
        DateTimeConditions(IdleCheckerRow.updated_at),
        ColumnOrder(IdleCheckerRow.updated_at),
    )

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return IdleCheckerData(
            id=IdleCheckerID(self.id.read(row)),
            name=self.name.read(row),
            description=self.description.read(row),
            checker_type=self.checker_type.read(row),
            target_session_types=self.target_session_types.read(row),
            initial_grace_period_seconds=self.initial_grace_period_seconds.read(row),
            spec=self.spec.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class IdleCheckerSearchableFields:
    own = _IdleCheckerOwnFields()


class _IdleCheckerAssignmentOwnFields(
    RowDataConverter[IdleCheckerBindingRow, IdleCheckerAssignmentData]
):
    """The binding row's own columns."""

    field_id = SearchableField(
        IdleCheckerBindingRow.id,
        UUIDConditions(IdleCheckerBindingRow.id),
        ColumnOrder(IdleCheckerBindingRow.id),
    )
    scope_type = SearchableField(
        IdleCheckerBindingRow.scope_type,
        StringConditions(IdleCheckerBindingRow.scope_type),
        ColumnOrder(IdleCheckerBindingRow.scope_type),
    )
    scope_id = SearchableField(
        IdleCheckerBindingRow.scope_id,
        UUIDConditions(IdleCheckerBindingRow.scope_id),
        ColumnOrder(IdleCheckerBindingRow.scope_id),
    )
    idle_checker_id = SearchableField(
        IdleCheckerBindingRow.idle_checker_id,
        UUIDConditions(IdleCheckerBindingRow.idle_checker_id),
        ColumnOrder(IdleCheckerBindingRow.idle_checker_id),
    )
    enabled = SearchableField(
        IdleCheckerBindingRow.enabled,
        BoolConditions(IdleCheckerBindingRow.enabled),
        ColumnOrder(IdleCheckerBindingRow.enabled),
    )
    created_at = SearchableField(
        IdleCheckerBindingRow.created_at,
        DateTimeConditions(IdleCheckerBindingRow.created_at),
        ColumnOrder(IdleCheckerBindingRow.created_at),
    )
    updated_at = SearchableField(
        IdleCheckerBindingRow.updated_at,
        DateTimeConditions(IdleCheckerBindingRow.updated_at),
        ColumnOrder(IdleCheckerBindingRow.updated_at),
    )

    @override
    def to_data(self, row: IdleCheckerBindingRow) -> IdleCheckerAssignmentData:
        return IdleCheckerAssignmentData(
            id=IdleCheckerAssignmentID(self.field_id.read(row)),
            scope_type=EntityType.from_name(self.scope_type.read(row)),
            scope_id=self.scope_id.read(row),
            idle_checker_id=IdleCheckerID(self.idle_checker_id.read(row)),
            enabled=self.enabled.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class IdleCheckerAssignmentSearchableFields:
    own = _IdleCheckerAssignmentOwnFields()


class _SessionIdleCheckOwnFields(RowDataConverter[SessionIdleCheckRow, SessionIdleCheckData]):
    """One session's state for one checker."""

    session_id = SearchableField(
        SessionIdleCheckRow.session_id,
        UUIDConditions(SessionIdleCheckRow.session_id),
        ColumnOrder(SessionIdleCheckRow.session_id),
    )
    idle_checker_id = SearchableField(
        SessionIdleCheckRow.idle_checker_id,
        UUIDConditions(SessionIdleCheckRow.idle_checker_id),
        ColumnOrder(SessionIdleCheckRow.idle_checker_id),
    )
    expire_at = SearchableField(
        SessionIdleCheckRow.expire_at,
        DateTimeConditions(SessionIdleCheckRow.expire_at),
        ColumnOrder(SessionIdleCheckRow.expire_at),
    )
    last_status = SearchableField(
        SessionIdleCheckRow.last_status,
        EnumConditions(SessionIdleCheckRow.last_status, IdleCheckPhase),
        ColumnOrder(SessionIdleCheckRow.last_status),
    )
    last_message = SearchableField(
        SessionIdleCheckRow.last_message,
        StringEqualityConditions(SessionIdleCheckRow.last_message),
        ColumnOrder(SessionIdleCheckRow.last_message),
    )
    is_manual = SearchableField(
        SessionIdleCheckRow.is_manual,
        BoolConditions(SessionIdleCheckRow.is_manual),
        ColumnOrder(SessionIdleCheckRow.is_manual),
    )
    manually_triggered_by = SearchableField(
        SessionIdleCheckRow.manually_triggered_by,
        UUIDConditions(SessionIdleCheckRow.manually_triggered_by),
        ColumnOrder(SessionIdleCheckRow.manually_triggered_by),
    )
    updated_at = SearchableField(
        SessionIdleCheckRow.updated_at,
        DateTimeConditions(SessionIdleCheckRow.updated_at),
        ColumnOrder(SessionIdleCheckRow.updated_at),
    )

    @override
    def to_data(self, row: SessionIdleCheckRow) -> SessionIdleCheckData:
        return SessionIdleCheckData(
            session_id=self.session_id.read(row),
            idle_checker_id=self.idle_checker_id.read(row),
            expire_at=self.expire_at.read(row),
            last_status=self.last_status.read(row),
            last_message=self.last_message.read(row),
            is_manual=self.is_manual.read(row),
            manually_triggered_by=self.manually_triggered_by.read(row),
        )


class SessionIdleCheckSearchableFields:
    own = _SessionIdleCheckOwnFields()
