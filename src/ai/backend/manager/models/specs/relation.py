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


class RelationCreator[TRow: Base](ABC):
    """Insert spec of a row linking two entities.

    Takes both ids rather than an owner: the pair is what names the row, and the caller
    holds the pair and not the row's id.

    Answers no ``data``. A relation is not returned to a caller — what a read answers
    with is the entities the relation reaches, never the relation.
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self, left: EntityIdentifier, right: EntityIdentifier) -> TRow:
        """Build the row linking the two entities."""
        raise NotImplementedError

    @abstractmethod
    def index_elements(self) -> list[str]:
        """The column names conflict detection keys on.

        Whether a soft-deleted row occupies the pair is a property of the table's own
        unique constraint, so what conflicts is declared here rather than assumed.
        """
        raise NotImplementedError

    @abstractmethod
    def build_conflict_values(self) -> dict[str, Any] | None:
        """What to write when the pair is already taken.

        ``None`` leaves the existing row alone. A mapping revives it — which is what a
        table whose unique constraint covers the bare pair needs, since a soft-deleted
        row still occupies it and an insert that did nothing would leave the relation
        switched off.
        """
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError


class RelationLifecycleUpdater[TRow: Base](ABC):
    """Update spec that switches one relation off or back on.

    ``build_values`` returns a constant, as the entity soft delete's updaters do: a
    transition value taken as an argument is a value that can be passed wrong. A
    relation declares one class per direction, and which of the two an operation is
    comes from the ops method it is handed to.

    Only relations carrying a lifecycle column declare these. A relation without one is
    linked and purged, and has nothing to switch.
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def conditions(
        self, left: EntityIdentifier, right: EntityIdentifier
    ) -> Sequence[QueryCondition]:
        """Return the conditions naming the pair's row, AND combined."""
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Return the constant the lifecycle column is written with."""
        raise NotImplementedError


class RelationPurger[TRow: Base](ABC):
    """Delete spec of the row linking two entities.

    Names the row by the pair, never by its own id: a relation row holds nothing in the
    graph, and nothing outside it holds that id.
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def conditions(
        self, left: EntityIdentifier, right: EntityIdentifier
    ) -> Sequence[QueryCondition]:
        """Return the conditions naming the pair's row, AND combined."""
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        """Return rows that must not exist before the link is removed (empty if none)."""
        raise NotImplementedError
