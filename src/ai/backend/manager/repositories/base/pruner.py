"""Pruner spec and cascade abstractions for bulk delete operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)

from .integrity import parse_integrity_error
from .types import QueryCondition

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


class CascadeChild(ABC):
    """A child table whose rows must be deleted before the parent's prune.

    Used for simple FK cascades. Each cascade DELETE runs as::

        DELETE FROM <row_class> WHERE <parent_id_column>
            IN (SELECT <parent pk> FROM <parent>
                WHERE <prune_condition AND conditions>)

    Polymorphic / cross-cutting cleanups (e.g., RBAC associations) are not
    handled here — see :meth:`PrunerSpec.entity_type` for that.
    """

    @classmethod
    @abstractmethod
    def row_class(cls) -> type[Base]:
        """ORM Row class for the cascade table.

        Example:
            return KernelRow
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def parent_id_column(cls) -> Any:
        """FK column on the cascade table that references the parent's PK.

        Example:
            return KernelRow.session_id
        """
        raise NotImplementedError


DEFAULT_PRUNE_LIMIT = 100_000
"""Default cap on rows pruned per call. Bounds memory (parent ID list),
held row locks, and transaction duration."""


@dataclass
class PrunerSpec[TRow: Base](ABC):
    """Spec for a prune operation: entity contract + runtime params + cascade.

    Subclasses declare the entity-level prune contract via classmethods.
    Per-call parameters live on the instance.

    Attributes:
        conditions: Additional WHERE clauses combined (AND) with
            ``prune_condition()``. Use to inject runtime bounds.
        cascade: FK-dependent child tables to delete first within the same
            transaction (see :class:`CascadeChild`).
        limit: Hard cap on rows pruned per call (default
            :data:`DEFAULT_PRUNE_LIMIT`). Required to bound the SELECT FOR
            UPDATE lock set, the in-memory ID list, and transaction
            duration. Operators run multiple calls to drain larger backlogs.
        cascade_rbac: When True (default) and :meth:`entity_type` returns a
            non-None ``EntityType``, ``execute_pruner`` also deletes
            ``association_scopes_entities`` rows whose
            ``(entity_type, entity_id)`` references the pruned parent rows.
    """

    conditions: list[QueryCondition] = field(default_factory=list)
    cascade: list[CascadeChild] = field(default_factory=list)
    limit: int = DEFAULT_PRUNE_LIMIT
    cascade_rbac: bool = True

    @classmethod
    @abstractmethod
    def row_class(cls) -> type[TRow]:
        """ORM Row class for the parent entity table.

        Example:
            return SessionRow
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def returning_id(cls) -> Any:
        """Primary-key column for the parent's ``DELETE ... RETURNING``.

        Example:
            return SessionRow.id
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def prune_condition(cls) -> sa.ColumnElement[bool]:
        """Hardcoded terminal-state WHERE clause for the parent entity.

        Example:
            return SessionRow.status.in_(TERMINAL_SESSION_STATUSES)
        """
        raise NotImplementedError

    @classmethod
    def entity_type(cls) -> EntityType | None:
        """RBAC ``EntityType`` for this entity, or ``None`` to skip RBAC cleanup.

        When non-None and ``cascade_rbac`` is True, ``execute_pruner``
        deletes matching rows in ``association_scopes_entities`` within the
        same transaction. Default: ``None`` (no RBAC cleanup).

        Example:
            return EntityType.SESSION
        """
        return None


@dataclass
class PrunerResult:
    """Result of executing a prune operation.

    Attributes:
        count: Number of parent rows deleted.
        ids: PK values of the deleted parent rows.
    """

    count: int
    ids: list[Any] = field(default_factory=list)


async def execute_pruner[TRow: Base](
    db_sess: SASession,
    spec: PrunerSpec[TRow],
) -> PrunerResult:
    """Execute the prune as a single SELECT FOR UPDATE followed by DELETEs.

    Order within the transaction:

    1. ``SELECT pk FOR UPDATE LIMIT spec.limit`` to lock the target parent
       rows and materialize their IDs once.
    2. FK cascade children (``spec.cascade``) — each DELETE uses
       ``parent_id_column.in_(target_ids)``.
    3. RBAC associations (when ``spec.cascade_rbac`` is True and
       ``spec.entity_type()`` is not None) — IDs are stringified for the
       polymorphic ``entity_id`` text column.
    4. Parent DELETE with ``RETURNING`` to surface the pruned PK list.

    Materializing the locked ID list avoids re-evaluating the parent SELECT
    in every cascade subquery and removes the race window between
    statements.

    Args:
        db_sess: Database session (must be writable).
        spec: PrunerSpec instance carrying conditions, cascade, and limit.

    Returns:
        PrunerResult with the count and PK list of deleted parent rows.

    Raises:
        RepositoryIntegrityError: If any DELETE violates a database constraint.
    """
    cls = type(spec)
    table = cls.row_class().__table__
    pk_col = cls.returning_id()

    where = cls.prune_condition()
    for f in spec.conditions:
        where = sa.and_(where, f())

    target_q = sa.select(pk_col).where(where).with_for_update().limit(spec.limit)
    target_ids = list((await db_sess.scalars(target_q)).all())
    if not target_ids:
        return PrunerResult(count=0, ids=[])

    for child in spec.cascade:
        ccls = type(child)
        cascade_table = ccls.row_class().__table__
        await db_sess.execute(
            sa.delete(cascade_table).where(ccls.parent_id_column().in_(target_ids))
        )

    rbac_entity_type = cls.entity_type()
    if spec.cascade_rbac and rbac_entity_type is not None:
        await db_sess.execute(
            sa.delete(AssociationScopesEntitiesRow).where(
                AssociationScopesEntitiesRow.entity_type == rbac_entity_type,
                AssociationScopesEntitiesRow.entity_id.in_([str(i) for i in target_ids]),
            )
        )

    stmt = sa.delete(table).where(pk_col.in_(target_ids)).returning(pk_col)
    try:
        deleted = list((await db_sess.scalars(stmt)).all())
    except sa.exc.IntegrityError as e:
        raise parse_integrity_error(e) from e

    return PrunerResult(count=len(deleted), ids=deleted)
