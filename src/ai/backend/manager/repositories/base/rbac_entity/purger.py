from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import (
    selectinload,
)

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.purger import Purger as BasePurger
from ai.backend.manager.repositories.base.purger import PurgerResult as BasePurgerResult
from ai.backend.manager.repositories.base.purger import TRow


@dataclass
class Purger(BasePurger[TRow]):
    """Single-row delete by primary key.

    Attributes:
        entity_id: ObjectId identifying the target entity.
        field_id: Optional ObjectId identifying the target field (for field-scoped entities).
    """

    entity_id: ObjectId
    field_id: ObjectId | None


@dataclass
class PurgerResult(BasePurgerResult[TRow]):
    pass


async def _get_related_roles(
    db_sess: SASession,
    object_id: ObjectId,
) -> list[RoleRow]:
    """
    Get all roles related to the given entity as object permissions.
    Loads object_permissions with their scope_associations, and permission_groups with permissions.
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


def _perm_group_ids_to_delete_in_role(
    role_row: RoleRow,
    entity_to_delete: ObjectId,
) -> list[UUID]:
    """
    Identify permission_groups to delete when an entity is removed from a role.

    A permission_group is deleted if:
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


def _perm_group_ids_to_delete(
    role_rows: Collection[RoleRow],
    entity_to_delete: ObjectId,
) -> list[UUID]:
    if not role_rows:
        return []
    permission_group_ids: list[UUID] = []
    for role_row in role_rows:
        perm_group_ids = _perm_group_ids_to_delete_in_role(role_row, entity_to_delete)
        permission_group_ids.extend(perm_group_ids)
    return permission_group_ids


def _object_permission_ids_to_delete(
    role_rows: Collection[RoleRow],
    entity_to_delete: ObjectId,
) -> list[UUID]:
    if not role_rows:
        return []
    object_permission_ids: list[UUID] = []
    for role_row in role_rows:
        for object_permission_row in role_row.object_permission_rows:
            object_id = object_permission_row.object_id()
            if object_id == entity_to_delete:
                object_permission_ids.append(object_permission_row.id)
    return object_permission_ids


async def _delete_main_object_row(
    db_sess: SASession,
    purger: Purger[TRow],
) -> TRow | None:
    row_class = purger.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
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

    deleted_row: TRow = row_class(**dict(row_data._mapping))
    return deleted_row


async def _delete_related_rows(
    db_sess: SASession,
    purger: Purger[TRow],
) -> None:
    entity_id = purger.entity_id
    field_id = purger.field_id
    if field_id is not None:
        await _delete_rbac_field(db_sess, field_id)
    else:
        await _delete_rbac_entity(db_sess, entity_id)


async def _delete_rbac_entity(
    db_sess: SASession,
    entity_id: ObjectId,
) -> None:
    # Get all roles with object_permissions and their scope_associations eagerly loaded
    role_rows = await _get_related_roles(db_sess, entity_id)
    object_permission_ids = _object_permission_ids_to_delete(role_rows, entity_id)
    permission_group_ids = _perm_group_ids_to_delete(role_rows, entity_id)

    # Execute deletions
    if object_permission_ids:
        await db_sess.execute(
            sa.delete(ObjectPermissionRow).where(ObjectPermissionRow.id.in_(object_permission_ids))  # type: ignore[attr-defined]
        )
    if permission_group_ids:
        await db_sess.execute(
            sa.delete(PermissionGroupRow).where(PermissionGroupRow.id.in_(permission_group_ids))  # type: ignore[attr-defined]
        )
    # Delete scope associations for the deleted entity
    await db_sess.execute(
        sa.delete(AssociationScopesEntitiesRow).where(
            sa.and_(
                AssociationScopesEntitiesRow.entity_id == entity_id.entity_id,
                AssociationScopesEntitiesRow.entity_type == entity_id.entity_type,
            )
        )
    )


async def _delete_rbac_field(
    db_sess: SASession,
    field_id: ObjectId,
) -> None:
    await db_sess.execute(
        sa.delete(EntityFieldRow).where(
            sa.and_(
                EntityFieldRow.field_id == field_id.entity_id,
                EntityFieldRow.field_type == field_id.entity_type,
            )
        )
    )


async def execute_purger(
    db_sess: SASession,
    purger: Purger[TRow],
) -> PurgerResult[TRow] | None:
    """
    Execute DELETE for a single row by primary key, along with related RBAC entries.
    - Delete the main object row.
    - Delete associated EntityFieldRow if field-scoped.
    - Delete related ObjectPermissionRow and AssociationScopesEntitiesRow.
    - Delete PermissionGroupRow if:
        - It has no remaining PermissionRow entries.
        - And the deleted object was the only one scoped to that permission group.

    Args:
        db_sess: Async SQLAlchemy session (must be writable)
        purger: Purger containing row_class and pk_value

    Returns:
        PurgerResult containing the deleted row, or None if no row matched
    """

    await _delete_related_rows(db_sess, purger)
    deleted_row = await _delete_main_object_row(db_sess, purger)
    if deleted_row is None:
        return None
    return PurgerResult(row=deleted_row)
