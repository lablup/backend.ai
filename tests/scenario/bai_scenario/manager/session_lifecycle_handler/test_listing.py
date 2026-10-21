"""세션 처리기 목록 조회 — 스케줄러가 시작할 때 만드는 처리기를 전부 돌려준다."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.session_lifecycle_handler.response import (
    SessionLifecycleHandlerNode,
)
from ai.backend.manager.api.adapters.session_lifecycle_handler.adapter import (
    SessionLifecycleHandlerAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.scheduler.factory import SESSION_LIFECYCLE_HANDLER_TYPES
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ListingStep = Scenario[
    TestSeedingSession, None, SessionLifecycleHandlerAdapter, list[SessionLifecycleHandlerNode]
]


@dataclass(frozen=True)
class TheSchedulerHandlersAreFixed(Given[TestSeedingSession, None]):
    """처리기 목록은 코드에 정해져 있어 심을 행이 없다."""

    @override
    def describe(self) -> str:
        return "스케줄러가 시작할 때 만드는 세션 처리기가 정해져 있다"

    @override
    async def lay(self, seeding: TestSeedingSession) -> None:
        return None


@dataclass(frozen=True)
class Listing(When[None, SessionLifecycleHandlerAdapter, list[SessionLifecycleHandlerNode]]):
    @override
    def operation(self) -> str:
        return "list_session_lifecycle_handlers"

    @override
    def describe(self, laid: None) -> str:
        return "세션 처리기 목록을 조회"

    @override
    async def call(
        self, adapter: SessionLifecycleHandlerAdapter, laid: None
    ) -> list[SessionLifecycleHandlerNode]:
        payload = await adapter.list_session_lifecycle_handlers()
        return payload.items


@dataclass(frozen=True)
class EveryHandlerIsListed(Then[None, list[SessionLifecycleHandlerNode]]):
    @override
    def says(self) -> str:
        return "처리기 전부가 각자의 이름과 클래스 설명의 첫 줄로 반환된다"

    @override
    def look(
        self, laid: None, answered: Answered[list[SessionLifecycleHandlerNode]]
    ) -> list[Verdict]:
        if answered.response is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                answered.response,
                [
                    SessionLifecycleHandlerNode(
                        name=handler_type.name(),
                        description=inspect.cleandoc(handler_type.__doc__ or "").partition("\n")[0],
                    )
                    for handler_type in SESSION_LIFECYCLE_HANDLER_TYPES
                ],
            )
        ]


@dataclass(frozen=True)
class EverySchedulerHandlerIsListed(
    Scenario[
        TestSeedingSession, None, SessionLifecycleHandlerAdapter, list[SessionLifecycleHandlerNode]
    ]
):
    @override
    def summary(self) -> str:
        return "every-scheduler-handler-is-listed"

    @override
    def describe(self) -> str:
        return "스케줄러가 만드는 세션 처리기 전부가 각자의 이름과 클래스 설명의 첫 줄로 반환된다"

    @override
    def given(self) -> Given[TestSeedingSession, None]:
        return TheSchedulerHandlersAreFixed()

    @override
    def when(
        self,
    ) -> When[None, SessionLifecycleHandlerAdapter, list[SessionLifecycleHandlerNode]]:
        return Listing()

    @override
    def then(self) -> Then[None, list[SessionLifecycleHandlerNode]]:
        return EveryHandlerIsListed()


@pytest.mark.parametrize(
    "scenario",
    [EverySchedulerHandlerIsListed()],
    ids=lambda scenario: scenario.summary(),
)
async def test_listing(
    scenario: ListingStep,
    adapter: SessionLifecycleHandlerAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
