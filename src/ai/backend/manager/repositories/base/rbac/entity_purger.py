"""Purger for RBAC scope-scoped entity delete operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec, Purger, PurgerResult, TRow

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACEntity:
    """Represents an RBAC entity to be purged.

    Attributes:
        entity: ObjectId representing the entity to delete.
    """

    entity: ObjectId


# =============================================================================
# Spec Classes
# =============================================================================


class RBACEntityPurgerSpec(ABC):
    """Spec for building RBAC entity info for single-row purge.

    Implementations specify which entity to purge by providing:
    - entity(): Returns RBACEntity with the ObjectId to delete
    - scope_type(): Returns the ScopeType when this entity acts as a scope
    """

    @abstractmethod
    def entity(self) -> RBACEntity:
        """Return the RBAC entity information for deletion."""
        raise NotImplementedError

    @abstractmethod
    def scope_type(self) -> ScopeType:
        """Return the scope type when this entity acts as a scope in associations."""
        raise NotImplementedError


class RBACEntityBatchPurgerSpec(BatchPurgerSpec[TRow], ABC):
    """Spec for RBAC entity batch purge operations.

    Inherits build_subquery() from BatchPurgerSpec.
    Implementations must provide:
    - entity_type(): Returns the EntityType for constructing ObjectIds from row PKs
    - scope_type(): Returns the ScopeType when this entity acts as a scope
    """

    @abstractmethod
    def entity_type(self) -> EntityType:
        """Return the entity type for constructing ObjectIds from row primary keys."""
        raise NotImplementedError

    @abstractmethod
    def scope_type(self) -> ScopeType:
        """Return the scope type when this entity acts as a scope in associations."""
        raise NotImplementedError


# =============================================================================
# Purger Classes
# =============================================================================


@dataclass
class RBACEntityPurger(Purger[TRow]):
    """Single-row RBAC entity purger by primary key.

    Inherits row_class and pk_value from Purger.

    Attributes:
        spec: RBACEntityPurgerSpec providing entity info for RBAC cleanup.
    """

    spec: RBACEntityPurgerSpec


@dataclass
class RBACEntityPurgerResult(PurgerResult[TRow]):
    """Result of executing a single-row RBAC entity purge."""

    pass


@dataclass
class RBACEntityBatchPurger[TRow: Base]:
    """Batch purger for RBAC scope-scoped entities.

    Attributes:
        spec: RBACEntityBatchPurgerSpec implementation defining what to delete.
        batch_size: Batch size for chunked deletion (default: 1000).
    """

    spec: RBACEntityBatchPurgerSpec[TRow]
    batch_size: int = 1000


@dataclass
class RBACEntityBatchPurgerResult:
    """Result of RBAC entity batch purge operation."""

    deleted_count: int
    deleted_permission_count: int
    deleted_scope_association_count: int


# =============================================================================
# Deletion Helpers (Single Entity)
# =============================================================================


async def _delete_entity_scope_permissions(
    db_sess: SASession,
    scope_type: ScopeType,
    scope_id: str,
) -> None:
    """Delete permissions where the entity is used as scope (entity-as-scope pattern)."""
    await db_sess.execute(
        sa.delete(PermissionRow).where(
            sa.and_(
                PermissionRow.scope_type == scope_type,
                PermissionRow.scope_id == scope_id,
            )
        )
    )


async def _delete_scope_associations(
    db_sess: SASession,
    entity_id: ObjectId,
) -> None:
    """Delete all scope associations where the entity is the target."""
    await db_sess.execute(
        sa.delete(AssociationScopesEntitiesRow).where(
            sa.and_(
                AssociationScopesEntitiesRow.entity_id == entity_id.entity_id,
                AssociationScopesEntitiesRow.entity_type == entity_id.entity_type,
            )
        )
    )


async def _delete_scope_associations_as_scope(
    db_sess: SASession,
    scope_type: ScopeType,
    scope_id: str,
) -> None:
    """Delete all scope associations where the purged entity is the scope."""
    await db_sess.execute(
        sa.delete(AssociationScopesEntitiesRow).where(
            sa.and_(
                AssociationScopesEntitiesRow.scope_type == scope_type,
                AssociationScopesEntitiesRow.scope_id == scope_id,
            )
        )
    )


# =============================================================================
# Deletion Helpers (Batch) - Return counts
# =============================================================================


async def _batch_delete_entity_scope_permissions(
    db_sess: SASession,
    scope_type: ScopeType,
    entity_ids: Collection[ObjectId],
) -> int:
    """Delete permissions where the entities are used as scope. Returns count of deleted rows."""
    if not entity_ids:
        return 0

    scope_id_values = [eid.entity_id for eid in entity_ids]
    result = await db_sess.execute(
        sa.delete(PermissionRow).where(
            sa.and_(
                PermissionRow.scope_type == scope_type,
                PermissionRow.scope_id.in_(scope_id_values),
            )
        )
    )
    return cast(CursorResult[Any], result).rowcount or 0


async def _batch_delete_scope_associations(
    db_sess: SASession,
    entity_ids: Collection[ObjectId],
) -> int:
    """Delete scope associations where entities are the target. Returns count of deleted rows."""
    if not entity_ids:
        return 0

    conditions = [
        sa.and_(
            AssociationScopesEntitiesRow.entity_id == eid.entity_id,
            AssociationScopesEntitiesRow.entity_type == eid.entity_type,
        )
        for eid in entity_ids
    ]

    result = await db_sess.execute(
        sa.delete(AssociationScopesEntitiesRow).where(sa.or_(*conditions))
    )
    return cast(CursorResult[Any], result).rowcount or 0


async def _batch_delete_scope_associations_as_scope(
    db_sess: SASession,
    scope_type: ScopeType,
    entity_ids: Collection[ObjectId],
) -> int:
    """Delete scope associations where the entities are the scope. Returns count of deleted rows."""
    if not entity_ids:
        return 0

    scope_id_values = [eid.entity_id for eid in entity_ids]
    result = await db_sess.execute(
        sa.delete(AssociationScopesEntitiesRow).where(
            sa.and_(
                AssociationScopesEntitiesRow.scope_type == scope_type,
                AssociationScopesEntitiesRow.scope_id.in_(scope_id_values),
            )
        )
    )
    return cast(CursorResult[Any], result).rowcount or 0


# =============================================================================
# Batch Orchestration Data
# =============================================================================


@dataclass
class _RBACEntityBatchCleanupCounts:
    """Internal result for batch RBAC cleanup counts."""

    permission_count: int
    scope_association_count: int


# =============================================================================
# Orchestration
# =============================================================================


async def _delete_rbac_for_entity(
    db_sess: SASession,
    entity_id: ObjectId,
    scope_type: ScopeType,
) -> None:
    """
    Delete all RBAC entries related to an entity.

    Deletion order:
    1. PermissionRows - permissions where this entity is the scope
    2. AssociationScopesEntitiesRows - scope-entity mappings (entity as target)
    3. AssociationScopesEntitiesRows - scope-entity mappings (entity as scope)
    """
    # 1. Delete permissions where entity is the scope
    await _delete_entity_scope_permissions(db_sess, scope_type, entity_id.entity_id)

    # 2. Delete scope associations where entity is the target
    await _delete_scope_associations(db_sess, entity_id)

    # 3. Delete scope associations where entity is the scope (bidirectional)
    await _delete_scope_associations_as_scope(db_sess, scope_type, entity_id.entity_id)


async def _batch_delete_rbac_for_entities(
    db_sess: SASession,
    entity_ids: Collection[ObjectId],
    scope_type: ScopeType,
) -> _RBACEntityBatchCleanupCounts:
    """Delete all RBAC entries for multiple entities.

    Mirrors _delete_rbac_for_entity() but for batch operations with counts.

    Deletion order:
    1. PermissionRows - permissions where these entities are the scope
    2. AssociationScopesEntitiesRows - scope-entity mappings (entities as target)
    3. AssociationScopesEntitiesRows - scope-entity mappings (entities as scope)
    """
    # 1. Delete permissions where entities are the scope
    perm_count = await _batch_delete_entity_scope_permissions(db_sess, scope_type, entity_ids)

    # 2. Delete scope associations where entities are the target
    scope_assoc_count = await _batch_delete_scope_associations(db_sess, entity_ids)

    # 3. Delete scope associations where entities are the scope (bidirectional)
    scope_assoc_as_scope_count = await _batch_delete_scope_associations_as_scope(
        db_sess, scope_type, entity_ids
    )

    return _RBACEntityBatchCleanupCounts(
        permission_count=perm_count,
        scope_association_count=scope_assoc_count + scope_assoc_as_scope_count,
    )


async def _delete_row_by_pk_returning(
    db_sess: SASession,
    purger: RBACEntityPurger[TRow],
) -> TRow | None:
    """Delete a row by primary key and return the deleted row data."""
    row_class = purger.row_class
    table = row_class.__table__
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {table.name})",
        )

    stmt = sa.delete(table).where(pk_columns[0] == purger.pk_value).returning(*table.columns)
    result = await db_sess.execute(stmt)
    row_data = result.fetchone()

    if row_data is None:
        return None

    return cast(TRow, row_class(**dict(row_data._mapping)))


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_entity_purger(
    db_sess: SASession,
    purger: RBACEntityPurger[TRow],
) -> RBACEntityPurgerResult[TRow] | None:
    """
    Execute DELETE for a single scope-scoped entity by primary key, along with related RBAC entries.

    Operations performed:
    1. Get entity info from spec
    2. Delete RBAC entries (Permissions/Associations in both directions)
    3. Delete the main object row with RETURNING

    Args:
        db_sess: Async SQLAlchemy session (must be writable)
        purger: Purger containing row_class, pk_value, and spec

    Returns:
        RBACEntityPurgerResult containing the deleted row, or None if no row matched
    """
    # 1. Get entity info from spec
    entity_id = purger.spec.entity().entity
    scope_type = purger.spec.scope_type()

    # 2. Delete RBAC entries
    await _delete_rbac_for_entity(db_sess, entity_id, scope_type)

    # 3. Delete main row with RETURNING
    row = await _delete_row_by_pk_returning(db_sess, purger)
    if row is None:
        return None

    return RBACEntityPurgerResult(row=row)


async def execute_rbac_entity_batch_purger(
    db_sess: SASession,
    purger: RBACEntityBatchPurger[TRow],
) -> RBACEntityBatchPurgerResult:
    """
    Execute batch DELETE for scope-scoped entities with RBAC cleanup.

    Deletes rows in batches, cleaning up related RBAC entries for each batch:
    - PermissionRows where entities are the scope
    - AssociationScopesEntitiesRows in both directions (entity as target and as scope)

    Args:
        db_sess: Async SQLAlchemy session (must be writable)
        purger: BatchPurger containing spec and batch configuration

    Returns:
        RBACEntityBatchPurgerResult with counts of deleted rows
    """
    total_deleted = 0
    total_perm = 0
    total_scope_assoc = 0

    # Get table and PK info from subquery
    base_subquery = purger.spec.build_subquery()
    table = cast(sa.Table, base_subquery.froms[0])
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Batch purger only supports single-column primary keys (table: {table.name})",
        )

    pk_col = pk_columns[0]
    entity_type = purger.spec.entity_type()
    scope_type = purger.spec.scope_type()

    while True:
        # 1. DELETE with RETURNING - get PKs and delete in one query
        sub = purger.spec.build_subquery().subquery()
        pk_subquery = sa.select(sub.c[pk_col.key]).limit(purger.batch_size)

        stmt = sa.delete(table).where(pk_col.in_(pk_subquery)).returning(pk_col)
        result = await db_sess.execute(stmt)
        deleted_pks = result.fetchall()

        if not deleted_pks:
            break

        pk_values = [row[0] for row in deleted_pks]
        batch_deleted = len(pk_values)
        total_deleted += batch_deleted

        # 2. Construct entity_ids from deleted PKs
        entity_ids: list[ObjectId] = [
            ObjectId(entity_type=entity_type, entity_id=str(pk)) for pk in pk_values
        ]

        # 3. Clean up RBAC entries (after main row deletion - no FK constraint)
        cleanup = await _batch_delete_rbac_for_entities(db_sess, entity_ids, scope_type)
        total_perm += cleanup.permission_count
        total_scope_assoc += cleanup.scope_association_count

        if batch_deleted < purger.batch_size:
            break

    return RBACEntityBatchPurgerResult(
        deleted_count=total_deleted,
        deleted_permission_count=total_perm,
        deleted_scope_association_count=total_scope_assoc,
    )
