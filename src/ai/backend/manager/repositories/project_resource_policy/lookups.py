"""DataLookup implementations for the project resource policy repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.specs.lookup import DataLookup

__all__ = ("ProjectResourcePolicyNameLookup",)


@dataclass
class ProjectResourcePolicyNameLookup(
    DataLookup[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Resolves a policy's name into the policy it names."""

    name: str

    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ProjectResourcePolicyRow.name == self.name]

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()
