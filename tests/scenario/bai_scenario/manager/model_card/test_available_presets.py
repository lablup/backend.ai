"""카드에 쓸 수 있는 프리셋 조회 — 그 카드에 부여된 읽기 권한을 검사한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ModelCardNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.model_card import (
    ACardAndACaller,
    ACardAndSomeone,
    TheFittingPresets,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchDeploymentRevisionPresetsPayload
type PresetsStep = Scenario[SeedingSession, ACardAndACaller, ModelCardAdapter, Searched]


@dataclass(frozen=True)
class AskingWhichPresetsFit(When[ACardAndACaller, ModelCardAdapter, Searched]):
    """카드에 쓸 수 있는 프리셋을 묻는다. id를 지정하지 않으면 심은 카드의 id를 쓴다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "available_presets"

    @override
    def describe(self, laid: ACardAndACaller) -> str:
        called = "존재하지 않는 id" if self.other is not None else laid.card.name
        return f"{laid.caller.username}이 {called}에 쓸 수 있는 프리셋 조회"

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ACardAndACaller) -> Searched:
        wanted = self.other if self.other is not None else laid.card.id
        with ActingAs(laid.caller):
            return await adapter.available_presets(wanted, SearchDeploymentRevisionPresetsInput())


@dataclass(frozen=True)
class ACardReaderSeesWhatFits(
    Scenario[SeedingSession, ACardAndACaller, ModelCardAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-card-sees-the-presets-that-fit-it"

    @override
    def describe(self) -> str:
        return (
            "카드 읽기 권한을 받은 사용자가 그 카드에 쓸 수 있는 프리셋을 물으면, "
            "카드의 요구 자원을 모두 채우는 프리셋만 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACardAndACaller]:
        return ACardAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ACardAndACaller, ModelCardAdapter, Searched]:
        return AskingWhichPresetsFit()

    @override
    def then(self) -> Then[ACardAndACaller, Searched]:
        return TheFittingPresets()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefused(
    Scenario[SeedingSession, ACardAndACaller, ModelCardAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-ask-which-presets-fit-the-card"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 카드에 쓸 수 있는 프리셋을 물으면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACardAndACaller]:
        return ACardAndSomeone()

    @override
    def when(self) -> When[ACardAndACaller, ModelCardAdapter, Searched]:
        return AskingWhichPresetsFit()

    @override
    def then(self) -> Then[ACardAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsRefusedAsPermission(
    Scenario[SeedingSession, ACardAndACaller, ModelCardAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"

    @override
    def describe(self) -> str:
        return (
            "카드 읽기 권한을 받은 사용자가 존재하지 않는 id로 물으면, 대상 없음이 아니라 "
            "권한 부족으로 거부된다. 없는 행에는 부여된 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACardAndACaller]:
        return ACardAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ACardAndACaller, ModelCardAdapter, Searched]:
        return AskingWhichPresetsFit(other=uuid4())

    @override
    def then(self) -> Then[ACardAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, ACardAndACaller, ModelCardAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 id로 물으면, 대상을 찾을 수 없다는 이유로 거부된다. "
            "권한 검사를 통과하는 사용자만 이 응답을 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACardAndACaller]:
        return ACardAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACardAndACaller, ModelCardAdapter, Searched]:
        return AskingWhichPresetsFit(other=uuid4())

    @override
    def then(self) -> Then[ACardAndACaller, Searched]:
        return TheCallIsRefused(ModelCardNotFound)


@pytest.mark.parametrize(
    "scenario",
    [
        ACardReaderSeesWhatFits(),
        AUserGrantedNothingIsRefused(),
        AnUnknownIdIsRefusedAsPermission(),
        AnUnknownIdIsNotFoundForASuperadmin(),
    ],
    ids=lambda scenario: scenario.summary(),
)
async def test_available_presets(
    scenario: PresetsStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
