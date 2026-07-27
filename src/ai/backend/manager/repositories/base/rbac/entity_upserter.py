"""Upserter for RBAC scope-scoped entity INSERT ON CONFLICT UPDATE operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, TypeVar

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.repository import (
    UnsupportedCompositePrimaryKeyError,
    UpsertEmptyResultError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.integrity import (
    match_integrity_error,
    parse_integrity_error,
)
from ai.backend.manager.repositories.base.rbac.utils import bulk_insert_on_conflict_do_nothing
from ai.backend.manager.repositories.base.upserter import UpserterSpec

TRow = TypeVar("TRow", bound=Base)


@dataclass
class RBACEntityUpserter[TRow: Base]:
    """Upserter for a single entity (INSERT ON CONFLICT UPDATE) with its scope associations.

    The scoped counterpart of :class:`RBACEntityCreator`: on insert it binds the new row to
    its scope(s) exactly like a create; on conflict it updates the row in place, leaving the
    already-present binding untouched. A ``scope_ref`` of ``None`` marks a GLOBAL entity that
    binds to no scope, making this a plain upsert.

    Attributes:
        spec: UpserterSpec defining the row, its insert values, and its on-conflict updates.
        element_type: The RBAC element type for this entity.
        scope_ref: Primary scope reference (scope_type + scope_id), or ``None`` for a GLOBAL
            entity.
        index_elements: Columns of the unique constraint used as the ON CONFLICT target.
        index_where: Predicate of a partial unique index, when the conflict target is one
            (e.g. ``scope_id IS NULL``); ``None`` for a plain unique constraint.
        additional_scope_refs: Additional scope references for multi-scope entities. Only
            meaningful alongside a ``scope_ref``.
        relation_type: The relation type for the scope-entity association. Defaults to AUTO.
    """

    spec: UpserterSpec[TRow]
    element_type: RBACElementType
    scope_ref: RBACElementRef | None
    index_elements: list[str]
    index_where: Any | None = None
    additional_scope_refs: Sequence[RBACElementRef] = field(default_factory=list)
    relation_type: RelationType = RelationType.AUTO

    def all_scope_refs(self) -> list[RBACElementRef]:
        """Every scope this entity binds to; empty for a GLOBAL entity (``scope_ref=None``)."""
        if self.scope_ref is None:
            return []
        return [self.scope_ref, *self.additional_scope_refs]


@dataclass
class RBACEntityUpserterResult[TRow: Base]:
    """Result of executing a single entity upsert."""

    row: TRow


async def execute_rbac_entity_upserter[TRow: Base](
    db_sess: SASession,
    upserter: RBACEntityUpserter[TRow],
) -> RBACEntityUpserterResult[TRow]:
    """Upsert a scope-scoped entity with its scope association.

    Operations:
    1. INSERT ... ON CONFLICT (``index_elements``) DO UPDATE, RETURNING the row.
    2. Insert AssociationScopesEntitiesRow (scope -> entity) for each scope, ON CONFLICT DO
       NOTHING — so a newly inserted row is bound and an updated row keeps its binding.

    A GLOBAL upserter (``scope_ref=None``) binds to no scope and skips step 2.
    """
    spec = upserter.spec
    row_class = spec.row_class
    table = row_class.__table__
    mapper = inspect(row_class)
    pk_columns = mapper.primary_key
    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Entity upserter only supports single-column primary keys (table: {table.name})",
        )

    stmt = (
        pg_insert(table)
        .values(spec.build_insert_values())
        .on_conflict_do_update(
            index_elements=upserter.index_elements,
            index_where=upserter.index_where,
            set_=spec.build_update_values(),
        )
        .returning(*table.columns)
    )
    try:
        result = await db_sess.execute(stmt)
    except sa.exc.IntegrityError as e:
        # The ON CONFLICT target is handled as an update; any other violation (e.g. a FK gate)
        # still raises and is mapped to a domain error, or re-raised if unmatched.
        match_integrity_error(parse_integrity_error(e), spec.integrity_error_checks)
    row_data = result.fetchone()
    if row_data is None:
        raise UpsertEmptyResultError
    row: TRow = row_class(**dict(row_data._mapping))

    entity_type = upserter.element_type.to_entity_type()
    pk_value = row_data._mapping[pk_columns[0].name]
    associations = [
        AssociationScopesEntitiesRow(
            scope_type=scope_ref.element_type.to_scope_type(),
            scope_id=scope_ref.element_id,
            entity_type=entity_type,
            entity_id=str(pk_value),
            relation_type=upserter.relation_type,
        )
        for scope_ref in upserter.all_scope_refs()
    ]
    await bulk_insert_on_conflict_do_nothing(db_sess, associations)

    return RBACEntityUpserterResult(row=row)
