"""카테고리 조회 — 인증만 확인한다. 존재하지 않는 id는 누구에게나 대상 없음이다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
    PrometheusQueryPresetCategoryAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset_category import (
    ACategoryAlone,
    ACategoryAndACaller,
    ACategoryAndNobody,
    ACategoryAndSomeone,
    CategoryNodeAnswer,
    TheCategoryNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Adapter = PrometheusQueryPresetCategoryAdapter
type ReadingStep = Scenario[TestSeedingSession, ACategoryAndACaller, Adapter, CategoryNodeAnswer]
type NobodyStep = Scenario[TestSeedingSession, ACategoryAlone, Adapter, CategoryNodeAnswer]


@dataclass(frozen=True)
class ReadingById(When[ACategoryAndACaller, Adapter, CategoryNodeAnswer]):
    """id로 조회한다. id를 지정하지 않으면 미리 만들어 둔 카테고리의 id를 쓴다."""

    named: UUID | None = None

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ACategoryAndACaller) -> str:
        if self.named is not None:
            called_ko, called_en = "존재하지 않는 id", "a missing id"
        else:
            called_ko = called_en = laid.category.name
        return Says(
            f"{laid.caller.username}이 {called_ko}(으)로 조회합니다",
            english=f"{laid.caller.username} reads a category by {called_en}",
        )

    @override
    async def call(self, adapter: Adapter, laid: ACategoryAndACaller) -> CategoryNodeAnswer:
        wanted = self.named if self.named is not None else laid.category.id
        with ActingAs(laid.caller):
            payload = await adapter.get(wanted)
        return payload.item


@dataclass(frozen=True)
class ReadingAsNobody(When[ACategoryAlone, Adapter, CategoryNodeAnswer]):
    """사용자 컨텍스트 없이 id로 조회한다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ACategoryAlone) -> str:
        return Says(
            f"사용자 컨텍스트 없이 {laid.category.name} 조회합니다",
            english=f"reads {laid.category.name} with no user context",
        )

    @override
    async def call(self, adapter: Adapter, laid: ACategoryAlone) -> CategoryNodeAnswer:
        payload = await adapter.get(laid.category.id)
        return payload.item


@dataclass(frozen=True)
class AUserGrantedNothingReadsIt(
    Scenario[TestSeedingSession, ACategoryAndACaller, Adapter, CategoryNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-category-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "카테고리 하나가 있고 아무 권한도 없는 사용자가 id 로 조회하면, "
            "그 카테고리 전체가 반환됩니다",
            english=(
                "with one category laid, when a user granted nothing reads it by id, "
                "the whole category comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone()

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, CategoryNodeAnswer]:
        return ReadingById()

    @override
    def then(self) -> Then[ACategoryAndACaller, CategoryNodeAnswer]:
        return TheCategoryNode(started=self.started)


@dataclass(frozen=True)
class AnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, ACategoryAndACaller, Adapter, CategoryNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 읽을 수 있는 사용자가 존재하지 않는 id 로 조회하면 거부됩니다. "
            "권한을 요구할 대상이 없으므로, 없는 것인지 접근하지 못하는 것인지는 응답으로 "
            "드러나지 않습니다",
            english=(
                "when a user who can read in public reads a missing id, the call is rejected. "
                "There is no target to require permission for, so the answer does not reveal "
                "whether it does not exist or cannot be accessed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone()

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, CategoryNodeAnswer]:
        return ReadingById(named=uuid4())

    @override
    def then(self) -> Then[ACategoryAndACaller, CategoryNodeAnswer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class NobodyMayNotRead(Scenario[TestSeedingSession, ACategoryAlone, Adapter, CategoryNodeAnswer]):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-read-a-category"

    @override
    def describe(self) -> str:
        return Says(
            "카테고리 하나가 있고 사용자 컨텍스트 없이 id 로 조회하면, "
            "호출자를 알 수 없어 거부됩니다",
            english=(
                "with one category laid, when it is read by id with no user context, "
                "the call is rejected because the caller is unknown"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACategoryAlone]:
        return ACategoryAndNobody()

    @override
    def when(self) -> When[ACategoryAlone, Adapter, CategoryNodeAnswer]:
        return ReadingAsNobody()

    @override
    def then(self) -> Then[ACategoryAlone, CategoryNodeAnswer]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[ReadingStep] = [
    AUserGrantedNothingReadsIt(started=datetime.now(UTC)),
    AnUnknownIdIsNotFound(),
]

NOBODY_SCENARIOS: list[NobodyStep] = [NobodyMayNotRead()]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", NOBODY_SCENARIOS, ids=lambda s: s.summary())
async def test_reading_as_nobody(
    scenario: NobodyStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
