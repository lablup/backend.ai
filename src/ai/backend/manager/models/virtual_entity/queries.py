"""Membership queries over the virtual-entity chain.

The chain has two edges. ``entity_memberships`` says which virtual entity holds a
member; ``scope_bindings`` says which scopes govern a virtual entity. A permission
check walks both, and so does anything asking what a scope reaches.
"""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute, aliased

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
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
    """EXISTS predicate: the scope reaches the named member.

    The same span a permission check walks -- the member is held by a virtual entity,
    and that virtual entity is governed by the scope. A scope holding the member
    itself answers through the self-govern edge every node carries, so the direct
    case needs no separate term.

    A cap bounds what the scope may do with the member, not whether it reaches it, so
    an own edge and a share both answer here.

    Either id accepts a literal UUID or a column expression, so the predicate works
    both as a direct filter and as a correlated condition inside a larger query.
    """
    member = aliased(VirtualEntityRow, name="member_virtual_entity")
    governor = aliased(VirtualEntityRow, name="governor_virtual_entity")
    return sa.exists(
        sa.select(sa.literal(1))
        .select_from(EntityMembershipRow)
        .join(member, EntityMembershipRow.member_entity_id == member.id)
        .join(
            ScopeBindingRow,
            ScopeBindingRow.virtual_entity_id == EntityMembershipRow.virtual_entity_id,
        )
        .join(governor, ScopeBindingRow.scope_entity_id == governor.id)
        .where(
            governor.entity_type == scope_type,
            governor.entity_id == scope_id,
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
