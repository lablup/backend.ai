"""Upserter for RBAC scope-scoped entity INSERT ON CONFLICT UPDATE operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

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


@dataclass
class RBACEntityUpserter[TRow: Base]:
    """Upserter for a single entity (INSERT ON CONFLICT UPDATE) with its scope associations.

    The upsert counterpart of :class:`RBACEntityCreator`: an inserted row is bound to its
    scope(s), an updated one is bound again as a no-op. ``scope_ref=None`` marks a GLOBAL
    entity that binds to no scope.

    ``index_elements`` is the ON CONFLICT target (``index_where`` for a partial index) and must
    include the scope columns alongside a ``scope_ref`` — the conflict path updates whichever
    row it matches and binds it to ``scope_ref``, so a scope-blind target would let a caller
    overwrite another scope's row. ``relation_type`` applies only to a binding this upsert
    inserts; an already-bound entity keeps its recorded one.
    """

    spec: UpserterSpec[TRow]
    element_type: RBACElementType
    scope_ref: RBACElementRef | None
    index_elements: list[str]
    index_where: sa.ColumnElement[bool] | None = None
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
    """Upsert a scope-scoped entity and bind it to its scope(s).

    Returns the inserted or updated row. See :class:`RBACEntityUpserter` for the conflict
    target the caller has to pick.
    """
    spec = upserter.spec
    row_class = spec.row_class
    table = row_class.__table__
    pk_columns = inspect(row_class).primary_key
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
        # The conflict target is an update, so this is another constraint (a FK gate, say).
        match_integrity_error(parse_integrity_error(e), spec.integrity_error_checks)
    else:
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
