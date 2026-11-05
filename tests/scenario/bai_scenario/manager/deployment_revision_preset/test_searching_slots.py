"""배포 리비전 프리셋이 두는 자원 슬롯 검색하기."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

import pytest

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.request import SearchAllocatedResourceSlotsInput
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    SearchAllocatedResourceSlotsPayload,
)
from ai.backend.common.types import IntrinsicSlotNames
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Language,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.deployment_revision_preset import (
    LAID_DESCRIPTION,
    PresetsAndACaller,
    PresetsAndAnOutsider,
)
from bai_scenario.components.system import lay_a_public_reader
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.deployment.revision_preset import (
    TestSeedDeploymentRevisionPreset,
    TestSeedPresetSlotOf,
)
from bai_scenario.seeds.resource_slot.slot_type import TestSeedSlotType
from bai_scenario.seeds.runtime_variant.runtime_variant import TestSeedRuntimeVariant

type Answer = SearchAllocatedResourceSlotsPayload
type SlotStep = Scenario[
    TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer
]


@dataclass(frozen=True)
class PresetsAndSlotsAndSomeone(Given[Any, PresetsAndACaller]):
    """슬롯 유형 하나와, 그 슬롯을 두는 프리셋 하나와, 그것을 읽을 수 있는 사용자."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return Says(
            f"슬롯 유형 하나와 그 슬롯을 두는 프리셋 하나 ({LAID_DESCRIPTION}), "
            "그것을 읽을 수 있는 사용자 한 명",
            english=(
                f"one slot type and one preset declaring it ({LAID_DESCRIPTION.in_(Language.ENGLISH)}) "
                "and one user who can read it"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> PresetsAndACaller:
        await seeding.creating(TestSeedSlotType(slot=IntrinsicSlotNames.CPU))
        variant = await seeding.creating(TestSeedRuntimeVariant())
        preset = await seeding.creating_from(TestSeedDeploymentRevisionPreset(), variant)
        await seeding.adding(TestSeedPresetSlotOf(), preset)
        caller = await lay_a_public_reader(seeding, DeploymentPresetEntityType(), self.role)
        return PresetsAndACaller(
            presets=(seeding.made(preset),),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class SearchingTheSlotsOfThePreset(
    When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    """심은 프리셋 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "search_resource_slots"

    @override
    def describe(self, laid: PresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 프리셋이 두는 자원 슬롯을 훑습니다",
            english=f"{laid.caller.username} searches the resource slots the preset declares",
        )

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: PresetsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search_resource_slots(
                laid.presets[0].id, SearchAllocatedResourceSlotsInput()
            )


@dataclass(frozen=True)
class TheSlotComesBack(Then[PresetsAndACaller, Answer]):
    """프리셋이 두는 슬롯이 온다."""

    @override
    def says(self) -> str:
        return Says(
            "프리셋이 두는 슬롯이 양과 함께 옵니다",
            english="the slot the preset declares comes back with its quantity",
        )

    @override
    def look(self, laid: PresetsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        for i, node in enumerate(page.items):
            verdicts += [
                Same(f"items[{i}].slot_name", node.slot_name, "cpu"),
                Same(f"items[{i}].quantity", node.quantity, Decimal("4")),
            ]
        return verdicts


@dataclass(frozen=True)
class APresetReaderSearchesTheSlotsOfAPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-preset-reader-searches-the-slots-of-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 조회 권한을 받은 사용자가 프리셋이 두는 자원 슬롯을 훑으면, 그 슬롯이 옵니다",
            english=(
                "when a user granted preset read searches the resource slots the preset "
                "declares, that slot comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSlotsAndSomeone()

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return SearchingTheSlotsOfThePreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return TheSlotComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingSearchesNoSlots(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-searches-no-slots"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋이 두는 자원 슬롯을 훑으려 하면, 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to search the resource slots the preset "
                "declares, the search is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndAnOutsider()

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return SearchingTheSlotsOfThePreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SlotStep] = [
    APresetReaderSearchesTheSlotsOfAPreset(),
    AUserGrantedNothingSearchesNoSlots(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_slots(
    scenario: SlotStep,
    adapter: DeploymentRevisionPresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
