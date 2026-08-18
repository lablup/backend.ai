"""Lookup implementations for the group table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainName
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ProjectNameInDomainLookup(DataLookup[GroupRow, GroupData]):
    """Resolves a project's name within its domain into the project it names.

    The pair is the table's unique constraint: a name is only unique inside one domain.
    """

    domain_name: DomainName
    project_name: str

    @override
    def row_class(self) -> type[GroupRow]:
        return GroupRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: GroupRow.domain_name == self.domain_name,
            lambda: GroupRow.name == self.project_name,
        ]

    @override
    def to_data(self, row: GroupRow) -> GroupData:
        return row.to_data()
