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
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[
    TestSeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer
]
type NobodyStep = Scenario[
    TestSeedingSession, APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer
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
        called_en = "an absent id" if self.named is not None else laid.preset.name
        return Says(
            f"{laid.caller.username}이 {called}(으)로 조회합니다",
            english=f"{laid.caller.username} reads by {called_en}",
        )

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
        return Says(
            f"사용자 컨텍스트 없이 {laid.preset.name} 조회합니다",
            english=f"reads {laid.preset.name} without a user context",
        )

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: APresetAlone
    ) -> PresetNodeAnswer:
        payload = await adapter.get(laid.preset.id)
        return payload.item


@dataclass(frozen=True)
class AUserGrantedNothingReadsIt(
    Scenario[TestSeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-preset-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 하나가 있고 아무 권한도 없는 사용자가 id 로 조회하면, 그 프리셋 전체가 "
            "반환됩니다",
            english=(
                "when a preset exists and a user granted nothing reads it by id, the whole "
                "preset comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingById()

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return ThePresetNode(started=self.started)


@dataclass(frozen=True)
class AnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 읽을 수 있는 사용자가 존재하지 않는 id 로 조회하면 거부됩니다. 권한을 "
            "요구할 대상이 없으므로, 없는 것인지 접근하지 못하는 것인지는 응답으로 드러나지 "
            "않습니다",
            english=(
                "when a user who can read in public reads an id that does not exist, it is "
                "rejected. Because there is no target to require permission on, the response "
                "does not reveal whether it does not exist or cannot be reached"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingById(named=uuid4())

    @override
    def then(self) -> Then[APresetAndACaller, PresetNodeAnswer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class NobodyMayNotRead(
    Scenario[TestSeedingSession, APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer]
):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-read-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 하나가 있고 사용자 컨텍스트 없이 id 로 조회하면, 호출자를 알 수 없어 "
            "거부됩니다",
            english=(
                "when a preset exists and it is read by id without a user context, it is "
                "rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAlone]:
        return APresetAndNobody()

    @override
    def when(self) -> When[APresetAlone, PrometheusQueryPresetAdapter, PresetNodeAnswer]:
        return ReadingAsNobody()

    @override
    def then(self) -> Then[APresetAlone, PresetNodeAnswer]:
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
