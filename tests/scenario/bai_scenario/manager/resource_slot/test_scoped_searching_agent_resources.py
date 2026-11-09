"""지정한 에이전트의 자원 검색 — 지정한 에이전트마다 권한을 검사하고, 하나라도 못 읽으면 전체를 거부한다."""

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
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.agent_resource import (
    AgentsReportingSlots,
    AnAgentAndACaller,
    AnAgentAndSomeone,
    Reported,
    ReportedSlotsAndACaller,
    TheReportedSlots,
    TwoAgentsAndACaller,
    TwoAgentsAndSomeoneReadingOne,
)
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchAgentResourcesPayload
type OneAgentStep = Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
type TwoAgentsStep = Scenario[
    TestSeedingSession, TwoAgentsAndACaller, ResourceSlotAdapter, Searched
]
type ReportedSlotsStep = Scenario[
    TestSeedingSession, ReportedSlotsAndACaller, ResourceSlotAdapter, Searched
]


@dataclass(frozen=True)
class SearchingTheAgent(When[AnAgentAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 에이전트 하나를 지정해 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search_agent_resources"

    @override
    def describe(self, laid: AnAgentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.agent.agent_id} 에이전트를 지정해 조회합니다",
            english=(f"{laid.caller.username} reads the agent {laid.agent.agent_id} by naming it"),
        )

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
        return Says(
            f"{laid.caller.username} 이 {laid.readable.agent_id}와 {laid.other.agent_id} "
            "에이전트를 함께 지정해 조회합니다",
            english=(
                f"{laid.caller.username} reads the agents {laid.readable.agent_id} and "
                f"{laid.other.agent_id} by naming both"
            ),
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
class SearchingTheReportingAgent(When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]):
    """슬롯을 보고한 에이전트 하나를 지정해 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search_agent_resources"

    @override
    def describe(self, laid: ReportedSlotsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.agents[0].agent_id} 에이전트를 지정해 조회합니다",
            english=(
                f"{laid.caller.username} reads the agent {laid.agents[0].agent_id} by naming it"
            ),
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ReportedSlotsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search_agent_resources(
                ScopedSearchAgentResourcesInput(
                    scope=AgentResourceScope(agent=[UUIDScope(value=laid.agents[0].agent_uuid)])
                )
            )


@dataclass(frozen=True)
class AUserReadingAgentsInTheGroupFindsEverySlot(
    Scenario[TestSeedingSession, ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-agents-in-the-group-finds-every-slot-the-agent-reports"

    @override
    def describe(self) -> str:
        return Says(
            "resource group 의 에이전트를 읽을 수 있는 사용자가 슬롯 둘을 보고한 에이전트를 "
            "지정해 조회하면 그 에이전트가 보고한 슬롯이 모두 반환됩니다",
            english=(
                "when a user who can read the agents of the resource group reads an agent that "
                "reports two slots by naming it, every slot the agent reports comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ReportedSlotsAndACaller]:
        return AgentsReportingSlots(agents=1, slots=2, role=UserRole.USER, granted=True)

    @override
    def when(self) -> When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheReportingAgent()

    @override
    def then(self) -> Then[ReportedSlotsAndACaller, Searched]:
        return TheReportedSlots(
            rows=(Reported(agent=0, slot=0), Reported(agent=0, slot=1)), in_order=False
        )


@dataclass(frozen=True)
class AUserReadingAgentsInTheGroupSearchesTheAgent(
    Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-agents-in-the-group-searches-the-agent-and-finds-no-slot"

    @override
    def describe(self) -> str:
        return Says(
            "resource group 의 에이전트를 읽을 수 있는 사용자가 아직 슬롯을 보고하지 않은 그 "
            "에이전트를 지정해 조회하면 응답이 비어 있습니다",
            english=(
                "when a user who can read the agents of the resource group reads that agent by "
                "naming it before it reports any slot, the answer is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(granted=True)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheAgent()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class TheSuperadminSearchesTheAgent(
    Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searches-the-agent-and-finds-no-slot"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아직 슬롯을 보고하지 않은 에이전트를 지정해 조회하면 응답이 비어 "
            "있습니다",
            english=(
                "when the superadmin reads an agent that does not report any slot yet by naming "
                "it, the answer is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheAgent()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheAgent(
    Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-an-agent-s-resources"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 에이전트를 지정해 조회하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing reads an agent by naming it, the call is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone()

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheAgent()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class OneAgentTheCallerMayNotReadRefusesTheWholeSearch(
    Scenario[TestSeedingSession, TwoAgentsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "one-agent-the-caller-may-not-read-refuses-the-whole-search"

    @override
    def describe(self) -> str:
        return Says(
            "둘 중 한 에이전트만 읽을 수 있는 사용자가 둘을 함께 지정해 조회하면 전체가 권한 "
            "부족으로 거부됩니다. 읽을 수 있는 쪽만 골라 응답하지 않습니다",
            english=(
                "when a user who can read only one of two agents names both, the whole call is "
                "rejected for lack of permission. It does not answer with only the readable one"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoAgentsAndACaller]:
        return TwoAgentsAndSomeoneReadingOne()

    @override
    def when(self) -> When[TwoAgentsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingBothAgents()

    @override
    def then(self) -> Then[TwoAgentsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneSearchTheAgent(
    Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-search-an-agent-s-resources"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 에이전트를 지정해 조회할 수 있습니다",
            english=(
                "turning permission checks off lets a user granted nothing read an agent by "
                "naming it"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentAndACaller]:
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


REPORTED_SLOTS: list[ReportedSlotsStep] = [
    AUserReadingAgentsInTheGroupFindsEverySlot(),
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


@pytest.mark.parametrize("scenario", REPORTED_SLOTS, ids=lambda s: s.summary())
async def test_scoped_searching_reported_slots(
    scenario: ReportedSlotsStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
