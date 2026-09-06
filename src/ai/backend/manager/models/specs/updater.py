"""Update specs of the v2 lineage.

Updates carry no membership work, so the roots differ only in how they pick what to
write: by id, by id behind a guard, or by conditions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


class DataUpdater[TRow: Base, TData](ABC):
    """Update spec for one row: the target row, the values to set, and how the
    updated row becomes data."""

    @property
    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access and PK detection."""
        raise NotImplementedError

    @abstractmethod
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        """Return the column that carries the id the row is written by.

        Named rather than derived from the primary key: what an operation is
        authorized against is the entity or field id, and a table whose key is a name
        (``domains.name``) still identifies its row by a uuid column beside it. Writing
        by the key while checking by the id lets the two part ways.
        """
        raise NotImplementedError

    @abstractmethod
    def target_id_value(self) -> UUID:
        """Return the id of the row to write."""
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Build the column-to-value mapping to set."""
        raise NotImplementedError

    @property
    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        """Return integrity error checks for declarative error matching."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert the updated row into its ``data/`` type."""
        raise NotImplementedError


class GuardedDataUpdater[TRow: Base, TData](ABC):
    """Update spec for one row that declines to write unless its guard holds.

    The id still names exactly one row — this is not a condition-selected write. The
    guard is a precondition on that row's current values, carried in the statement so
    the read and the write cannot part ways.
    """

    @property
    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access and PK detection."""
        raise NotImplementedError

    @abstractmethod
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        """Return the column that carries the id the row is written by."""
        raise NotImplementedError

    @abstractmethod
    def target_id_value(self) -> UUID:
        """Return the id of the row to write."""
        raise NotImplementedError

    @abstractmethod
    def guard_conditions(self) -> list[QueryCondition]:
        """Return the preconditions the row must satisfy (AND combined).

        They narrow nothing: the row is already named. A row failing them is left
        alone and the operation reports that it wrote nothing.
        """
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Build the column-to-value mapping to set."""
        raise NotImplementedError

    @property
    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        """Return integrity error checks for declarative error matching."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert the updated row into its ``data/`` type."""
        raise NotImplementedError


class DataBatchUpdater[TRow: Base, TData](ABC):
    """Update spec for every row matching its conditions, converting each updated
    row to data so the operation can report what it actually wrote."""

    @property
    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access."""
        raise NotImplementedError

    @abstractmethod
    def conditions(self) -> list[QueryCondition]:
        """Return the WHERE clauses selecting the rows to update (AND combined)."""
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Build the column-to-value mapping to set."""
        raise NotImplementedError

    @property
    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        """Return integrity error checks for declarative error matching."""
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        """Convert one updated row into its ``data/`` type."""
        raise NotImplementedError
