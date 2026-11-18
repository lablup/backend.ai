"""배포 처리기 목록 조회 — 코디네이터에 등록된 처리기를 그대로 돌려준다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.scheduling_handler.types import (
    SchedulingHandlerCategory,
    SchedulingHandlerNode,
)
from ai.backend.manager.api.adapters.scheduling_handler.adapter import SchedulingHandlerAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.deployment.handlers.deploying_initializing import (
    DeployingInitializingHandler,
)
from ai.backend.manager.sokovan.deployment.handlers.replica import CheckReplicaDeploymentHandler
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
    TestSeedingSession, None, SchedulingHandlerAdapter, list[SchedulingHandlerNode]
]


@dataclass(frozen=True)
class TwoHandlersAreRegistered(Given[TestSeedingSession, None]):
    """adapter가 받는 처리기는 conftest가 복제본 점검 처리기와 초기화 처리기로 정한다. 심을 행은 없다."""

    @override
    def describe(self) -> str:
        return Says(
            "코디네이터가 복제본 점검 처리기와 배포 초기화 처리기를 등록했습니다",
            english="the coordinator has registered a replica check handler and a deploying initialization handler",
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
class Listing(When[None, SchedulingHandlerAdapter, list[SchedulingHandlerNode]]):
    @override
    def operation(self) -> str:
        return "list_scheduling_handlers"

    @override
    def describe(self, laid: None) -> str:
        return Says("배포 처리기 목록을 조회합니다", english="lists the scheduling handlers")

    @override
    async def call(
        self, adapter: SchedulingHandlerAdapter, laid: None
    ) -> list[SchedulingHandlerNode]:
        payload = await adapter.list_scheduling_handlers()
        return payload.items


@dataclass(frozen=True)
class TheHandlersAreListed(Then[None, list[SchedulingHandlerNode]]):
    @override
    def says(self) -> str:
        return Says(
            "등록된 순서대로 처리기마다 이름, 분류, 설명의 첫 줄이 반환됩니다",
            english="each handler comes back in registration order with its name, category and the first line of its description",
        )

    @override
    def look(self, laid: None, answered: Answered[list[SchedulingHandlerNode]]) -> list[Verdict]:
        if answered.response is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                answered.response,
                [
                    SchedulingHandlerNode(
                        name=CheckReplicaDeploymentHandler.name(),
                        category=SchedulingHandlerCategory.SCALING,
                        description="Handler for checking and managing deployment replicas.",
                    ),
                    SchedulingHandlerNode(
                        name=DeployingInitializingHandler.name(),
                        category=SchedulingHandlerCategory.LIFECYCLE,
                        description=(
                            "DEPLOYING / INITIALIZING: register the appproxy endpoint for "
                            "deployments that entered"
                        ),
                    ),
                ],
            )
        ]


@dataclass(frozen=True)
class NothingIsListed(Then[None, list[SchedulingHandlerNode]]):
    @override
    def says(self) -> str:
        return Says("빈 목록이 반환됩니다", english="an empty list comes back")

    @override
    def look(self, laid: None, answered: Answered[list[SchedulingHandlerNode]]) -> list[Verdict]:
        if answered.response is None:
            return [MissingResponse(answered.raised)]
        return [Same("items", answered.response, [])]


@dataclass(frozen=True)
class TheRegisteredHandlersAreListed(
    Scenario[TestSeedingSession, None, SchedulingHandlerAdapter, list[SchedulingHandlerNode]]
):
    @override
    def summary(self) -> str:
        return "the-registered-handlers-are-listed"

    @override
    def describe(self) -> str:
        return Says(
            "코디네이터가 등록한 처리기가 이름, 분류, 설명으로 반환됩니다",
            english="the handlers the coordinator registered come back with name, category and description",
        )

    @override
    def given(self) -> Given[TestSeedingSession, None]:
        return TwoHandlersAreRegistered()

    @override
    def when(self) -> When[None, SchedulingHandlerAdapter, list[SchedulingHandlerNode]]:
        return Listing()

    @override
    def then(self) -> Then[None, list[SchedulingHandlerNode]]:
        return TheHandlersAreListed()


@dataclass(frozen=True)
class NoRegisteredHandlerListsNothing(
    Scenario[TestSeedingSession, None, SchedulingHandlerAdapter, list[SchedulingHandlerNode]]
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
    def when(self) -> When[None, SchedulingHandlerAdapter, list[SchedulingHandlerNode]]:
        return Listing()

    @override
    def then(self) -> Then[None, list[SchedulingHandlerNode]]:
        return NothingIsListed()


@pytest.mark.parametrize(
    "scenario",
    [TheRegisteredHandlersAreListed()],
    ids=lambda scenario: scenario.summary(),
)
async def test_listing(
    scenario: ListingStep,
    adapter: SchedulingHandlerAdapter,
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
    adapter_with_no_handler_registered: SchedulingHandlerAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter_with_no_handler_registered, engine)
