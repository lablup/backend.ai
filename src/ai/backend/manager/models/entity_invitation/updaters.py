"""Update specs settling one entity invitation.

Three specs rather than one carrying the status, because they differ in who may run
them. The invitee holds no permission on the invitation — they were reached by email —
so their two are authorized by a guard matching that address. Withdrawing one is
authorized the ordinary way, through the entity the invitation offers.
"""

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
    "EntityInvitationCancelUpdater",
    "EntityInvitationRejectUpdater",
)


@dataclass
class _InviteeInvitationUpdater(GuardedDataUpdater[EntityInvitationRow, EntityInvitationData]):
    """What the invitee's two answers share: the row is pending, and it is theirs.

    The address is read back from ``users`` inside the statement, so an invitation
    addressed to somebody else reads as one that was not there.
    """

    invitation_id: EntityInvitationID
    invitee_user_id: UserID

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
        invitee_user_id = self.invitee_user_id

        def pending() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.status == EntityInvitationStatus.PENDING

        def addressed_to_invitee() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.invitee_email == (
                sa.select(UserRow.email).where(UserRow.uuid == invitee_user_id).scalar_subquery()
            )

        return [pending, addressed_to_invitee]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: EntityInvitationRow) -> EntityInvitationData:
        return row.to_data()


@dataclass
class EntityInvitationAcceptUpdater(_InviteeInvitationUpdater):
    """The invitee takes what was offered."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityInvitationStatus.ACCEPTED}


@dataclass
class EntityInvitationRejectUpdater(_InviteeInvitationUpdater):
    """The invitee turns down what was offered."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityInvitationStatus.REJECTED}


@dataclass
class EntityInvitationCancelUpdater(GuardedDataUpdater[EntityInvitationRow, EntityInvitationData]):
    """The offer is withdrawn before it was answered.

    No address guard: whoever may reach the entity the invitation offers may withdraw
    it, and the permission check upstream is what says so.
    """

    invitation_id: EntityInvitationID

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
        return {"status": EntityInvitationStatus.CANCELED}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: EntityInvitationRow) -> EntityInvitationData:
        return row.to_data()
