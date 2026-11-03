"""프리셋 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.role_preset.request import CreateRolePresetInput
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.system import lay_a_caller
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MADE = "made-preset"
"""만들려는 프리셋의 이름. 시나리오가 정한 값이다."""

type CreatingStep = Scenario[TestSeedingSession, UserData, RolePresetAdapter, RolePresetNode]


@dataclass(frozen=True)
class TheSuperadmin(Given[Any, UserData]):
    """프리셋을 만들려는 슈퍼관리자 한 명."""

    @override
    def describe(self) -> str:
        return "슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: Any) -> UserData:
        caller: UserData = seeding.made(await lay_a_caller(seeding, UserRole.SUPERADMIN))
        return caller


@dataclass(frozen=True)
class CreatingWithOwnerAssign(When[UserData, RolePresetAdapter, RolePresetNode]):
    """소유자 부여를 켠 프로젝트 스코프 프리셋을 만든다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: UserData) -> str:
        return f"{laid.username}이 소유자 부여를 켠 프로젝트 스코프 프리셋을 만듦"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: UserData) -> RolePresetNode:
        with ActingAs(laid):
            payload = await adapter.create(
                CreateRolePresetInput(
                    name=MADE, scope_type=ProjectEntityType(), auto_assign_to_owner=True
                )
            )
        return payload.role_preset


@dataclass(frozen=True)
class OwnerAssignComesBackOn(Then[UserData, RolePresetNode]):
    """소유자 부여가 켜진 프리셋이 온다."""

    @override
    def says(self) -> str:
        return "소유자 부여가 켜진 프리셋이 온다"

    @override
    def look(self, laid: UserData, answered: Answered[RolePresetNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("name", node.name, MADE),
            Same("auto_assign_to_owner", node.auto_assign_to_owner, True),
        ]


@dataclass(frozen=True)
class AProjectPresetIsMadeWithOwnerAssign(
    Scenario[TestSeedingSession, UserData, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-project-preset-is-made-with-owner-assign"

    @override
    def describe(self) -> str:
        return "프로젝트 스코프 프리셋을 소유자 부여를 켜고 만들면, 켜진 프리셋이 온다"

    @override
    def given(self) -> Given[TestSeedingSession, UserData]:
        return TheSuperadmin()

    @override
    def when(self) -> When[UserData, RolePresetAdapter, RolePresetNode]:
        return CreatingWithOwnerAssign()

    @override
    def then(self) -> Then[UserData, RolePresetNode]:
        return OwnerAssignComesBackOn()


SCENARIOS: list[CreatingStep] = [
    AProjectPresetIsMadeWithOwnerAssign(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
