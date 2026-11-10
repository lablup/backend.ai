"""Write specs for a query preset category."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.creators import (
    PrometheusQueryPresetCategoryCreator,
)
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow


@dataclass(frozen=True)
class TestSeedCategory(TestSeedRow[PrometheusQueryPresetCategoryData]):
    """A category in the global preset catalog. The name is the seeder's."""

    name_hint: str = "category"
    description: str | None = Says("미리 생성한 카테고리", english="a category created in advance")

    @override
    def kind(self) -> str:
        return Says("카테고리", english="Category")

    @override
    def detail(self) -> str:
        if self.description is not None:
            return Says("")
        return Says("설명 없음", english="no description")

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> PrometheusQueryPresetCategoryCreator:
        return PrometheusQueryPresetCategoryCreator(name=name, description=self.description)
