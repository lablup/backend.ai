"""리소스 프리셋 수정 — 누가 고칠 수 있고 무엇이 바뀌는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_preset.request import UpdateResourcePresetInput
from ai.backend.common.dto.manager.v2.resource_preset.response import ResourcePresetNode
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ResourcePresetNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    ThePresetNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

RENAMED = "renamed-preset"

type EditingStep = Scenario[
    TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode
]


@dataclass(frozen=True)
class Renaming(When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]):
    """미리 만든 프리셋의 이름을 바꾼다. 답이 실은 노드를 벗겨서 준다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target_ko = "없는 id" if self.unknown else laid.preset.name
        target_en = "an unknown id" if self.unknown else laid.preset.name
        return Says(
            f"{laid.caller.username}이 {target_ko}의 이름을 변경합니다",
            english=f"{laid.caller.username} renames {target_en}",
        )

    @override
    async def call(
        self, adapter: ResourcePresetAdapter, laid: APresetAndACaller
    ) -> ResourcePresetNode:
        target = uuid4() if self.unknown else laid.preset.id
        with ActingAs(laid.caller):
            payload = await adapter.update(UpdateResourcePresetInput(id=target, name=RENAMED))
        return payload.resource_preset


@dataclass(frozen=True)
class TheSuperadminRenamesAPreset(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-renames-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 프리셋의 이름만 변경하면, 이름은 새 값이 되고 나머지는 그대로 남습니다",
            english=(
                "when the superadmin renames a preset, the name takes the new value and the "
                "rest stays as it was"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]:
        return Renaming()

    @override
    def then(self) -> Then[APresetAndACaller, ResourcePresetNode]:
        return ThePresetNode(named=RENAMED)


@dataclass(frozen=True)
class AUserGrantedUpdateRenamesAPreset(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-in-public-renames-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 수정 권한을 받은 사용자가 프리셋의 이름을 변경하면, 새 이름의 프리셋이 "
            "반환됩니다",
            english=(
                "a user granted update in public renaming a preset gets the preset under the "
                "new name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]:
        return Renaming()

    @override
    def then(self) -> Then[APresetAndACaller, ResourcePresetNode]:
        return ThePresetNode(named=RENAMED)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋을 수정하려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing trying to edit a preset is rejected for not enough "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]:
        return Renaming()

    @override
    def then(self) -> Then[APresetAndACaller, ResourcePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]
):
    @override
    def summary(self) -> str:
        return "editing-an-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 없는 id 의 프리셋을 수정하려 하면 대상이 없다는 것으로 거부됩니다",
            english=(
                "when the superadmin tries to edit the preset of an unknown id, the call is "
                "rejected as no such target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, ResourcePresetAdapter, ResourcePresetNode]:
        return Renaming(unknown=True)

    @override
    def then(self) -> Then[APresetAndACaller, ResourcePresetNode]:
        return TheCallIsRefused(ResourcePresetNotFound)


SCENARIOS: list[EditingStep] = [
    TheSuperadminRenamesAPreset(),
    AUserGrantedUpdateRenamesAPreset(),
    AUserGrantedNothingMayNotEdit(),
    AnIdNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: ResourcePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
