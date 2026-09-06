"""Searcher spec for the huggingface_registries table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class HuggingFaceRegistrySearcher(Searcher[HuggingFaceRegistryRow, HuggingFaceRegistryData]):
    """The name is the meta row's, so every read loads it."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(HuggingFaceRegistryRow).options(selectinload(HuggingFaceRegistryRow.meta))

    @override
    def to_data(self, row: HuggingFaceRegistryRow) -> HuggingFaceRegistryData:
        return row.to_dataclass()
