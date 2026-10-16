"""Purge specs for session groups."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.session_group import SessionGroupEntityType, SessionGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.searchable_fields import SessionGroupSearchableFields
from ai.backend.manager.models.specs.purger import GuardedEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck, GuardCheck

__all__ = ("SessionGroupPurger",)


@dataclass(frozen=True)
class SessionGroupPurger(GuardedEntityPurger[SessionGroupRow, SessionGroupData]):
    """Removes a session group; its member sessions stay, their group id cleared by the FK.

    A group a replica group holds is answered for as not found.
    """

    group_id: SessionGroupID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.group_id

    @override
    def row_class(self) -> type[SessionGroupRow]:
        return SessionGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SessionGroupRow.id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=SessionGroupSearchableFields.linked.replica_groups.not_exists(),
                error=EntityNotFoundError(
                    f"Session group {self.group_id} not found",
                    entity_type=SessionGroupEntityType(),
                    operation=ActionOperationType.PURGE,
                ),
            ),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: SessionGroupRow) -> SessionGroupData:
        return SessionGroupSearchableFields.own.to_data(row)
