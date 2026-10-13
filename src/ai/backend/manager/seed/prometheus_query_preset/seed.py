from __future__ import annotations

import re
from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.dto.clients.prometheus.defs import PROMETHEUS_DURATION_PATTERN
from ai.backend.common.exception import InvalidMetricPresetTemplate
from ai.backend.manager.clients.prometheus.preset import PromQLTemplateRenderer
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
    def check(self) -> list[str]:
        """The rules the create API applies to the name, the rank, the window and the
        template."""
        failures: list[str] = []
        if not self.name.strip():
            failures.append("name is blank")
        if self.rank < 0:
            failures.append(f"rank {self.rank} is negative")
        if self.time_window is not None and not re.fullmatch(
            PROMETHEUS_DURATION_PATTERN, self.time_window
        ):
            failures.append(f"time_window {self.time_window!r} is not a Prometheus duration")
        try:
            PromQLTemplateRenderer().validate(self.query_template)
        except InvalidMetricPresetTemplate as e:
            failures.append(str(e))
        return failures

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[PrometheusQueryPresetSeed]]) -> list[SeedRejection]:
        return []
