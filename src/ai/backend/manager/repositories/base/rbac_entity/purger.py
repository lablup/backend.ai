from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar
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
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow

TRow = TypeVar("TRow", bound=Base)


@dataclass
class Purger(Generic[TRow]):
    """Single-row delete by primary key.

    Attributes:
        row_class: ORM class for table access and PK detection.
        pk_value: Primary key value to identify the target row.
    """

    row_class: type[TRow]
    pk_value: UUID | str | int
    entity_id: ObjectId


@dataclass
class PurgerResult(Generic[TRow]):
    """Result of executing a single-row delete operation."""

    row: TRow


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
                    PermissionGroupRow.scope_id.in_([scope.scope_id for scope in scopes]),  # type: ignore[attr-defined]
                    PermissionGroupRow.scope_type.in_([scope.scope_type for scope in scopes]),  # type: ignore[attr-defined]
                ),
            ),
        )
    )
    return role_scalars.all()


async def _purge_related_rows(
    db_sess: SASession,
    object_permission_ids: Iterable[UUID],
    permission_group_ids: Iterable[UUID],
    association_ids: Iterable[UUID],
) -> None:
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


async def execute_purger(
    db_sess: SASession,
    purger: Purger[TRow],
) -> PurgerResult[TRow] | None:
    row_class = purger.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {table.name})",
        )

    scopes: list[ScopeId] = []
    object_id = purger.entity_id
    object_permission_ids: list[UUID] = []
    permission_group_ids: list[UUID] = []
    association_ids: list[UUID] = []

    assoc_rows = await _get_association_rows(db_sess, object_id)
    for assoc_row in assoc_rows:
        association_ids.append(assoc_row.id)
        scopes.append(assoc_row.parsed_scope_id())

    # Check all roles associated with the entity as object permission
    role_rows = await _get_related_roles(db_sess, object_id, scopes)
    for role_row in role_rows:
        for obj_perm_row in role_row.object_permission_rows:
            object_permission_ids.append(obj_perm_row.id)
        for perm_group_row in role_row.permission_group_rows:
            permission_group_ids.append(perm_group_row.id)
    await _purge_related_rows(
        db_sess,
        object_permission_ids,
        permission_group_ids,
        association_ids,
    )
    stmt = sa.delete(table).where(pk_columns[0] == purger.pk_value).returning(*table.columns)

    result = await db_sess.execute(stmt)
    row_data = result.fetchone()

    if row_data is None:
        return None

    deleted_row: TRow = row_class(**dict(row_data._mapping))
    return PurgerResult(row=deleted_row)
