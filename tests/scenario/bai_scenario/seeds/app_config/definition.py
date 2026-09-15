"""Write specs for an app config definition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow

from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.creators import AppConfigDefinitionCreator


@dataclass(frozen=True)
class SeedDefinition(SeedRow[AppConfigDefinitionData]):
    """One registered config name. The name is the seeder's and doubles as the config name."""

    name_hint: str = "config"

    @override
    def kind(self) -> str:
        return "설정 정의"

    @override
    def detail(self) -> str:
        return "이 이름의 설정이 등록돼 있다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> AppConfigDefinitionCreator:
        return AppConfigDefinitionCreator(config_name=name)
