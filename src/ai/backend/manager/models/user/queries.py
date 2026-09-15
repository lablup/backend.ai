"""What naming a user as a scope reaches."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.virtual_entity.queries import UuidExpr, scope_membership_exists

__all__ = ("user_scope_reaches",)


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
    personal_project = (
        sa.select(ProjectRow.id)
        .where(
            ProjectRow.creator_id == user_id,
            ProjectRow.type == ProjectType.PERSONAL,
        )
        .scalar_subquery()
    )
    return sa.or_(
        scope_membership_exists(UserEntityType(), user_id, member_type, member_id),
        scope_membership_exists(ProjectEntityType(), personal_project, member_type, member_id),
    )
