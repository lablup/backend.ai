"""Write specs for a runtime variant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.creators import RuntimeVariantCreator
from bai_scenario.seeds.seeder import Naming, SeedRow


@dataclass(frozen=True)
class SeedRuntimeVariant(SeedRow[RuntimeVariantData]):
    """A runtime a revision names.

    The write spec stores an empty baseline model definition and takes no say on reading
    config files from the model folder, so the variant reads none.
    """

    name_hint: str = "runtime"
    description: str | None = None

    @override
    def kind(self) -> str:
        return "런타임 변형"

    @override
    def detail(self) -> str:
        return "기본 모델 정의가 비어 있고, 모델 폴더의 설정 파일을 읽지 않는다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> RuntimeVariantCreator:
        return RuntimeVariantCreator(name=name, description=self.description)
