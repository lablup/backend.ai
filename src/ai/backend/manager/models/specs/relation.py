"""Relation specs of the v2 lineage: rows that link two entities.

A relation belongs to neither of the entities it links — both own it — so it is neither
an entity nor a field. The roots below are unrelated to the entity and field roots for
the same reason those are unrelated to each other: a relation must not flow through a
path that would provision or tear down a graph node it never had.

Design rationale: `proposals/BEP-1075-entity-relation-operations.md`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import ConflictCheck, IntegrityErrorCheck


class RelationCreator[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](ABC):
    """Insert spec of a row linking two entities.

    Takes both ids rather than an owner: the pair is what names the row, and the caller
    holds the pair and not the row's id. Typed by the pair's id types, so a spec reads
    each id as what it is.

    Answers no ``data``. A relation is not returned to a caller — what a read answers
    with is the entities the relation reaches, never the relation.

    A pair already linked, switched off or not, is a unique violation the spec maps to a
    domain error; switching it back on is the restore updater's, not the create's.
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self, scope: TScope, target: TTarget) -> TRow:
        """Build the row linking the scope to the target."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError


class RelationLifecycleUpdater[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
    ABC
):
    """Update spec that switches one relation off or back on.

    ``build_values`` returns a constant, as the entity soft delete's updaters do: a
    transition value taken as an argument is a value that can be passed wrong. A
    relation declares one class per direction, and which of the two an operation is
    comes from the ops method it is handed to.

    Switching touches the row alone: what each side reads of the other stays, so a
    relation switched off is still listed on both sides and can be switched back on.
    Only relations carrying a lifecycle column declare these. A relation without one is
    linked and purged, and has nothing to switch.
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def conditions(self, scope: TScope, target: TTarget) -> Sequence[QueryCondition]:
        """Return the conditions naming the pair's row, AND combined."""
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Return the constant the lifecycle column is written with."""
        raise NotImplementedError


class RelationPurger[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](ABC):
    """Delete spec of the row linking two entities.

    Names the row by the pair, never by its own id: a relation row holds nothing in the
    graph, and nothing outside it holds that id. An entity going away takes its rows
    with it through the table's foreign keys, so nothing names a whole side.
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def conditions(self, scope: TScope, target: TTarget) -> Sequence[QueryCondition]:
        """Return the conditions naming the pair's row, AND combined."""
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        """Return rows that must not exist before the link is removed (empty if none)."""
        raise NotImplementedError
