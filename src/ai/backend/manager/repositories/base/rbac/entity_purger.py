"""Purger for RBAC scope-scoped entity delete operations."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Generic, Protocol, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import (
    selectinload,
)

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec as BaseBatchPurgerSpec
from ai.backend.manager.repositories.base.purger import Purger as BasePurger
from ai.backend.manager.repositories.base.purger import PurgerResult as BasePurgerResult
from ai.backend.manager.repositories.base.purger import TRow

# =============================================================================
# Protocol
# =============================================================================


class RBACEntityRowProtocol(Protocol):
    """Protocol for rows that support RBAC entity purging.

    Row classes used with RBACEntityPurger/RBACEntityBatchPurger must implement this method.
    """

    def entity_id(self) -> ObjectId:
        """Return the entity ObjectId for RBAC cleanup."""
        ...


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACEntityPurger(BasePurger[TRow]):
    """Single-row RBAC entity purger by primary key.

    Inherits row_class and pk_value from BasePurger.
    The row_class must implement RBACEntityRowProtocol (entity_id() method).
    """

    pass


@dataclass
class RBACEntityPurgerResult(BasePurgerResult[TRow]):
    """Result of executing a single-row RBAC entity purge."""

    pass


class RBACEntityBatchPurgerSpec(BaseBatchPurgerSpec[TRow]):
    """Spec for RBAC entity batch purge operations.

    Inherits build_subquery() from BaseBatchPurgerSpec.
    The selected rows must implement RBACEntityRowProtocol.
    """

    pass


@dataclass
class RBACEntityBatchPurger(Generic[TRow]):
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
    deleted_object_permission_count: int
    deleted_permission_group_count: int
    deleted_scope_association_count: int


# =============================================================================
# Query Helpers (Single Entity)
# =============================================================================


async def _get_related_roles(
    db_sess: SASession,
    object_id: ObjectId,
) -> list[RoleRow]:
    """
    Get all roles related to the given entity via object permissions.

    Eagerly loads:
    - object_permissions with their scope_associations
    - permission_groups with their permissions
    """
    role_scalars = await db_sess.scalars(
        sa.select(RoleRow)
        .join(ObjectPermissionRow, RoleRow.id == ObjectPermissionRow.role_id)
        .where(
            sa.and_(
                ObjectPermissionRow.entity_id == object_id.entity_id,
                ObjectPermissionRow.entity_type == object_id.entity_type,
            )
        )
        .options(
            selectinload(RoleRow.object_permission_rows).selectinload(
                ObjectPermissionRow.scope_association_rows
            ),
            selectinload(RoleRow.permission_group_rows).selectinload(
                PermissionGroupRow.permission_rows
            ),
        )
    )
    return list(role_scalars.unique().all())


# =============================================================================
# Query Helpers (Batch)
# =============================================================================


async def _get_related_roles_for_entities(
    db_sess: SASession,
    entity_ids: Collection[ObjectId],
) -> list[RoleRow]:
    """
    Get all roles related to multiple entities via object permissions.

    Eagerly loads:
    - object_permissions with their scope_associations
    - permission_groups with their permissions
    """
    if not entity_ids:
        return []

    conditions = [
        sa.and_(
            ObjectPermissionRow.entity_id == eid.entity_id,
            ObjectPermissionRow.entity_type == eid.entity_type,
        )
        for eid in entity_ids
    ]

    role_scalars = await db_sess.scalars(
        sa.select(RoleRow)
        .join(ObjectPermissionRow, RoleRow.id == ObjectPermissionRow.role_id)
        .where(sa.or_(*conditions))
        .options(
            selectinload(RoleRow.object_permission_rows).selectinload(
                ObjectPermissionRow.scope_association_rows
            ),
            selectinload(RoleRow.permission_group_rows).selectinload(
                PermissionGroupRow.permission_rows
            ),
        )
    )
    return list(role_scalars.unique().all())


# =============================================================================
# ID Collection Helpers (Pure Functions)
# =============================================================================


def _find_orphaned_perm_groups_in_role(
    role_row: RoleRow,
    entity_to_delete: ObjectId,
) -> list[UUID]:
    """
    Identify permission_groups to delete when an entity is removed from a role.

    A permission_group is considered orphaned and should be deleted if:
    1. It has no remaining PermissionRow entries, AND
    2. No other object_permission entity in this role belongs to the same scope.
    """
    perm_group_ids: list[UUID] = []
    if not role_row.permission_group_rows:
        return perm_group_ids

    # Collect scopes from remaining entities (via eagerly loaded scope_association_rows)
    remaining_scopes: set[ScopeId] = set()
    for object_permission_row in role_row.object_permission_rows:
        if object_permission_row.object_id() == entity_to_delete:
            continue
        for assoc in object_permission_row.scope_association_rows:
            remaining_scopes.add(assoc.parsed_scope_id())

    for perm_group_row in role_row.permission_group_rows:
        # Skip permission groups that have remaining permissions
        if perm_group_row.permission_rows:
            continue
        perm_group_scope = perm_group_row.parsed_scope_id()
        if perm_group_scope not in remaining_scopes:
            perm_group_ids.append(perm_group_row.id)
    return perm_group_ids


def _find_orphaned_perm_groups(
    role_rows: Collection[RoleRow],
    entity_to_delete: ObjectId,
) -> list[UUID]:
    """Collect orphaned permission group IDs across the given roles."""
    if not role_rows:
        return []
    permission_group_ids: list[UUID] = []
    for role_row in role_rows:
        perm_group_ids = _find_orphaned_perm_groups_in_role(role_row, entity_to_delete)
        permission_group_ids.extend(perm_group_ids)
    return permission_group_ids


def _find_object_permissions_for_entity(
    role_rows: Collection[RoleRow],
    entity_to_delete: ObjectId,
) -> list[UUID]:
    """Collect object permission IDs that reference the entity to be deleted."""
    if not role_rows:
        return []
    object_permission_ids: list[UUID] = []
    for role_row in role_rows:
        for object_permission_row in role_row.object_permission_rows:
            object_id = object_permission_row.object_id()
            if object_id == entity_to_delete:
                object_permission_ids.append(object_permission_row.id)
    return object_permission_ids


# =============================================================================
# ID Collection Helpers (Batch)
# =============================================================================


def _find_object_permissions_for_entities(
    role_rows: Collection[RoleRow],
    entities_to_delete: Collection[ObjectId],
) -> list[UUID]:
    """Collect object permission IDs that reference any of the entities to be deleted."""
    if not role_rows or not entities_to_delete:
        return []
    entity_set = set(entities_to_delete)
    object_permission_ids: list[UUID] = []
    for role_row in role_rows:
        for object_permission_row in role_row.object_permission_rows:
            if object_permission_row.object_id() in entity_set:
                object_permission_ids.append(object_permission_row.id)
    return object_permission_ids


def _find_orphaned_perm_groups_for_entities(
    role_rows: Collection[RoleRow],
    entities_to_delete: Collection[ObjectId],
) -> list[UUID]:
    """
    Identify permission_groups that will be orphaned after deleting multiple entities.

    A permission_group is considered orphaned and should be deleted if:
    1. It has no remaining PermissionRow entries, AND
    2. No other object_permission entity in this role belongs to the same scope
       (after all the entities are deleted)
    """
    if not role_rows or not entities_to_delete:
        return []

    entity_set = set(entities_to_delete)
    perm_group_ids: list[UUID] = []

    for role_row in role_rows:
        if not role_row.permission_group_rows:
            continue

        # Collect scopes from remaining entities (not in delete set)
        remaining_scopes: set[ScopeId] = set()
        for object_permission_row in role_row.object_permission_rows:
            if object_permission_row.object_id() in entity_set:
                continue
            for assoc in object_permission_row.scope_association_rows:
                remaining_scopes.add(assoc.parsed_scope_id())

        for perm_group_row in role_row.permission_group_rows:
            # Skip permission groups that have remaining permissions
            if perm_group_row.permission_rows:
                continue
            perm_group_scope = perm_group_row.parsed_scope_id()
            if perm_group_scope not in remaining_scopes:
                perm_group_ids.append(perm_group_row.id)

    return perm_group_ids


# =============================================================================
# Deletion Helpers (Single Entity)
# =============================================================================


async def _delete_object_permissions(
    db_sess: SASession,
    ids: Collection[UUID],
) -> None:
    """Delete ObjectPermissionRows by IDs."""
    if not ids:
        return
    await db_sess.execute(sa.delete(ObjectPermissionRow).where(ObjectPermissionRow.id.in_(ids)))


async def _delete_permission_groups(
    db_sess: SASession,
    ids: Collection[UUID],
) -> None:
    """Delete PermissionGroupRows by IDs."""
    if not ids:
        return
    await db_sess.execute(sa.delete(PermissionGroupRow).where(PermissionGroupRow.id.in_(ids)))


async def _delete_scope_associations(
    db_sess: SASession,
    entity_id: ObjectId,
) -> None:
    """Delete all scope associations for the given entity."""
    await db_sess.execute(
        sa.delete(AssociationScopesEntitiesRow).where(
            sa.and_(
                AssociationScopesEntitiesRow.entity_id == entity_id.entity_id,
                AssociationScopesEntitiesRow.entity_type == entity_id.entity_type,
            )
        )
    )


# =============================================================================
# Deletion Helpers (Batch) - Return counts
# =============================================================================


async def _batch_delete_object_permissions(
    db_sess: SASession,
    ids: Collection[UUID],
) -> int:
    """Delete ObjectPermissionRows by IDs. Returns count of deleted rows."""
    if not ids:
        return 0
    result = await db_sess.execute(
        sa.delete(ObjectPermissionRow).where(ObjectPermissionRow.id.in_(ids))
    )
    return cast(CursorResult, result).rowcount or 0


async def _batch_delete_permission_groups(
    db_sess: SASession,
    ids: Collection[UUID],
) -> int:
    """Delete PermissionGroupRows by IDs. Returns count of deleted rows."""
    if not ids:
        return 0
    result = await db_sess.execute(
        sa.delete(PermissionGroupRow).where(PermissionGroupRow.id.in_(ids))
    )
    return cast(CursorResult, result).rowcount or 0


async def _batch_delete_scope_associations(
    db_sess: SASession,
    entity_ids: Collection[ObjectId],
) -> int:
    """Delete scope associations for multiple entities. Returns count of deleted rows."""
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
    return cast(CursorResult, result).rowcount or 0


# =============================================================================
# Orchestration
# =============================================================================


async def _delete_rbac_for_entity(
    db_sess: SASession,
    entity_id: ObjectId,
) -> None:
    """
    Delete all RBAC entries related to an entity.

    Deletion order:
    1. ObjectPermissionRows - permissions granted on this entity
    2. PermissionGroupRows - orphaned groups with no remaining permissions/entities
    3. AssociationScopesEntitiesRows - scope-entity mappings
    """
    # Collect related data
    role_rows = await _get_related_roles(db_sess, entity_id)
    object_permission_ids = _find_object_permissions_for_entity(role_rows, entity_id)
    permission_group_ids = _find_orphaned_perm_groups(role_rows, entity_id)

    # Execute deletions
    await _delete_object_permissions(db_sess, object_permission_ids)
    await _delete_permission_groups(db_sess, permission_group_ids)
    await _delete_scope_associations(db_sess, entity_id)


async def _fetch_row_by_pk(
    db_sess: SASession,
    purger: RBACEntityPurger[TRow],
) -> TRow | None:
    """Fetch a row by primary key."""
    row_class = purger.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {table.name})",
        )

    result = await db_sess.scalars(sa.select(row_class).where(pk_columns[0] == purger.pk_value))
    return result.first()


async def _delete_row_by_pk(
    db_sess: SASession,
    purger: RBACEntityPurger[TRow],
) -> None:
    """Delete a row by primary key."""
    row_class = purger.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {table.name})",
        )

    await db_sess.execute(sa.delete(table).where(pk_columns[0] == purger.pk_value))


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_entity_purger(
    db_sess: SASession,
    purger: RBACEntityPurger[TRow],
) -> RBACEntityPurgerResult[TRow] | None:
    """
    Execute DELETE for a single scope-scoped entity by primary key, along with related RBAC entries.

    The row_class must implement RBACEntityRowProtocol (entity_id() method).

    Operations performed:
    1. Fetch row by primary key to get RBAC info
    2. Delete RBAC entries (ObjectPermissions/PermissionGroups/Associations)
    3. Delete the main object row

    Args:
        db_sess: Async SQLAlchemy session (must be writable)
        purger: Purger containing row_class and pk_value

    Returns:
        RBACEntityPurgerResult containing the deleted row, or None if no row matched
    """
    # 1. Fetch row to get RBAC info
    row = await _fetch_row_by_pk(db_sess, purger)
    if row is None:
        return None

    # 2. Extract entity_id from row (must implement RBACEntityRowProtocol)
    entity_id: ObjectId = row.entity_id()  # type: ignore[attr-defined]

    # 3. Delete RBAC entries
    await _delete_rbac_for_entity(db_sess, entity_id)

    # 4. Delete main row
    await _delete_row_by_pk(db_sess, purger)

    return RBACEntityPurgerResult(row=row)


async def execute_rbac_entity_batch_purger(
    db_sess: SASession,
    purger: RBACEntityBatchPurger[TRow],
) -> RBACEntityBatchPurgerResult:
    """
    Execute batch DELETE for scope-scoped entities with RBAC cleanup.

    The selected rows must implement RBACEntityRowProtocol (entity_id() method).

    Deletes rows in batches, cleaning up related RBAC entries for each batch:
    - ObjectPermissionRows for entity_ids
    - Orphaned PermissionGroupRows
    - AssociationScopesEntitiesRows for entity_ids

    Args:
        db_sess: Async SQLAlchemy session (must be writable)
        purger: BatchPurger containing spec and batch configuration

    Returns:
        RBACEntityBatchPurgerResult with counts of deleted rows
    """
    total_deleted = 0
    total_obj_perm = 0
    total_perm_group = 0
    total_scope_assoc = 0

    while True:
        # 1. Select batch of rows to delete
        subquery = purger.spec.build_subquery().limit(purger.batch_size)
        rows = list((await db_sess.scalars(subquery)).all())

        if not rows:
            break

        # 2. Extract entity_ids from rows (must implement RBACEntityRowProtocol)
        entity_ids: list[ObjectId] = [
            row.entity_id()  # type: ignore[attr-defined]
            for row in rows
        ]

        # 3. Clean up RBAC entries for entities
        role_rows = await _get_related_roles_for_entities(db_sess, entity_ids)

        # Find and delete object permissions
        obj_perm_ids = _find_object_permissions_for_entities(role_rows, entity_ids)
        total_obj_perm += await _batch_delete_object_permissions(db_sess, obj_perm_ids)

        # Find and delete orphaned permission groups
        perm_group_ids = _find_orphaned_perm_groups_for_entities(role_rows, entity_ids)
        total_perm_group += await _batch_delete_permission_groups(db_sess, perm_group_ids)

        # Delete scope associations
        total_scope_assoc += await _batch_delete_scope_associations(db_sess, entity_ids)

        # 4. Delete main rows
        table = cast(sa.Table, purger.spec.build_subquery().froms[0])
        pk_columns = list(table.primary_key.columns)

        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Batch purger only supports single-column primary keys (table: {table.name})",
            )

        pk_col = pk_columns[0]
        pk_values = [getattr(row, pk_col.key) for row in rows]

        result = await db_sess.execute(sa.delete(table).where(pk_col.in_(pk_values)))
        batch_deleted = cast(CursorResult, result).rowcount or 0
        total_deleted += batch_deleted

        if len(rows) < purger.batch_size:
            break

    return RBACEntityBatchPurgerResult(
        deleted_count=total_deleted,
        deleted_object_permission_count=total_obj_perm,
        deleted_permission_group_count=total_perm_group,
        deleted_scope_association_count=total_scope_assoc,
    )
