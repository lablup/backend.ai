"""Query conditions for entity invitation rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.entity_invitation.types import EntityInvitationStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow

__all__ = ("EntityInvitationConditions",)


class EntityInvitationConditions:
    @staticmethod
    def by_ids(ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.id.in_(ids)

        return inner

    @staticmethod
    def by_status(status: EntityInvitationStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.status == status

        return inner

    @staticmethod
    def by_status_in(statuses: Collection[EntityInvitationStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_invitee_email(email: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.invitee_email == email

        return inner

    @staticmethod
    def by_target(target: EntityIdentifier) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                EntityInvitationRow.target_entity_type == target.entity_type(),
                EntityInvitationRow.target_entity_id == target,
            )

        return inner

    @staticmethod
    def by_target_entity_type(entity_type: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.target_entity_type == entity_type

        return inner
