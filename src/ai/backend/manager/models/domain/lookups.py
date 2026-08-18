"""Lookup implementations for the domain table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainName
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class DomainNameLookup(DataLookup[DomainRow, DomainData]):
    """Resolves a domain's name into the domain it names."""

    name: DomainName

    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: DomainRow.name == self.name]

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()
