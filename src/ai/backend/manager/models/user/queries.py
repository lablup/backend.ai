"""What naming a user as a scope reaches."""

from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.virtual_entity.queries import (
    UuidExpr,
    scope_membership_exists,
    scope_share_exists,
    user_scope_membership_query,
)
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

__all__ = (
    "joined_project_ids_query",
    "user_scope_reaches",
    "user_scope_shares",
)


def joined_project_ids_query(user_id: UserID) -> sa.Select[tuple[uuid.UUID]]:
    """The projects the user is on the roster of, personal ones left out."""
    roster = (
        user_scope_membership_query(ProjectEntityType(), user_id)
        .where(
            VirtualEntityRow.entity_id.not_in(
                sa.select(ProjectRow.id).where(ProjectRow.type == ProjectType.PERSONAL)
            )
        )
        .subquery()
    )
    return sa.select(roster.c.scope_id)


def user_scope_reaches(
    user_id: UserID,
    member_type: EntityType,
    member_id: UuidExpr,
) -> sa.ColumnElement[bool]:
    """EXISTS predicate: naming this user as a scope reaches the member.

    A personal project is the user under another name (BEP-1077), and what they hold
    is created in it rather than in them. Naming the user therefore has to stand for
    the project too, so that a caller never has to name both.
    """
    return sa.or_(
        scope_membership_exists(UserEntityType(), user_id, member_type, member_id),
        scope_membership_exists(
            ProjectEntityType(), _personal_project_id(user_id), member_type, member_id
        ),
    )


def user_scope_shares(
    user_id: UserID,
    member_type: EntityType,
    member_id: UuidExpr,
) -> sa.ColumnElement[bool]:
    """EXISTS predicate: the member was shared to this user or their personal project."""
    return sa.or_(
        scope_share_exists(UserEntityType(), user_id, member_type, member_id),
        scope_share_exists(
            ProjectEntityType(), _personal_project_id(user_id), member_type, member_id
        ),
    )


def _personal_project_id(user_id: UserID) -> sa.ScalarSelect[ProjectID]:
    return (
        sa.select(ProjectRow.id)
        .where(
            ProjectRow.creator_id == user_id,
            ProjectRow.type == ProjectType.PERSONAL,
        )
        .scalar_subquery()
    )
