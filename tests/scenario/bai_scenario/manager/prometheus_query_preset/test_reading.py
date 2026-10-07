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

from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import TestGiven, TestScenario, TestThen, TestWhen
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

type ReadingStep = TestScenario[
    SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer
]
type NobodyStep = TestScenario[
    SeedingSession, APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer
]


@dataclass(frozen=True)
class ReadingById(TestWhen[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]):
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
class ReadingAsNobody(TestWhen[APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer]):
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
    TestScenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
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
    def given(self) -> TestGiven[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> TestWhen[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingById()

    @override
    def then(self) -> TestThen[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started)


@dataclass(frozen=True)
class AnUnknownIdIsNotFound(
    TestScenario[SeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return (
            "public 에서 읽을 수 있는 사용자가 존재하지 않는 id로 조회하면 거부된다. 권한을 "
            "물을 대상이 없으므로, 없는 것인지 닿지 못하는 것인지는 응답으로 드러나지 않는다"
        )

    @override
    def given(self) -> TestGiven[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> TestWhen[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingById(named=uuid4())

    @override
    def then(self) -> TestThen[APresetAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class NobodyMayNotRead(
    TestScenario[SeedingSession, APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-read-a-preset"

    @override
    def describe(self) -> str:
        return "프리셋 하나가 있고 사용자 컨텍스트 없이 id로 조회하면, 호출자를 알 수 없어 거부된다"

    @override
    def given(self) -> TestGiven[SeedingSession, APresetAlone]:
        return APresetAndNobody()

    @override
    def when(self) -> TestWhen[APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingAsNobody()

    @override
    def then(self) -> TestThen[APresetAlone, PresetNodeAnswer]:
        return TheCallIsRefused(UnreachableError)


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
