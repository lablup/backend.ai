"""여러 id로 읽기 — 훑기를 id 조건으로 부르므로 문이 훑기와 같다.

인증만 보므로 거부 원소는 생기지 않는다. 없는 id만 빈 자리로 온다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest
from bai_scenario.components.prometheus_query_preset import (
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NothingIsAnswered,
    PresetNodeAnswer,
    TheBatchAnswersInOrder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Loaded = list[PresetNodeAnswer]
type LoadingStep = Scenario[
    SeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded
]


@dataclass(frozen=True)
class LoadingTheLaidAndOneUnknown(
    When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]
):
    """심은 것들의 id 뒤에 아무것도 갖지 않은 id 하나를 붙여 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 심은 정의 {len(laid.laid)}개의 id와 없는 id 하나를 한 번에 조회"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Loaded:
        ids = [one.id for one in laid.laid] + [PrometheusQueryPresetID(uuid4())]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class LoadingNothing(When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]):
    """빈 id 목록으로 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 빈 id 목록으로 조회"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class TheLaidAndTheUnknownComeBackInOrder(
    Scenario[SeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap"

    @override
    def describe(self) -> str:
        return (
            "정의 둘과 없는 id 하나를 섞어 한 번에 읽으면, 있는 둘은 노드로 없는 하나는 "
            "빈 자리로 오고 순서가 준 순서와 같다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]:
        return LoadingTheLaidAndOneUnknown()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return TheBatchAnswersInOrder()


@dataclass(frozen=True)
class AnEmptyListAnswersNothing(
    Scenario[SeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-an-empty-id-list-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return "정의가 있어도 빈 id 목록으로 읽으면, 빈 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=0)

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]:
        return LoadingNothing()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return NothingIsAnswered()


SCENARIOS: list[LoadingStep] = [TheLaidAndTheUnknownComeBackInOrder(), AnEmptyListAnswersNothing()]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_loading(
    scenario: LoadingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
