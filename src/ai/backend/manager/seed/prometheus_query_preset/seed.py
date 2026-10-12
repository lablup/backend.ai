from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.models.prometheus_query_preset.row import PresetOptions
from ai.backend.manager.models.prometheus_query_preset.upserters import (
    PrometheusQueryPresetUpserter,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class PrometheusQueryPresetSeed(SeedItem):
    """One ``prometheus_query_presets`` row, keyed by its id."""

    id: PrometheusQueryPresetID
    name: str = Field(min_length=1, max_length=256)
    metric_name: str = Field(min_length=1, max_length=256)
    query_template: str = Field(min_length=1)
    time_window: str | None = Field(default=None, max_length=32)
    options: PresetOptions
    description: str | None = None
    rank: int = Field(default=0, ge=-(2**31), le=2**31 - 1)
    category_id: PrometheusQueryPresetCategoryID | None = None

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=PrometheusQueryPresetUpserter(
                id=self.id,
                name=self.name,
                metric_name=self.metric_name,
                query_template=self.query_template,
                time_window=self.time_window,
                options=self.options,
                description=self.description,
                rank=self.rank,
                category_id=self.category_id,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[PrometheusQueryPresetSeed]]) -> list[SeedRejection]:
        return []
