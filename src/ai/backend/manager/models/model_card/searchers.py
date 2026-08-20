"""Searcher specs for the model cards table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ModelCardSearcher(Searcher[ModelCardRow, ModelCardData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ModelCardRow)

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardData:
        return row.to_data()
