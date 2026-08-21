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

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.base import Base
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


class FieldPurger[TRow: Base, TData](ABC):
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


class DataBatchPurger[TRow: Base, TData](ABC):
    """Delete spec for every row a subquery selects, converting each deleted row
    to data so the operation can report what it actually removed.

    Carries no scope teardown: reserve it for rows that provision no scope
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
