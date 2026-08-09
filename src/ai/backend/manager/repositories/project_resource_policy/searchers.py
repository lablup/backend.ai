"""Searcher implementations for the project resource policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ProjectResourcePolicySearcher(Searcher[ProjectResourcePolicyRow, ProjectResourcePolicyData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ProjectResourcePolicyRow)

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()
