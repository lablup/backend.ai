"""DataQuerier implementations for the project resource policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class ProjectResourcePolicyQuerier(
    DataQuerier[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    name: str

    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()
