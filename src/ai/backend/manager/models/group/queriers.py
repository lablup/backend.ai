"""Query specs for the groups table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class ProjectQuerier(DataQuerier[GroupRow, GroupData]):
    """Reads one project by its id."""

    project_id: ProjectID

    @override
    def row_class(self) -> type[GroupRow]:
        return GroupRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return GroupRow.id

    @override
    def entity_id_value(self) -> ProjectID:
        return self.project_id

    @override
    def to_data(self, row: GroupRow) -> GroupData:
        return row.to_data()
