"""Upserter input for RBAC scope-scoped entity INSERT ON CONFLICT UPDATE operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base.upserter import BulkUpserterError, UpserterSpec


@dataclass(frozen=True)
class ConflictTarget:
    """The unique index ON CONFLICT arbitrates on — a violation of it updates, any other
    constraint still raises.

    Attributes:
        columns: Columns of the index to infer.
        index_predicate: The WHERE of a partial index (e.g. ``scope_id IS NULL``), which has
            to match the index definition for the inference to succeed. ``None`` for a plain
            unique constraint. This is not a filter on the update — it only picks the index.
    """

    columns: list[str]
    index_predicate: sa.ColumnElement[bool] | None = None


@dataclass
class RBACEntityUpserter[TRow: Base]:
    """Upserter for a single entity (INSERT ON CONFLICT UPDATE) with its scope associations.

    The upsert counterpart of :class:`RBACEntityCreator`: an inserted row is bound to its
    scope(s), an updated one is bound again as a no-op. ``scope_ref=None`` marks a GLOBAL
    entity that binds to no scope.

    ``conflict_target`` must include the scope columns alongside a ``scope_ref`` — the conflict
    path updates whichever row it matches and binds it to ``scope_ref``, so a scope-blind
    target would let a caller overwrite another scope's row. ``relation_type`` applies only to
    a binding this upsert inserts; an already-bound entity keeps its recorded one.
    """

    spec: UpserterSpec[TRow]
    element_type: RBACElementType
    scope_ref: RBACElementRef | None
    conflict_target: ConflictTarget
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


@dataclass
class RBACBulkEntityUpserterResultWithFailures[TRow: Base]:
    """Result of a scoped bulk upsert that isolates each entity.

    Mirrors :class:`RBACBulkEntityCreatorResultWithFailures`. ``errors`` index into the
    sequence of upserters handed to the executor, not into any list the caller may have
    derived it from.
    """

    successes: list[TRow]
    errors: list[BulkUpserterError[TRow]]
