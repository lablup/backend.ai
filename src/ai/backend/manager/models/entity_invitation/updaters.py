"""Update spec for entity invitation status transitions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.manager.data.entity_invitation.types import (
    EntityInvitationData,
    EntityInvitationStatus,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater

__all__ = ("EntityInvitationStatusUpdater",)


@dataclass
class EntityInvitationStatusUpdater(GuardedDataUpdater[EntityInvitationRow, EntityInvitationData]):
    """Settles one pending invitation.

    The guard carries ``PENDING`` into the statement, so an invitation already
    answered is left alone and the caller is told nothing was written rather than
    overwriting an earlier answer.
    """

    invitation_id: EntityInvitationID
    status: EntityInvitationStatus

    @property
    @override
    def row_class(self) -> type[EntityInvitationRow]:
        return EntityInvitationRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityInvitationRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.invitation_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        def pending() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.status == EntityInvitationStatus.PENDING

        return [pending]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": self.status}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: EntityInvitationRow) -> EntityInvitationData:
        return row.to_data()
