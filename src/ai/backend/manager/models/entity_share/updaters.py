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

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.entity_share.types import (
    EntityShareData,
    EntityShareStatus,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "EntityShareAcceptUpdater",
    "EntityShareCancelUpdater",
    "EntityShareRejectUpdater",
)


@dataclass
class _RecipientInvitationUpdater(GuardedDataUpdater[EntityShareRow, EntityShareData]):
    """What the invitee's two answers share: the row is pending, and it is theirs.

    The address is read back from ``users`` inside the statement, so an invitation
    addressed to somebody else reads as one that was not there.
    """

    share_id: EntityShareID
    recipient_user_id: UserID

    @property
    @override
    def row_class(self) -> type[EntityShareRow]:
        return EntityShareRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityShareRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.share_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        recipient_user_id = self.recipient_user_id

        def pending() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.status == EntityShareStatus.PENDING

        def addressed_to_invitee() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.recipient_email == (
                sa.select(UserRow.email).where(UserRow.uuid == recipient_user_id).scalar_subquery()
            )

        return [pending, addressed_to_invitee]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()


@dataclass
class EntityShareAcceptUpdater(_RecipientInvitationUpdater):
    """The invitee takes what was offered."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityShareStatus.ACCEPTED}


@dataclass
class EntityShareRejectUpdater(_RecipientInvitationUpdater):
    """The invitee turns down what was offered."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityShareStatus.REJECTED}


@dataclass
class EntityShareCancelUpdater(GuardedDataUpdater[EntityShareRow, EntityShareData]):
    """The offer is withdrawn before it was answered.

    No address guard: whoever may reach the entity the invitation offers may withdraw
    it, and the permission check upstream is what says so.
    """

    share_id: EntityShareID

    @property
    @override
    def row_class(self) -> type[EntityShareRow]:
        return EntityShareRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityShareRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.share_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        def pending() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.status == EntityShareStatus.PENDING

        return [pending]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityShareStatus.CANCELED}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()
