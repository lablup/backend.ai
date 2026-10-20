"""리소스 프리셋 purge — 누가 지울 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ResourcePresetNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    ThePurgedPresetId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PurgingStep = Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, UUID]


@dataclass(frozen=True)
class Purging(When[APresetAndACaller, ResourcePresetAdapter, UUID]):
    """미리 만든 프리셋 하나를 purge 한다. 답이 실은 id 를 벗겨서 준다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "없는 id" if self.unknown else laid.preset.name
        return f"{laid.caller.username}이 {target}을 purge 함"

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: APresetAndACaller) -> UUID:
        with ActingAs(laid.caller):
            payload = await adapter.purge(uuid4() if self.unknown else laid.preset.id)
        return payload.id


@dataclass(frozen=True)
class TheSuperadminPurgesAPreset(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, UUID]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-preset"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 프리셋을 purge 하면 지운 프리셋의 id 가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, UUID]:
        return Purging()

    @override
    def then(self) -> Then[APresetAndACaller, UUID]:
        return ThePurgedPresetId()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, UUID]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-preset"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 프리셋을 purge 하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, UUID]:
        return Purging()

    @override
    def then(self) -> Then[APresetAndACaller, UUID]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, UUID]
):
    @override
    def summary(self) -> str:
        return "purging-an-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 없는 id 의 프리셋을 purge 하려 하면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, UUID]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[APresetAndACaller, UUID]:
        return TheCallIsRefused(ResourcePresetNotFound)


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesAPreset(),
    AUserGrantedNothingMayNotPurge(),
    AnIdNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: ResourcePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
