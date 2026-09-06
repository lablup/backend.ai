"""Delete specs of the v2 lineage.

The roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityIdentifier, FieldData
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import ConflictCheck


class EntityPurger[TRow: Base, TData](ABC):
    """Delete spec of one entity named by id.

    Removing the row removes what it left in the RBAC graph. Declared separately from
    ``pk_value()`` because a primary key is not always the entity id.
    """

    @abstractmethod
    def entity_id(self) -> EntityIdentifier:
        """The id of the entity this row is."""
        raise NotImplementedError

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        """Return the column carrying the entity id, which the delete keys on."""
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class FieldPurger[TRow: Base, TData: FieldData](ABC):
    """Delete spec of a field row — authorized through its owner, like an update
    to the owning entity; no scope to tear down."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        """Return the column carrying the field id, which the delete keys on."""
        raise NotImplementedError

    @abstractmethod
    def target_id_value(self) -> UUID:
        """Return the id of the field row to delete."""
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class GuardedFieldPurger[TRow: Base, TData: FieldData](ABC):
    """Delete spec of a field row that declines to delete unless its guard holds.

    The id still names exactly one row. The guard is a precondition on that row's
    current values, carried in the statement so the read and the delete cannot part
    ways.
    """

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        """Return the column carrying the field id, which the delete keys on."""
        raise NotImplementedError

    @abstractmethod
    def target_id_value(self) -> UUID:
        """Return the id of the field row to delete."""
        raise NotImplementedError

    @abstractmethod
    def guard_conditions(self) -> list[QueryCondition]:
        """Return the preconditions the row must satisfy (AND combined).

        They narrow nothing: the row is already named. A row failing them is left
        alone and the operation reports that it removed nothing.
        """
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class FieldBatchPurger[TOwnerID: EntityIdentifier, TRow: Base, TData](ABC):
    """Delete spec for the field rows of one owner that a subquery selects, converting
    each deleted row to data so the operation can report what it actually removed.

    A field row holds nothing in the RBAC graph, so the delete is the whole operation —
    the batch counterpart of :class:`FieldPurger`. Bounded by the owner rather than by a
    scope, as every field write is: what authorizes the rows is the entity owning them.
    """

    @abstractmethod
    def build_subquery(self, owner_id: TOwnerID) -> sa.sql.Select[tuple[TRow]]:
        """Build the subquery selecting the owner's rows to delete."""
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        """Return rows that must not exist before deletion (empty if none)."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert one deleted row into its ``data/`` type."""
        raise NotImplementedError


class EntityBatchPurger[TRow: Base, TData](ABC):
    """Delete spec for every entity row a subquery selects; each row's RBAC graph goes
    with it, as :class:`EntityPurger` does for one.

    Deliberately NOT a :class:`FieldBatchPurger` subtype — the hooks are duplicated
    instead — so an entity spec cannot flow through the field path and leave its virtual
    scope, memberships and permissions behind.
    """

    @abstractmethod
    def entity_id(self, row: TRow) -> EntityIdentifier:
        """The id of the entity a deleted row was, read off that row.

        Takes the row because the selection names no id; it answers its own type, so
        nothing declares the type separately.
        """
        raise NotImplementedError

    @abstractmethod
    def build_subquery(self) -> sa.sql.Select[tuple[TRow]]:
        """Build the subquery selecting the rows to delete."""
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        """Return rows that must not exist before deletion (empty if none)."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert one deleted row into its ``data/`` type."""
        raise NotImplementedError
