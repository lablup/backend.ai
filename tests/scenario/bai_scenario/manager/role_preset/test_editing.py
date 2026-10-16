"""프리셋 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.role_preset.request import UpdateRolePresetBody
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    PresetLook,
    ThePresetComesBack,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

RENAMED = "renamed-preset"

type EditingStep = Scenario[
    TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode
]


@dataclass(frozen=True)
class Renaming(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """프리셋 이름을 바꾼다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.preset.name}의 이름을 {RENAMED}(으)로 바꿈"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(laid.preset.id, UpdateRolePresetBody(name=RENAMED))
        return payload.role_preset


@dataclass(frozen=True)
class TheSuperadminRenamesIt(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-renames-a-preset"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 프리셋 이름을 바꾸면, 새 이름을 실은 프리셋 전체가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Renaming()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return ThePresetComesBack(PresetLook(self.started, named=RENAMED))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRename(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-rename-a-preset"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 프리셋 이름을 바꾸려 하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Renaming()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[EditingStep] = [
    TheSuperadminRenamesIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRename(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
