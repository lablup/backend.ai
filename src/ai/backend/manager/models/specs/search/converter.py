"""Turning one row into its data type."""

from __future__ import annotations

from abc import ABC, abstractmethod


class RowDataConverter[TRow, TData](ABC):
    """Builds the data type from a row, reading each value through a declared field.

    Every data field comes from a ``SearchableField`` of the same name, so a data field
    cannot be added without declaring how it is read, filtered and ordered.
    """

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError
