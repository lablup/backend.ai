"""Searcher implementations for the resource slot repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ResourceSlotTypeSearcher(Searcher[ResourceSlotTypeRow, ResourceSlotTypeData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ResourceSlotTypeRow)

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return row.to_data()
