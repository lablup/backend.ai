"""카테고리 조회 — 인증만 확인한다. 존재하지 않는 id는 누구에게나 대상 없음이다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest
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
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
    PrometheusQueryPresetCategoryAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Adapter = PrometheusQueryPresetCategoryAdapter
type ReadingStep = Scenario[SeedingSession, ACategoryAndACaller, Adapter, CategoryNodeAnswer]
type NobodyStep = Scenario[SeedingSession, ACategoryAlone, Adapter, CategoryNodeAnswer]


@dataclass(frozen=True)
class ReadingById(When[ACategoryAndACaller, Adapter, CategoryNodeAnswer]):
    """id로 조회한다. id를 지정하지 않으면 미리 만들어 둔 카테고리의 id를 쓴다."""

    named: UUID | None = None

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ACategoryAndACaller) -> str:
        called = "존재하지 않는 id" if self.named is not None else laid.category.name
        return f"{laid.caller.username}이 {called}(으)로 조회"

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
        return f"사용자 컨텍스트 없이 {laid.category.name} 조회"

    @override
    async def call(self, adapter: Adapter, laid: ACategoryAlone) -> CategoryNodeAnswer:
        payload = await adapter.get(laid.category.id)
        return payload.item


@dataclass(frozen=True)
class AUserGrantedNothingReadsIt(
    Scenario[SeedingSession, ACategoryAndACaller, Adapter, CategoryNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-category-by-id"

    @override
    def describe(self) -> str:
        return "카테고리 하나가 있고 아무 권한도 없는 사용자가 id로 조회하면, 그 카테고리 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone()

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, CategoryNodeAnswer]:
        return ReadingById()

    @override
    def then(self) -> Then[ACategoryAndACaller, CategoryNodeAnswer]:
        return TheCategoryNode(started=self.started)


@dataclass(frozen=True)
class AnUnknownIdIsNotFound(
    Scenario[SeedingSession, ACategoryAndACaller, Adapter, CategoryNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-anyone"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 id로 조회하면, 대상을 찾을 수 없다는 "
            "이유로 거부된다. 조회는 인증만 확인하므로 권한 검사가 먼저 막지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone()

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, CategoryNodeAnswer]:
        return ReadingById(named=uuid4())

    @override
    def then(self) -> Then[ACategoryAndACaller, CategoryNodeAnswer]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class NobodyMayNotRead(Scenario[SeedingSession, ACategoryAlone, Adapter, CategoryNodeAnswer]):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-read-a-category"

    @override
    def describe(self) -> str:
        return "카테고리 하나가 있고 사용자 컨텍스트 없이 id로 조회하면, 인증 실패로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACategoryAlone]:
        return ACategoryAndNobody()

    @override
    def when(self) -> When[ACategoryAlone, Adapter, CategoryNodeAnswer]:
        return ReadingAsNobody()

    @override
    def then(self) -> Then[ACategoryAlone, CategoryNodeAnswer]:
        return TheCallIsRefused(UserNotFound)


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
