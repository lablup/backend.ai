"""Upserter input for RBAC scope-scoped entity INSERT ON CONFLICT UPDATE operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, TypeVar

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.base import Base
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
