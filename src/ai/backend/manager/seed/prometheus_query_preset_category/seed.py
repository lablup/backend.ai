from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.models.prometheus_query_preset_category.upserters import (
    PrometheusQueryPresetCategoryUpserter,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class PrometheusQueryPresetCategorySeed(SeedItem):
    """One ``prometheus_query_preset_categories`` row, keyed by its id."""

    id: PrometheusQueryPresetCategoryID
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=PrometheusQueryPresetCategoryUpserter(
                id=self.id, name=self.name, description=self.description
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        """The rule the create API applies to the name."""
        if not self.name.strip():
            return ["name is blank"]
        return []

    @override
    @classmethod
    def reject(
        cls, files: Sequence[SeedItems[PrometheusQueryPresetCategorySeed]]
    ) -> list[SeedRejection]:
        return []
