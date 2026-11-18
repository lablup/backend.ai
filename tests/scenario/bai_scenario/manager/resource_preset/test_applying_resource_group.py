"""프리셋을 자원 그룹에 묶기 — 프리셋과 그 스코프 양쪽의 권한을 본다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_preset import (
    APresetAGroupAndACaller,
    APresetAndAGroupAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ApplyingStep = Scenario[
    TestSeedingSession, APresetAGroupAndACaller, ResourcePresetAdapter, ResourcePresetData
]


@dataclass(frozen=True)
class ApplyingTheGroup(When[APresetAGroupAndACaller, ResourcePresetAdapter, ResourcePresetData]):
    """미리 만들어 둔 프리셋을 미리 만들어 둔 자원 그룹에 묶는다."""

    @override
    def operation(self) -> str:
        return "apply_resource_group"

    @override
    def describe(self, laid: APresetAGroupAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {laid.preset.name}을 자원 그룹 "
            f"{laid.group.name}에 묶습니다",
            english=(
                f"{laid.caller.username} binds the preset {laid.preset.name} to the resource "
                f"group {laid.group.name}"
            ),
        )

    @override
    async def call(
        self, adapter: ResourcePresetAdapter, laid: APresetAGroupAndACaller
    ) -> ResourcePresetData:
        with ActingAs(laid.caller):
            return await adapter.apply_resource_group(
                ResourcePresetID(laid.preset.id), laid.group.name
            )


@dataclass(frozen=True)
class ThePresetInThatGroup(Then[APresetAGroupAndACaller, ResourcePresetData]):
    """그 그룹 이름을 가진 프리셋이 온다. 나머지 값은 그대로다."""

    @override
    def says(self) -> str:
        return Says(
            "그 그룹 이름을 가진 프리셋이 응답으로 오고, 나머지 값은 그대로입니다",
            english=(
                "the preset comes back naming that resource group, and the rest stays as it was"
            ),
        )

    @override
    def look(
        self, laid: APresetAGroupAndACaller, answered: Answered[ResourcePresetData]
    ) -> list[Verdict]:
        data = answered.response
        if data is None:
            return [MissingResponse(answered.raised)]
        return [
            Held[UUID](
                "id",
                data.id,
                SameAs(
                    laid.preset.id,
                    Says(
                        "미리 저장한 프리셋의 id", english="the id of the preset seeded in advance"
                    ),
                ),
            ),
            Same("name", data.name, laid.preset.name),
            Same("resource_slots", data.resource_slots, laid.preset.resource_slots),
            Same("shared_memory", data.shared_memory, laid.preset.shared_memory),
            Same("resource_group_name", data.resource_group_name, laid.group.name),
        ]


@dataclass(frozen=True)
class AUserGrantedUpdateBindsAPreset(
    Scenario[TestSeedingSession, APresetAGroupAndACaller, ResourcePresetAdapter, ResourcePresetData]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-binds-a-preset-to-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 프리셋과 public 스코프 자체를 고칠 수 있는 사용자가 프리셋을 자원 그룹에 "
            "묶으면, 그 그룹 이름을 가진 프리셋이 반환되고 나머지 값은 그대로입니다",
            english=(
                "when a user who can update presets and the public scope itself in public binds a "
                "preset to a resource group, the preset comes back naming that group and the rest "
                "stays as it was"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAGroupAndACaller]:
        return APresetAndAGroupAndSomeone(
            granted=Permission.UPDATE, scope_permission=Permission.UPDATE
        )

    @override
    def when(self) -> When[APresetAGroupAndACaller, ResourcePresetAdapter, ResourcePresetData]:
        return ApplyingTheGroup()

    @override
    def then(self) -> Then[APresetAGroupAndACaller, ResourcePresetData]:
        return ThePresetInThatGroup()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotBind(
    Scenario[TestSeedingSession, APresetAGroupAndACaller, ResourcePresetAdapter, ResourcePresetData]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-bind-a-preset-to-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋을 자원 그룹에 묶으려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "a user granted nothing binding a preset to a resource group is rejected for not "
                "enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAGroupAndACaller]:
        return APresetAndAGroupAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[APresetAGroupAndACaller, ResourcePresetAdapter, ResourcePresetData]:
        return ApplyingTheGroup()

    @override
    def then(self) -> Then[APresetAGroupAndACaller, ResourcePresetData]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[ApplyingStep] = [
    AUserGrantedUpdateBindsAPreset(),
    AUserGrantedNothingMayNotBind(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_applying_resource_group(
    scenario: ApplyingStep, adapter: ResourcePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
