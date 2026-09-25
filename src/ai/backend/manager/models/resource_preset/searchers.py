"""List-read spec for resource presets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_preset.searchable_fields import (
    ResourcePresetSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ResourcePresetSearcher(Searcher[ResourcePresetRow, ResourcePresetData]):
    """Resource presets matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ResourcePresetRow)

    @override
    def to_data(self, row: ResourcePresetRow) -> ResourcePresetData:
        return ResourcePresetSearchableFields.own.to_data(row)
