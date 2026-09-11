"""프리셋 조회 — 인증만 확인한다.

조회는 권한을 검사하지 않으므로, 존재하지 않는 id는 누구에게나 대상 없음이다. 권한 검사가 있는
실행과 수정의 없는 id와 다르다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    APresetAlone,
    APresetAndACaller,
    APresetAndNobody,
    APresetAndSomeone,
    PresetNodeAnswer,
    ThePresetNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer
]
type NobodyStep = Scenario[
    SeedingSession, APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer
]


@dataclass(frozen=True)
class ReadingById(When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]):
    """id로 조회한다. id를 지정하지 않으면 미리 만들어 둔 프리셋의 id를 쓴다."""

    named: UUID | None = None

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        called = "존재하지 않는 id" if self.named is not None else laid.preset.name
        return f"{laid.caller.username}이 {called}(으)로 조회"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: APresetAndACaller
    ) -> PresetNodeAnswer:
        wanted = self.named if self.named is not None else laid.preset.id
        with ActingAs(laid.caller):
            payload = await adapter.get(wanted)
        return payload.item


@dataclass(frozen=True)
class ReadingAsNobody(When[APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer]):
    """사용자 컨텍스트 없이 id로 조회한다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: APresetAlone) -> str:
        return f"사용자 컨텍스트 없이 {laid.preset.name} 조회"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: APresetAlone
    ) -> PresetNodeAnswer:
        payload = await adapter.get(laid.preset.id)
        return payload.item


@dataclass(frozen=True)
class AUserGrantedNothingReadsIt(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-preset-by-id"

    @override
    def describe(self) -> str:
        return (
            "프리셋 하나가 있고 아무 권한도 없는 사용자가 id로 조회하면, 그 프리셋 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingById()

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started)


@dataclass(frozen=True)
class AnUnknownIdIsNotFound(
    Scenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
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
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingById(named=uuid4())

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class NobodyMayNotRead(
    Scenario[SeedingSession, APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-read-a-preset"

    @override
    def describe(self) -> str:
        return "프리셋 하나가 있고 사용자 컨텍스트 없이 id로 조회하면, 인증 실패로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAlone]:
        return APresetAndNobody()

    @override
    def when(self) -> When[APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingAsNobody()

    @override
    def then(self) -> Then[APresetAlone, PresetNodeAnswer]:
        return TheCallIsRefused(UserNotFound)


SCENARIOS: list[ReadingStep] = [
    AUserGrantedNothingReadsIt(started=datetime.now(UTC)),
    AnUnknownIdIsNotFound(),
]

NOBODY_SCENARIOS: list[NobodyStep] = [NobodyMayNotRead()]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", NOBODY_SCENARIOS, ids=lambda s: s.summary())
async def test_reading_as_nobody(
    scenario: NobodyStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
