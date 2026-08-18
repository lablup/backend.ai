"""Searcher implementations for the runtime variant repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class RuntimeVariantSearcher(Searcher[RuntimeVariantRow, RuntimeVariantData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RuntimeVariantRow)

    @override
    def to_data(self, row: RuntimeVariantRow) -> RuntimeVariantData:
        return row.to_data()
