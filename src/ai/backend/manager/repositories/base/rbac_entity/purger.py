from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import (
    contains_eager,
    selectinload,
    with_loader_criteria,
)

from ai.backend.manager.data.permission.id import (
    ObjectId,
    ScopeId,
)
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
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


async def _get_association_rows(
    db_sess: SASession,
    object_id: ObjectId,
) -> list[AssociationScopesEntitiesRow]:
    assoc_scalars = await db_sess.scalars(
        sa.select(AssociationScopesEntitiesRow).where(
            sa.and_(
                AssociationScopesEntitiesRow.entity_id == object_id.entity_id,
                AssociationScopesEntitiesRow.entity_type == object_id.entity_type,
            )
        )
    )
    return assoc_scalars.all()


async def _get_related_roles(
    db_sess: SASession,
    object_id: ObjectId,
    scopes: list[ScopeId],
) -> list[RoleRow]:
    """
    Get all roles related to the given entity as object permissions
    And load their permission groups scoped:
    - That have no remaining permissions.
    - And are scoped to the given scopes.
    """
    perm_group_scope_conditions = [
        (
            PermissionGroupRow.scope_id == scope.scope_id
            and PermissionGroupRow.scope_type == scope.scope_type
        )
        for scope in scopes
    ]
    role_scalars = await db_sess.scalars(
        sa.select(RoleRow)
        .select_from(
            sa.join(RoleRow, ObjectPermissionRow, RoleRow.id == ObjectPermissionRow.role_id)
        )
        .where(
            sa.and_(
                ObjectPermissionRow.entity_id == object_id.entity_id,
                ObjectPermissionRow.entity_type == object_id.entity_type,
            )
        )
        .options(
            contains_eager(RoleRow.object_permission_rows),
            selectinload(RoleRow.permission_group_rows),
            with_loader_criteria(
                PermissionGroupRow,
                sa.and_(
                    sa.not_(
                        sa.exists(
                            sa.select(PermissionRow.id).where(
                                PermissionRow.permission_group_id == PermissionGroupRow.id
                            )
                        )
                    ),
                    sa.or_(*perm_group_scope_conditions),
                ),
            ),
        )
    )
    return role_scalars.all()


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
    scopes: list[ScopeId] = []
    object_permission_ids: list[UUID] = []
    permission_group_ids: list[UUID] = []
    association_ids: list[UUID] = []

    assoc_rows = await _get_association_rows(db_sess, entity_id)
    for assoc_row in assoc_rows:
        association_ids.append(assoc_row.id)
        scopes.append(assoc_row.parsed_scope_id())

    # Check all roles associated with the entity as object permission
    role_rows = await _get_related_roles(db_sess, entity_id, scopes)
    for role_row in role_rows:
        for obj_perm_row in role_row.object_permission_rows:
            object_permission_ids.append(obj_perm_row.id)
        for perm_group_row in role_row.permission_group_rows:
            permission_group_ids.append(perm_group_row.id)

    await db_sess.execute(
        sa.delete(ObjectPermissionRow).where(ObjectPermissionRow.id.in_(object_permission_ids))  # type: ignore[attr-defined]
    )
    await db_sess.execute(
        sa.delete(PermissionGroupRow).where(PermissionGroupRow.id.in_(permission_group_ids))  # type: ignore[attr-defined]
    )
    await db_sess.execute(
        sa.delete(AssociationScopesEntitiesRow).where(
            AssociationScopesEntitiesRow.id.in_(association_ids)  # type: ignore[attr-defined]
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
