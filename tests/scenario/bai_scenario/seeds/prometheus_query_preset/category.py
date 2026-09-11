"""Write specs for a query preset category."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow

from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.creators import (
    PrometheusQueryPresetCategoryCreator,
)


@dataclass(frozen=True)
class SeedCategory(SeedRow[PrometheusQueryPresetCategoryData]):
    """A category in the global preset catalog. The name is the seeder's."""

    name_hint: str = "category"
    description: str | None = "심어둔 분류"

    @override
    def kind(self) -> str:
        return "분류"

    @override
    def detail(self) -> str:
        return "" if self.description is not None else "설명이 없다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> PrometheusQueryPresetCategoryCreator:
        return PrometheusQueryPresetCategoryCreator(name=name, description=self.description)
