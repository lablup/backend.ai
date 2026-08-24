"""Update spec for entity invitation status transitions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.entity_invitation.types import (
    EntityInvitationData,
    EntityInvitationStatus,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "EntityInvitationAcceptUpdater",
    "EntityInvitationStatusUpdater",
)


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


@dataclass
class EntityInvitationAcceptUpdater(GuardedDataUpdater[EntityInvitationRow, EntityInvitationData]):
    """Settles one pending invitation as accepted, on behalf of its invitee.

    The second guard matches the accepter's own address against the row, so an
    invitation addressed to somebody else reads as one that was not there.
    """

    invitation_id: EntityInvitationID
    accepter_user_id: UserID

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
        accepter_user_id = self.accepter_user_id

        def pending() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.status == EntityInvitationStatus.PENDING

        def addressed_to_accepter() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.invitee_email == (
                sa.select(UserRow.email).where(UserRow.uuid == accepter_user_id).scalar_subquery()
            )

        return [pending, addressed_to_accepter]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityInvitationStatus.ACCEPTED}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: EntityInvitationRow) -> EntityInvitationData:
        return row.to_data()
