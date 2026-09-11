"""Membership queries over the virtual-entity chain.

The virtual-entity chain (``entity_memberships`` joined to ``virtual_entities`` at both
ends) is the read model for user-scope membership.
"""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute, aliased

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

__all__ = (
    "scope_membership_exists",
    "user_scope_membership_exists",
    "user_scope_membership_query",
)


# The column element is parameterized loosely: an id newtype makes
# `ColumnElement[DomainID]`, which is not a `ColumnElement[UUID]` under invariance,
# and every such newtype is a UUID at the database.
type _UuidExpr = uuid.UUID | sa.ColumnElement[Any] | InstrumentedAttribute[Any]


def user_scope_membership_query(
    scope_type: EntityType, user_id: _UuidExpr | None = None
) -> sa.Select[tuple[uuid.UUID, uuid.UUID]]:
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
            member.entity_type == UserEntityType(),
        )
    )
    if user_id is not None:
        query = query.where(member.entity_id == user_id)
    return query


def scope_membership_exists(
    scope_type: EntityType,
    scope_id: _UuidExpr,
    member_type: EntityType,
    member_id: _UuidExpr,
) -> sa.ColumnElement[bool]:
    """EXISTS predicate: the scope's virtual entity holds the named member.

    A cap bounds what the scope may do with the member, not whether the scope holds
    it, so an own edge and a share both answer here.

    Either id accepts a literal UUID or a column expression, so the predicate works
    both as a direct filter and as a correlated condition inside a larger query.
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
            member.entity_type == member_type,
            member.entity_id == member_id,
        )
    )


def user_scope_membership_exists(
    scope_type: EntityType,
    scope_id: _UuidExpr,
    user_id: _UuidExpr,
) -> sa.ColumnElement[bool]:
    """EXISTS predicate: the user is enrolled in the scope's virtual entity."""
    return scope_membership_exists(scope_type, scope_id, UserEntityType(), user_id)
