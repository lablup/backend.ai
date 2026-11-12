"""여러 id로 조회 — 검색을 id 조건으로 호출하므로 권한 경로가 검색과 같다.

권한이 없는 호출자는 거부된다. 없는 id만 빈 항목으로 반환된다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Says,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NothingIsAnswered,
    PresetNodeAnswer,
    TheBatchAnswersInOrder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[PresetNodeAnswer]
type LoadingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded
]


@dataclass(frozen=True)
class LoadingTheLaidAndOneUnknown(
    When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]
):
    """미리 만들어 둔 프리셋들의 id 뒤에 존재하지 않는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 프리셋 {len(laid.laid)}개의 id 와 없는 id 하나를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} reads the ids of {len(laid.laid)} presets seeded in "
                "advance and one absent id at once"
            ),
        )

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Loaded:
        ids = [one.id for one in laid.laid] + [PrometheusQueryPresetID(uuid4())]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class LoadingNothing(When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]):
    """빈 id 목록으로 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 빈 id 목록으로 조회합니다",
            english=f"{laid.caller.username} reads with an empty id list",
        )

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class TheLaidAndTheUnknownComeBackInOrder(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 둘과 없는 id 하나를 섞어 한 번에 조회하면, 있는 둘은 노드로 없는 하나는 빈 "
            "항목으로 반환되고 순서가 요청한 순서와 같습니다",
            english=(
                "when two presets and one absent id are read at once, the two present ones "
                "come back as nodes and the absent one as an empty item, in the requested "
                "order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]:
        return LoadingTheLaidAndOneUnknown()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return TheBatchAnswersInOrder()


@dataclass(frozen=True)
class AnEmptyListAnswersNothing(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-an-empty-id-list-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋이 있어도 빈 id 목록으로 조회하면, 빈 응답이 반환됩니다",
            english=("even when presets exist, reading an empty id list answers an empty response"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=0)

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]:
        return LoadingNothing()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return NothingIsAnswered()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotLoad(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-load-presets-by-ids"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 프리셋 id 를 한 번에 조회하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing reads presets by ids at once, it is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(reading_in_public=False)

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Loaded]:
        return LoadingTheLaidAndOneUnknown()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[LoadingStep] = [
    TheLaidAndTheUnknownComeBackInOrder(),
    AnEmptyListAnswersNothing(),
    AUserGrantedNothingMayNotLoad(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_loading(
    scenario: LoadingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
