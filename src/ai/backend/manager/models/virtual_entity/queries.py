"""Membership queries over the virtual-entity chain.

The virtual-entity chain (``entity_memberships`` joined to ``virtual_entities`` at both
ends) is the read model for user-scope membership. ``association_scopes_entities``
remains as the legacy dual-written association and must not be used for new membership
reads.
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute, aliased

from ai.backend.common.data.entity.types import EntityID, ScopeID, ScopeType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

__all__ = (
    "user_scope_membership_exists",
    "user_scope_membership_query",
)

type _UuidExpr = uuid.UUID | sa.ColumnElement[uuid.UUID] | InstrumentedAttribute[uuid.UUID]


def user_scope_membership_query(
    scope_type: ScopeType, user_id: _UuidExpr | None = None
) -> sa.Select[tuple[EntityID, ScopeID]]:
    """(``user_id``, ``scope_id``) pairs of the users enrolled in scopes of
    ``scope_type``, narrowed to one user when ``user_id`` is given. The scope side is
    ``VirtualEntityRow``, so callers may filter on its columns; both selected columns
    are UUIDs, so no string casts are needed."""
    member = aliased(VirtualEntityRow, name="member_virtual_entity")
    query = (
        sa.select(
            member.entity_id.label("user_id"),
            VirtualEntityRow.entity_id.label("scope_id"),
        )
        .select_from(EntityMembershipRow)
        .join(VirtualEntityRow, EntityMembershipRow.virtual_entity_id == VirtualEntityRow.id)
        .join(member, EntityMembershipRow.member_entity_id == member.id)
        .where(
            VirtualEntityRow.entity_type == scope_type,
            member.entity_type == USER_ENTITY_TYPE,
        )
    )
    if user_id is not None:
        query = query.where(member.entity_id == user_id)
    return query


def user_scope_membership_exists(
    scope_type: ScopeType,
    scope_id: _UuidExpr,
    user_id: _UuidExpr,
) -> sa.ColumnElement[bool]:
    """EXISTS predicate: the user is enrolled in the scope's virtual entity.

    ``scope_id`` / ``user_id`` accept literal UUIDs or column expressions, so the
    predicate works both as a direct filter and as a correlated condition inside a
    larger query.
    """
    member = aliased(VirtualEntityRow, name="member_virtual_entity")
    return sa.exists(
        sa.select(sa.literal(1))
        .select_from(EntityMembershipRow)
        .join(VirtualEntityRow, EntityMembershipRow.virtual_entity_id == VirtualEntityRow.id)
        .join(member, EntityMembershipRow.member_entity_id == member.id)
        .where(
            VirtualEntityRow.entity_type == scope_type,
            VirtualEntityRow.entity_id == scope_id,
            member.entity_type == USER_ENTITY_TYPE,
            member.entity_id == user_id,
        )
    )
