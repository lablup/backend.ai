"""What a session group search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session_group.types import (
    SessionGroupData,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import SearchableField

__all__ = ("SessionGroupSearchableFields",)


class _SessionGroupOwnFields(RowDataConverter[SessionGroupRow, SessionGroupData]):
    """The session group's own columns."""

    id = SearchableField(
        SessionGroupRow.id, UUIDConditions(SessionGroupRow.id), ColumnOrder(SessionGroupRow.id)
    )
    domain_id = SearchableField(
        SessionGroupRow.domain_id,
        UUIDConditions(SessionGroupRow.domain_id),
        ColumnOrder(SessionGroupRow.domain_id),
    )
    project_id = SearchableField(
        SessionGroupRow.project_id,
        UUIDConditions(SessionGroupRow.project_id),
        ColumnOrder(SessionGroupRow.project_id),
    )
    owner_user_id = SearchableField(
        SessionGroupRow.owner_user_id,
        UUIDConditions(SessionGroupRow.owner_user_id),
        ColumnOrder(SessionGroupRow.owner_user_id),
    )
    placement_direction = SearchableField(
        SessionGroupRow.placement_direction,
        EnumConditions(SessionGroupRow.placement_direction, SessionGroupPlacementDirection),
        ColumnOrder(SessionGroupRow.placement_direction),
    )
    placement_enforcement = SearchableField(
        SessionGroupRow.placement_enforcement,
        EnumConditions(SessionGroupRow.placement_enforcement, SessionGroupPlacementEnforcement),
        ColumnOrder(SessionGroupRow.placement_enforcement),
    )
    created_at = SearchableField(
        SessionGroupRow.created_at,
        DateTimeConditions(SessionGroupRow.created_at),
        ColumnOrder(SessionGroupRow.created_at),
    )
    deleted_at = SearchableField(
        SessionGroupRow.deleted_at,
        DateTimeConditions(SessionGroupRow.deleted_at),
        ColumnOrder(SessionGroupRow.deleted_at),
    )

    @override
    def to_data(self, row: SessionGroupRow) -> SessionGroupData:
        return SessionGroupData(
            id=self.id.read(row),
            domain_id=self.domain_id.read(row),
            project_id=self.project_id.read(row),
            owner_user_id=self.owner_user_id.read(row),
            placement_direction=self.placement_direction.read(row),
            placement_enforcement=self.placement_enforcement.read(row),
            created_at=self.created_at.read(row),
            deleted_at=self.deleted_at.read(row),
        )


class _SessionGroupLinkedEntities:
    """How a session group connects to other entities."""

    replica_groups = ToManyCorrelation(
        ReplicaGroupRow, SessionGroupRow, ReplicaGroupRow.session_group_id == SessionGroupRow.id
    )
    """The replica groups holding the group. A group one holds belongs to a deployment."""


class SessionGroupSearchableFields:
    own = _SessionGroupOwnFields()
    linked = _SessionGroupLinkedEntities
