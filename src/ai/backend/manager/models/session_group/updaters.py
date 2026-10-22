"""GuardedDataUpdater implementations for the session group."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.manager.data.session_group.types import (
    SessionGroupData,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.errors.session_group import SessionGroupInUseForUpdate
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.searchable_fields import SessionGroupSearchableFields
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.types import OptionalState

__all__ = ("SessionGroupUpdater",)


@dataclass
class SessionGroupUpdater(GuardedDataUpdater[SessionGroupRow, SessionGroupData]):
    """Changes a session group's placement policy.

    A group a replica group holds is refused as in use, as the purge does.
    """

    session_group_id: SessionGroupID
    placement_direction: OptionalState[SessionGroupPlacementDirection] = field(
        default_factory=OptionalState[SessionGroupPlacementDirection].nop
    )
    placement_enforcement: OptionalState[SessionGroupPlacementEnforcement] = field(
        default_factory=OptionalState[SessionGroupPlacementEnforcement].nop
    )

    @property
    @override
    def row_class(self) -> type[SessionGroupRow]:
        return SessionGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SessionGroupRow.id

    @override
    def target_id_value(self) -> SessionGroupID:
        return self.session_group_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=SessionGroupSearchableFields.linked.replica_groups.not_exists(),
                error=SessionGroupInUseForUpdate(
                    f"Session group {self.session_group_id} cannot be updated while a replica group uses it"
                ),
            ),
        )

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.placement_direction.update_dict(to_update, "placement_direction")
        self.placement_enforcement.update_dict(to_update, "placement_enforcement")
        return to_update

    @override
    def to_data(self, row: SessionGroupRow) -> SessionGroupData:
        return SessionGroupSearchableFields.own.to_data(row)
