"""Syncer for RBAC scope-entity associations.

Declares "Entity X should belong to Scope Y" and handles all cases
internally — create, rebind (scope migration), or no-op — eliminating
branching logic at the call site.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)


class SyncAction(enum.Enum):
    """Outcome of a scope-sync operation."""

    CREATED = "created"
    REBOUND = "rebound"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class RBACEntityScopeSyncer:
    """Declarative scope syncer for a single entity.

    Attributes:
        entity_ref: RBAC element reference for the entity (element_type + element_id).
        desired_scope_ref: The scope that the entity should belong to.
        relation_type: Edge type for the association. Defaults to AUTO.
    """

    entity_ref: RBACElementRef
    desired_scope_ref: RBACElementRef
    relation_type: RelationType = RelationType.AUTO


@dataclass(frozen=True)
class RBACEntityScopeSyncerResult:
    """Result of executing a scope-sync operation.

    Attributes:
        action: What happened — CREATED, REBOUND, or UNCHANGED.
        association_row: The current association row (None only if UNCHANGED).
        unbound_rows: Stale association rows that were removed (empty unless REBOUND).
    """

    action: SyncAction
    association_row: AssociationScopesEntitiesRow | None
    unbound_rows: list[AssociationScopesEntitiesRow] = field(default_factory=list)


async def execute_rbac_entity_scope_syncer(
    db_sess: SASession,
    syncer: RBACEntityScopeSyncer,
) -> RBACEntityScopeSyncerResult:
    """Ensure entity belongs to exactly the desired scope.

    Two-query, idempotent algorithm:
    1. DELETE stale associations for (entity_type, entity_id, scope_type)
       where scope_id != desired, RETURNING removed rows.
    2. INSERT desired association ON CONFLICT DO NOTHING, RETURNING the row
       if newly inserted.
    3. Determine action:
       - INSERT returned row + DELETE had rows → REBOUND
       - INSERT returned row only → CREATED
       - INSERT returned nothing → UNCHANGED

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        syncer: Syncer instance declaring the desired state.

    Returns:
        RBACEntityScopeSyncerResult describing the outcome.
    """
    entity_type = syncer.entity_ref.element_type.to_entity_type()
    entity_id = syncer.entity_ref.element_id
    scope_type = syncer.desired_scope_ref.element_type.to_scope_type()
    desired_scope_id = syncer.desired_scope_ref.element_id

    # 1. Remove stale associations
    delete_stmt = (
        sa.delete(AssociationScopesEntitiesRow)
        .where(
            AssociationScopesEntitiesRow.entity_type == entity_type,
            AssociationScopesEntitiesRow.entity_id == entity_id,
            AssociationScopesEntitiesRow.scope_type == scope_type,
            AssociationScopesEntitiesRow.scope_id != desired_scope_id,
        )
        .returning(AssociationScopesEntitiesRow)
    )
    unbound_rows = list((await db_sess.scalars(delete_stmt)).all())

    # 2. Insert desired association idempotently
    insert_stmt = (
        pg_insert(AssociationScopesEntitiesRow)
        .values(
            scope_type=scope_type,
            scope_id=desired_scope_id,
            entity_type=entity_type,
            entity_id=entity_id,
            relation_type=syncer.relation_type,
        )
        .on_conflict_do_nothing(constraint="uq_scope_id_entity_id")
        .returning(AssociationScopesEntitiesRow)
    )
    inserted_row = (await db_sess.scalars(insert_stmt)).first()

    # 3. Determine action
    if inserted_row is not None and unbound_rows:
        action = SyncAction.REBOUND
    elif inserted_row is not None:
        action = SyncAction.CREATED
    else:
        action = SyncAction.UNCHANGED

    return RBACEntityScopeSyncerResult(
        action=action,
        association_row=inserted_row,
        unbound_rows=unbound_rows,
    )
