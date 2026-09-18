"""세션 여럿의 할당을 한 번에 읽기 — 세션마다 따로 답한다.

읽을 수 있는 세션은 할당으로, 읽을 수 없는 세션은 거부로 답하고, 그 거부는 그 세션을
기다리는 필드에서만 난다. 할당 행이 없는 세션은 빈 할당으로 답한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.v2.kernel.response import ResourceAllocationGQLDTO
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.session import (
    MineAnswersItsAllocationTheirsIsRefused,
    SessionsInTwoProjectsAndAReaderOfOne,
    TwoSessionsAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[ResourceAllocationGQLDTO | Exception]
type LoadingStep = Scenario[SeedingSession, TwoSessionsAndACaller, SessionAdapter, Loaded]


@dataclass(frozen=True)
class LoadingBothSessionsAllocations(When[TwoSessionsAndACaller, SessionAdapter, Loaded]):
    """자기 프로젝트의 세션과 다른 프로젝트의 세션의 할당을 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_resource_allocation_by_session"

    @override
    def describe(self, laid: TwoSessionsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.mine.name}(와)과 {laid.theirs.name}의 할당을 한 번에 읽음"

    @override
    async def call(self, adapter: SessionAdapter, laid: TwoSessionsAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_resource_allocation_by_session([
                SessionID(laid.mine.id),
                SessionID(laid.theirs.id),
            ])


@dataclass(frozen=True)
class TheOtherProjectsSessionIsRefusedAlone(
    Scenario[SeedingSession, TwoSessionsAndACaller, SessionAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-allocations-answers-the-own-session-and-refuses-the-others-alone"

    @override
    def describe(self) -> str:
        return (
            "첫 프로젝트 범위에서만 세션을 읽을 수 있는 사용자가 두 프로젝트의 세션 할당을 한 번에 읽으면, "
            "자기 프로젝트의 세션은 빈 할당으로, 다른 프로젝트의 세션은 권한 부족의 거부로 답하고 "
            "호출 자체는 거부되지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoSessionsAndACaller]:
        return SessionsInTwoProjectsAndAReaderOfOne()

    @override
    def when(self) -> When[TwoSessionsAndACaller, SessionAdapter, Loaded]:
        return LoadingBothSessionsAllocations()

    @override
    def then(self) -> Then[TwoSessionsAndACaller, Loaded]:
        return MineAnswersItsAllocationTheirsIsRefused()


SCENARIOS: list[LoadingStep] = [
    TheOtherProjectsSessionIsRefusedAlone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_loading(
    scenario: LoadingStep, adapter: SessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
