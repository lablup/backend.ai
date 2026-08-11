"""Update specs of the v2 lineage.

Updates carry no membership work, so a single root serves all families; the batch
variant selects by conditions instead of a primary key.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any
from uuid import UUID

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
    def pk_value(self) -> UUID | str | int:
        """Return the primary key value identifying the target row."""
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
