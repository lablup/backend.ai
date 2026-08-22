"""Searcher implementations for the runtime variant preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class RuntimeVariantPresetSearcher(Searcher[RuntimeVariantPresetRow, RuntimeVariantPresetData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RuntimeVariantPresetRow)

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return row.to_data()
