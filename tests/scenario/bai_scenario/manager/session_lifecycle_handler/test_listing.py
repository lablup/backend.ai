"""세션 처리기 목록 조회 — 코디네이터에 등록된 처리기를 그대로 돌려준다."""

from __future__ import annotations

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
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.terminate_sessions import (
    TerminateSessionsLifecycleHandler,
)
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
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
class TheTerminatorIsRegistered(Given[TestSeedingSession, None]):
    """adapter가 받는 처리기는 conftest가 세션 종료 처리기 하나로 정한다. 심을 행은 없다."""

    @override
    def describe(self) -> str:
        return Says(
            "코디네이터가 세션 종료 처리기를 등록했습니다",
            english="the coordinator has registered a session terminator handler",
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> None:
        return None


@dataclass(frozen=True)
class NothingIsRegistered(Given[TestSeedingSession, None]):
    """adapter가 받는 처리기는 conftest가 비워 둔다. 심을 행은 없다."""

    @override
    def describe(self) -> str:
        return Says(
            "코디네이터가 등록한 처리기가 없습니다",
            english="the coordinator has registered no handler",
        )

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
        return Says(
            "세션 처리기 목록을 조회합니다",
            english="lists the session handlers",
        )

    @override
    async def call(
        self, adapter: SessionLifecycleHandlerAdapter, laid: None
    ) -> list[SessionLifecycleHandlerNode]:
        payload = await adapter.list_session_lifecycle_handlers()
        return payload.items


@dataclass(frozen=True)
class TheTerminatorIsListed(Then[None, list[SessionLifecycleHandlerNode]]):
    @override
    def says(self) -> str:
        return Says(
            "세션 종료 처리기 하나가 그 이름과 설명으로 반환됩니다",
            english="one session terminator handler comes back with its name and description",
        )

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
                        name=TerminateSessionsLifecycleHandler.name(),
                        description=TerminateSessionsLifecycleHandler.description(),
                    )
                ],
            )
        ]


@dataclass(frozen=True)
class NothingIsListed(Then[None, list[SessionLifecycleHandlerNode]]):
    @override
    def says(self) -> str:
        return Says("빈 목록이 반환됩니다", english="an empty list comes back")

    @override
    def look(
        self, laid: None, answered: Answered[list[SessionLifecycleHandlerNode]]
    ) -> list[Verdict]:
        if answered.response is None:
            return [MissingResponse(answered.raised)]
        return [Same("items", answered.response, [])]


@dataclass(frozen=True)
class TheRegisteredHandlerIsListed(
    Scenario[
        TestSeedingSession, None, SessionLifecycleHandlerAdapter, list[SessionLifecycleHandlerNode]
    ]
):
    @override
    def summary(self) -> str:
        return "the-registered-handler-is-listed"

    @override
    def describe(self) -> str:
        return Says(
            "코디네이터가 등록한 처리기가 그 이름과 설명으로 반환됩니다",
            english=(
                "the handler the coordinator registered comes back with its name and description"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, None]:
        return TheTerminatorIsRegistered()

    @override
    def when(
        self,
    ) -> When[None, SessionLifecycleHandlerAdapter, list[SessionLifecycleHandlerNode]]:
        return Listing()

    @override
    def then(self) -> Then[None, list[SessionLifecycleHandlerNode]]:
        return TheTerminatorIsListed()


@dataclass(frozen=True)
class NoRegisteredHandlerListsNothing(
    Scenario[
        TestSeedingSession, None, SessionLifecycleHandlerAdapter, list[SessionLifecycleHandlerNode]
    ]
):
    @override
    def summary(self) -> str:
        return "no-registered-handler-lists-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "코디네이터가 등록한 처리기가 없으면 빈 목록이 반환됩니다",
            english="when the coordinator has registered no handler, an empty list comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, None]:
        return NothingIsRegistered()

    @override
    def when(
        self,
    ) -> When[None, SessionLifecycleHandlerAdapter, list[SessionLifecycleHandlerNode]]:
        return Listing()

    @override
    def then(self) -> Then[None, list[SessionLifecycleHandlerNode]]:
        return NothingIsListed()


@pytest.mark.parametrize(
    "scenario",
    [TheRegisteredHandlerIsListed()],
    ids=lambda scenario: scenario.summary(),
)
async def test_listing(
    scenario: ListingStep,
    adapter: SessionLifecycleHandlerAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize(
    "scenario",
    [NoRegisteredHandlerListsNothing()],
    ids=lambda scenario: scenario.summary(),
)
async def test_listing_with_no_handler_registered(
    scenario: ListingStep,
    adapter_with_no_handler_registered: SessionLifecycleHandlerAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter_with_no_handler_registered, engine)
