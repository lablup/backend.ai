"""Delete specs of the v2 lineage.

The family roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import ConflictCheck


class GlobalEntityPurger[TRow: Base, TData](ABC):
    """Delete spec of a global entity; no scope to tear down."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def pk_value(self) -> UUID | str | int:
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class EntityPurger[TRow: Base, TData](ABC):
    """Delete spec of an entity: purging the row tears its scope down with it
    (the virtual scope node, the edges it left elsewhere, and any permissions
    granted on it), symmetrically with the entity create.

    ``scope_of()`` takes no row: the scope's identity is known from the purge
    target itself, and the spec carries whatever fields name it — the scope id
    is not necessarily the row's primary key.
    """

    @abstractmethod
    def scope_of(self) -> ScopeRef:
        """The scope being torn down."""
        raise NotImplementedError

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def pk_value(self) -> UUID | str | int:
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class FieldEntityPurger[TRow: Base, TData](ABC):
    """Delete spec of a field row — authorized through its owner, like an update
    to the owning entity; no scope to tear down."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def pk_value(self) -> UUID | str | int:
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class DataBatchPurger[TRow: Base, TData](ABC):
    """Delete spec for every row a subquery selects, converting each deleted row
    to data so the operation can report what it actually removed.

    Carries no scope teardown: reserve it for global- and field-family rows
    until a batch purge that tears scopes down exists.
    """

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
