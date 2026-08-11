"""Membership queries over the virtual-scope chain.

The virtual-scope chain (``entity_memberships`` joined to ``virtual_scopes``) is the
read model for user-scope membership. ``association_scopes_entities`` remains as the
legacy dual-written association and must not be used for new membership reads.
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import ScopeType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow

__all__ = (
    "user_scope_membership_exists",
    "user_scope_membership_query",
)

type _UuidExpr = uuid.UUID | sa.ColumnElement[uuid.UUID] | InstrumentedAttribute[uuid.UUID]


def user_scope_membership_query(scope_type: ScopeType) -> sa.Select[tuple[EntityID, ScopeID]]:
    """(``user_id``, ``scope_id``) pairs of the users enrolled in scopes of
    ``scope_type``. Callers narrow by either column, or ``.subquery()`` it to join
    against user/scope tables — both columns are UUIDs, so no string casts are
    needed."""
    return (
        sa.select(
            EntityMembershipRow.entity_id.label("user_id"),
            VirtualScopeRow.scope_id.label("scope_id"),
        )
        .select_from(EntityMembershipRow)
        .join(VirtualScopeRow, EntityMembershipRow.virtual_scope_id == VirtualScopeRow.id)
        .where(
            VirtualScopeRow.scope_type == scope_type,
            EntityMembershipRow.entity_type == USER_ENTITY_TYPE,
        )
    )


def user_scope_membership_exists(
    scope_type: ScopeType,
    scope_id: _UuidExpr,
    user_id: _UuidExpr,
) -> sa.ColumnElement[bool]:
    """EXISTS predicate: the user is enrolled in the scope's virtual scope.

    ``scope_id`` / ``user_id`` accept literal UUIDs or column expressions, so the
    predicate works both as a direct filter and as a correlated condition inside a
    larger query.
    """
    return sa.exists(
        sa.select(sa.literal(1))
        .select_from(EntityMembershipRow)
        .join(VirtualScopeRow, EntityMembershipRow.virtual_scope_id == VirtualScopeRow.id)
        .where(
            VirtualScopeRow.scope_type == scope_type,
            VirtualScopeRow.scope_id == scope_id,
            EntityMembershipRow.entity_type == USER_ENTITY_TYPE,
            EntityMembershipRow.entity_id == user_id,
        )
    )
