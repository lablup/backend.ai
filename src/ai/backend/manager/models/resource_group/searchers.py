"""Searcher specs for the scaling_groups table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ResourceGroupSearcher(Searcher[ResourceGroupRow, ResourceGroupData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ResourceGroupRow)

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        return row.to_dataclass()
