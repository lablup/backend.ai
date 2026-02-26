"""Upserter for RBAC scope-scoped entity upsert (INSERT ON CONFLICT UPDATE) operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TypeVar

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.upserter import (
    Upserter,
    UpserterResult,
    execute_upserter,
)

TRow = TypeVar("TRow", bound=Base)


@dataclass
class RBACEntityUpserter[TRow: Base]:
    """Upserter for a single entity with conditional scope associations for RBAC.

    Wraps a base ``Upserter`` and creates RBAC scope-entity associations
    only when the row is newly inserted (not updated), as determined by
    the base upserter's ``was_inserted`` flag.

    Attributes:
        upserter: Base Upserter instance to delegate the upsert to.
        element_type: The RBAC element type for this entity.
        scope_ref: Primary scope reference (scope_type + scope_id) for this entity.
        additional_scope_refs: Additional scope references for multi-scope entities.
        relation_type: The relation type for the scope-entity association. Defaults to AUTO.
        index_elements: Column names to use for conflict detection. Defaults to ["id"].
    """

    upserter: Upserter[TRow]
    element_type: RBACElementType
    scope_ref: RBACElementRef
    additional_scope_refs: Sequence[RBACElementRef] = field(default_factory=list)
    relation_type: RelationType = RelationType.AUTO
    index_elements: list[str] = field(default_factory=lambda: ["id"])


@dataclass
class RBACEntityUpserterResult[TRow: Base]:
    """Result of executing a single entity upsert."""

    row: TRow
    was_inserted: bool


async def execute_rbac_entity_upserter[TRow: Base](
    db_sess: SASession,
    rbac_upserter: RBACEntityUpserter[TRow],
) -> RBACEntityUpserterResult[TRow]:
    """Execute INSERT ON CONFLICT UPDATE with conditional RBAC association creation.

    Delegates the upsert to ``execute_upserter``, then conditionally creates
    scope-entity associations if the row was newly inserted.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        rbac_upserter: RBAC upserter wrapping a base Upserter.

    Returns:
        RBACEntityUpserterResult containing the upserted row and whether it was inserted.
    """
    result: UpserterResult[TRow] = await execute_upserter(
        db_sess,
        rbac_upserter.upserter,
        index_elements=rbac_upserter.index_elements,
    )

    if result.was_inserted:
        row_class = rbac_upserter.upserter.spec.row_class
        mapper = sa.inspect(row_class)
        pk_columns = mapper.primary_key
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Entity upserter only supports single-column primary keys"
                f" (table: {mapper.local_table.name})",
            )

        pk_attr = pk_columns[0].key
        pk_value = getattr(result.row, pk_attr)
        entity_type = rbac_upserter.element_type.to_entity_type()
        all_scope_refs = [rbac_upserter.scope_ref, *rbac_upserter.additional_scope_refs]
        for scope_ref in all_scope_refs:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=scope_ref.element_type.to_scope_type(),
                    scope_id=scope_ref.element_id,
                    entity_type=entity_type,
                    entity_id=str(pk_value),
                    relation_type=rbac_upserter.relation_type,
                ),
            )

    return RBACEntityUpserterResult(row=result.row, was_inserted=result.was_inserted)
