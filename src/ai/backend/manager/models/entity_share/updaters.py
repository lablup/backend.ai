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

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.data.entity_share.types import (
    EntityShareData,
    EntityShareStatus,
)
from ai.backend.manager.errors.entity_share import EntityShareNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "EntityShareAcceptUpdater",
    "EntityShareCancelUpdater",
    "EntityShareLeaveUpdater",
    "EntityShareRejectUpdater",
    "EntityShareRevokeUpdater",
)


@dataclass
class _RecipientInvitationUpdater(GuardedDataUpdater[EntityShareRow, EntityShareData]):
    """What the receiving side's two answers share: the offer is open, and it is theirs.

    Open is pending and still in time. An offer whose moment has passed reads as one
    that was not there, which is what expiry means without a sweep writing a state, and
    an offer with no moment stays open.

    Theirs means addressed to the scope answering. A person is addressed two ways, by
    the node they hold and by the address that reached them before they had an account,
    so both are read back inside the statement.
    """

    share_id: EntityShareID
    answering_scope: EntityIdentifier

    @property
    @override
    def row_class(self) -> type[EntityShareRow]:
        return EntityShareRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityShareRow.id

    @override
    def target_id_value(self) -> EntityShareID:
        return self.share_id

    def addressed_to_scope(self) -> QueryCondition:
        """The offer is addressed to the scope answering.

        A person is addressed two ways, by the node they hold and by the address that
        reached them before they had an account, so both are read back here.
        """
        scope = self.answering_scope

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            named = sa.and_(
                EntityShareRow.recipient_entity_type == scope.entity_type(),
                EntityShareRow.recipient_entity_id == scope,
            )
            if scope.entity_type() != UserEntityType():
                return named
            return sa.or_(
                named,
                EntityShareRow.recipient_email
                == (sa.select(UserRow.email).where(UserRow.uuid == scope).scalar_subquery()),
            )

        return inner

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        def pending() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.status == EntityShareStatus.PENDING

        def in_time() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                EntityShareRow.expires_at.is_(None),
                EntityShareRow.expires_at > sa.func.now(),
            )

        return (
            GuardCheck(
                condition=pending,
                error=EntityShareNotFound(f"No open offer {self.share_id} to answer"),
            ),
            GuardCheck(
                condition=in_time,
                error=EntityShareNotFound(f"Offer {self.share_id} has expired"),
            ),
            GuardCheck(
                condition=self.addressed_to_scope(),
                error=EntityShareNotFound(
                    f"Offer {self.share_id} is not addressed to {self.answering_scope}"
                ),
            ),
        )

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()


@dataclass
class EntityShareAcceptUpdater(_RecipientInvitationUpdater):
    """The receiving side takes what was offered.

    Settling records the scope that answered. An offer that named one already carries
    the same, because the guard would not have matched otherwise; an offer that reached
    an address gains it here, and from then on an accepted row always names one.

    The moment is cleared with it: a share that was taken does not run out, and only an
    offer still waiting has one.
    """

    @override
    def build_values(self) -> dict[str, Any]:
        scope = self.answering_scope
        return {
            "status": EntityShareStatus.ACCEPTED,
            "recipient_entity_type": scope.entity_type(),
            "recipient_entity_id": scope,
            "expires_at": None,
        }


@dataclass
class EntityShareRejectUpdater(_RecipientInvitationUpdater):
    """The receiving side turns down what was offered."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityShareStatus.REJECTED}


@dataclass
class EntityShareLeaveUpdater(_RecipientInvitationUpdater):
    """The receiving side gives back what it took.

    The same transition the lending side reaches by revoking, guarded on the scope that
    holds it rather than on the entity that was lent.
    """

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        def taken() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.status == EntityShareStatus.ACCEPTED

        return (
            GuardCheck(
                condition=taken,
                error=EntityShareNotFound(f"No held share {self.share_id} to give back"),
            ),
            GuardCheck(
                condition=self.addressed_to_scope(),
                error=EntityShareNotFound(
                    f"Share {self.share_id} is not held by {self.answering_scope}"
                ),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityShareStatus.REVOKED}


@dataclass
class EntityShareRevokeUpdater(GuardedDataUpdater[EntityShareRow, EntityShareData]):
    """What was lent is taken back.

    Guarded on the share still being held, so taking it back twice settles nothing
    rather than rewriting a row that was already returned. No address guard: whoever
    may reach the entity that was lent may take it back, and the permission check
    upstream is what says so.
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
    def target_id_value(self) -> EntityShareID:
        return self.share_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        def taken() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.status == EntityShareStatus.ACCEPTED

        return (
            GuardCheck(
                condition=taken,
                error=EntityShareNotFound(f"No held share {self.share_id} to take back"),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": EntityShareStatus.REVOKED}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()


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
    def target_id_value(self) -> EntityShareID:
        return self.share_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        def pending() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.status == EntityShareStatus.PENDING

        return (
            GuardCheck(
                condition=pending,
                error=EntityShareNotFound(f"No open offer {self.share_id} to cancel"),
            ),
        )

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
