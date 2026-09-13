"""Write specs for a login client type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.creators import LoginClientTypeCreator


@dataclass(frozen=True)
class SeedLoginClientType(SeedRow[LoginClientTypeData]):
    """A login client type in the global catalog."""

    name_hint: str = "client"
    description: str | None = "미리 만들어 둔 로그인 클라이언트 종류"

    @override
    def kind(self) -> str:
        return "로그인 클라이언트 종류"

    @override
    def detail(self) -> str:
        return "" if self.description is not None else "설명 없음"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> LoginClientTypeCreator:
        return LoginClientTypeCreator(name=name, description=self.description)
