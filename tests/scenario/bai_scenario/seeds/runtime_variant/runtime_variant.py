"""Write specs for a runtime variant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow

from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.creators import RuntimeVariantCreator


@dataclass(frozen=True)
class SeedRuntimeVariant(SeedRow[RuntimeVariantData]):
    """A runtime variant in the global catalog. It is created in no scope."""

    name_hint: str = "variant"
    description: str | None = "심어둔 런타임 변형"

    @override
    def kind(self) -> str:
        return "런타임 변형"

    @override
    def detail(self) -> str:
        return "" if self.description is not None else "설명 없음"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> RuntimeVariantCreator:
        return RuntimeVariantCreator(name=name, description=self.description)
