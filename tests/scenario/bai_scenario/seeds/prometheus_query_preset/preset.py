"""Write specs for a query preset.

A preset goes in through the creator alone, so a template the renderer would refuse at
the API still lands here. A row that needs one stored says so with ``query_template``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import override

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
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow, TestSeedRowFrom, joined

METRIC = "container_cpu_seconds_total"
TEMPLATE = "avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))"
"""A template the renderer accepts: literal PromQL and the three placeholders."""

EMPTY_WITHOUT_LABELS = "${{labels}}"
"""A template the renderer accepts that renders to nothing when no label is given.
Prometheus refuses the empty query it becomes."""


@dataclass(frozen=True)
class TestSeedPreset(TestSeedRow[PrometheusQueryPresetData]):
    """A query preset in the global catalog, filed under no category."""

    name_hint: str = "preset"
    description: str | None = Says(
        "미리 생성한 질의 프리셋",
        english="a query preset created in advance",
    )
    query_template: str = TEMPLATE
    time_window: str | None = None
    filter_labels: Sequence[str] = ()
    group_labels: Sequence[str] = ()

    @override
    def kind(self) -> str:
        return Says("질의 프리셋", english="Query preset")

    @override
    def detail(self) -> str:
        says: list[str] = []
        if self.query_template == EMPTY_WITHOUT_LABELS:
            says.append(
                Says(
                    "라벨이 없으면 빈 질의로 렌더되는 템플릿을 가집니다",
                    english="has a template that renders to an empty query without labels",
                )
            )
        if self.time_window is not None:
            says.append(
                Says(
                    f"시간 창을 {self.time_window} 값으로 설정합니다",
                    english=f"sets the time window to {self.time_window}",
                )
            )
        if self.filter_labels:
            filter_values = ", ".join(self.filter_labels)
            says.append(
                Says(
                    f"필터 라벨을 {filter_values} 값으로 제한합니다",
                    english=f"limits filter labels to {filter_values}",
                )
            )
        if self.group_labels:
            group_values = ", ".join(self.group_labels)
            says.append(
                Says(
                    f"그룹 라벨을 {group_values} 값으로 제한합니다",
                    english=f"limits group labels to {group_values}",
                )
            )
        return joined(says, ", ")

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
class TestSeedPresetIn(
    TestSeedRowFrom[PrometheusQueryPresetCategoryData, PrometheusQueryPresetData]
):
    """The same preset, filed under the given category."""

    preset: TestSeedPreset = TestSeedPreset()

    @override
    def kind(self) -> str:
        return self.preset.kind()

    @override
    def detail(self) -> str:
        parts: list[str] = [Says("카테고리에 속합니다", english="belongs to a category")]
        if preset_detail := self.preset.detail():
            parts.append(preset_detail)
        return joined(parts, ", ")

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
