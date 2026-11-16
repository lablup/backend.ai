"""Write specs for a login client type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.creators import LoginClientTypeCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow


@dataclass(frozen=True)
class TestSeedLoginClientType(TestSeedRow[LoginClientTypeData]):
    """A login client type in the global catalog."""

    name_hint: str = "client"
    description: str | None = Says(
        "미리 생성한 로그인 클라이언트 종류",
        english="a login client type created in advance",
    )

    @override
    def kind(self) -> str:
        return Says("로그인 클라이언트 종류", english="Login client type")

    @override
    def detail(self) -> str:
        if self.description is not None:
            return Says("")
        return Says("설명 없음", english="no description")

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> LoginClientTypeCreator:
        return LoginClientTypeCreator(name=name, description=self.description)
