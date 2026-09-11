"""Write specs for a query preset.

A preset goes in through the creator alone, so a template the renderer would refuse at
the API still lands here. A row that needs one stored says so with ``query_template``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow, SeedRowFrom

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreator,
)

METRIC = "container_cpu_seconds_total"
TEMPLATE = "avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))"
"""A template the renderer accepts: literal PromQL and the three placeholders."""

UNRENDERABLE = "up${{ nope }}"
"""A template the renderer refuses: it names a variable no placeholder provides."""

EMPTY_WITHOUT_LABELS = "${{labels}}"
"""A template the renderer accepts that renders to nothing when no label is given.
Prometheus refuses the empty query it becomes."""


@dataclass(frozen=True)
class SeedPreset(SeedRow[PrometheusQueryPresetData]):
    """A query preset in the global catalog, filed under no category."""

    name_hint: str = "preset"
    description: str | None = "미리 만들어 둔 질의 프리셋"
    query_template: str = TEMPLATE
    time_window: str | None = None
    filter_labels: Sequence[str] = ()
    group_labels: Sequence[str] = ()

    @override
    def kind(self) -> str:
        return "질의 프리셋"

    @override
    def detail(self) -> str:
        says: list[str] = []
        if self.query_template == UNRENDERABLE:
            says.append("렌더러가 받지 않는 템플릿을 갖는다")
        if self.query_template == EMPTY_WITHOUT_LABELS:
            says.append("라벨 없이는 빈 질의로 렌더되는 템플릿을 갖는다")
        if self.time_window is not None:
            says.append(f"시간 창이 {self.time_window}(으)로 설정돼 있다")
        if self.filter_labels:
            says.append(f"필터 라벨을 {', '.join(self.filter_labels)}(으)로 제한한다")
        if self.group_labels:
            says.append(f"그룹 라벨을 {', '.join(self.group_labels)}(으)로 제한한다")
        return ", ".join(says)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> PrometheusQueryPresetCreator:
        return PrometheusQueryPresetCreator(
            name=name,
            description=self.description,
            metric_name=METRIC,
            query_template=self.query_template,
            time_window=self.time_window,
            filter_labels=list(self.filter_labels),
            group_labels=list(self.group_labels),
        )


@dataclass(frozen=True)
class SeedPresetIn(SeedRowFrom[PrometheusQueryPresetCategoryData, PrometheusQueryPresetData]):
    """The same preset, filed under the given category."""

    preset: SeedPreset = SeedPreset()

    @override
    def kind(self) -> str:
        return self.preset.kind()

    @override
    def detail(self) -> str:
        return ", ".join(one for one in ("카테고리에 속한다", self.preset.detail()) if one)

    @override
    def name(self, naming: Naming) -> str:
        return self.preset.name(naming)

    @override
    def seed(
        self, name: str, source: PrometheusQueryPresetCategoryData
    ) -> PrometheusQueryPresetCreator:
        return replace(
            self.preset.seed(name), category_id=PrometheusQueryPresetCategoryID(source.id)
        )
