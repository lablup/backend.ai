"""지정한 에이전트의 자원 검색 — 지정한 에이전트마다 권한을 검사하고, 하나라도 못 읽으면 전체를 거부한다.

에이전트가 보고한 슬롯을 미리 만들어 두는 seed가 아직 없어, 보고된 슬롯이 집계되는 시나리오는
여기 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AgentResourceScope,
    ScopedSearchAgentResourcesInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
)
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When
from bai_scenario.components.agent_resource import (
    AnAgentAndACaller,
    AnAgentAndSomeone,
    TwoAgentsAndACaller,
    TwoAgentsAndSomeoneReadingOne,
)
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchAgentResourcesPayload
type OneAgentStep = Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
type TwoAgentsStep = Scenario[SeedingSession, TwoAgentsAndACaller, ResourceSlotAdapter, Searched]


@dataclass(frozen=True)
class SearchingTheAgent(When[AnAgentAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 에이전트 하나를 지정해 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search_agent_resources"

    @override
    def describe(self, laid: AnAgentAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.agent.agent_id} 에이전트를 지정해 조회"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: AnAgentAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search_agent_resources(
                ScopedSearchAgentResourcesInput(
                    scope=AgentResourceScope(agent=[UUIDScope(value=laid.agent.agent_uuid)])
                )
            )


@dataclass(frozen=True)
class SearchingBothAgents(When[TwoAgentsAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 에이전트 둘을 함께 지정해 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search_agent_resources"

    @override
    def describe(self, laid: TwoAgentsAndACaller) -> str:
        return (
            f"{laid.caller.username}이 {laid.readable.agent_id}와 {laid.other.agent_id} "
            "에이전트를 함께 지정해 조회"
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: TwoAgentsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search_agent_resources(
                ScopedSearchAgentResourcesInput(
                    scope=AgentResourceScope(
                        agent=[
                            UUIDScope(value=laid.readable.agent_uuid),
                            UUIDScope(value=laid.other.agent_uuid),
                        ]
                    )
                )
            )


@dataclass(frozen=True)
class AUserReadingAgentsInTheGroupSearchesTheAgent(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-agents-in-the-group-searches-the-agent-and-finds-no-slot"

    @override
    def describe(self) -> str:
        return (
            "리소스 그룹의 에이전트를 읽을 수 있는 사용자가 아직 슬롯을 보고하지 않은 그 에이전트를 "
            "지정해 조회하면 응답이 비어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(granted=True)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheAgent()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class TheSuperadminSearchesTheAgent(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searches-the-agent-and-finds-no-slot"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아직 슬롯을 보고하지 않은 에이전트를 지정해 조회하면 응답이 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheAgent()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheAgent(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-an-agent-s-resources"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 에이전트를 지정해 조회하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone()

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheAgent()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class OneAgentTheCallerMayNotReadRefusesTheWholeSearch(
    Scenario[SeedingSession, TwoAgentsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "one-agent-the-caller-may-not-read-refuses-the-whole-search"

    @override
    def describe(self) -> str:
        return (
            "둘 중 한 에이전트만 읽을 수 있는 사용자가 둘을 함께 지정해 조회하면 전체가 권한 부족으로 거부된다. "
            "읽을 수 있는 쪽만 골라 답하지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoAgentsAndACaller]:
        return TwoAgentsAndSomeoneReadingOne()

    @override
    def when(self) -> When[TwoAgentsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingBothAgents()

    @override
    def then(self) -> Then[TwoAgentsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneSearchTheAgent(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-search-an-agent-s-resources"

    @override
    def describe(self) -> str:
        return "권한 검사를 끄면 아무 권한도 없는 사용자도 에이전트를 지정해 조회할 수 있다"

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone()

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheAgent()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


ONE_AGENT: list[OneAgentStep] = [
    AUserReadingAgentsInTheGroupSearchesTheAgent(),
    TheSuperadminSearchesTheAgent(),
    AUserGrantedNothingMayNotSearchTheAgent(),
    EnforcementOffLetsAnyoneSearchTheAgent(),
]

TWO_AGENTS: list[TwoAgentsStep] = [
    OneAgentTheCallerMayNotReadRefusesTheWholeSearch(),
]


@pytest.mark.parametrize("scenario", ONE_AGENT, ids=lambda s: s.summary())
async def test_scoped_searching_one_agent(
    scenario: OneAgentStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", TWO_AGENTS, ids=lambda s: s.summary())
async def test_scoped_searching_two_agents(
    scenario: TwoAgentsStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
