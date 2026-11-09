"""에이전트 자원 검색 — 슈퍼관리자인지 검사하고, 필터와 크기에 따라 보고된 슬롯을 반환한다.

정렬을 지정하지 않으면 슬롯 이름 순서로 반환한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AgentResourceFilter,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
)
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.agent_resource import (
    AgentsReportingSlots,
    AnAgentAndACaller,
    AnAgentAndSomeone,
    Reported,
    ReportedSlotsAndACaller,
    TheFirstReportedSlots,
    TheReportedSlots,
)
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

DEFAULT_PAGE = 10

type Searched = AdminSearchAgentResourcesPayload
type SearchingStep = Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
type SearchingReportedStep = Scenario[
    TestSeedingSession, ReportedSlotsAndACaller, ResourceSlotAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryAgentResource(
    When[AnAgentAndACaller | ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]
):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search_agent_resources"

    @override
    def describe(self, laid: AnAgentAndACaller | ReportedSlotsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads everything without a filter",
        )

    @override
    async def call(
        self, adapter: ResourceSlotAdapter, laid: AnAgentAndACaller | ReportedSlotsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_agent_resources(AdminSearchAgentResourcesInput())


@dataclass(frozen=True)
class SearchingBySlotName(When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 슬롯 중 하나의 이름을 필터로 검색한다."""

    slot: int

    @override
    def operation(self) -> str:
        return "search_agent_resources"

    @override
    def describe(self, laid: ReportedSlotsAndACaller) -> str:
        name = laid.slots[self.slot].name
        return Says(
            f"{laid.caller.username} 이 {name} 슬롯 이름 필터로 조회합니다",
            english=f"{laid.caller.username} reads with the slot name filter {name}",
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ReportedSlotsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_agent_resources(
                AdminSearchAgentResourcesInput(
                    filter=AgentResourceFilter(
                        slot_name=StringFilter(equals=laid.slots[self.slot].name)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByAgent(When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 에이전트 중 하나를 필터로 검색한다."""

    agent: int

    @override
    def operation(self) -> str:
        return "search_agent_resources"

    @override
    def describe(self, laid: ReportedSlotsAndACaller) -> str:
        agent = laid.agents[self.agent].agent_id
        return Says(
            f"{laid.caller.username} 이 {agent} 에이전트 필터로 조회합니다",
            english=f"{laid.caller.username} reads with the agent filter {agent}",
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ReportedSlotsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_agent_resources(
                AdminSearchAgentResourcesInput(
                    filter=AgentResourceFilter(
                        agent_id=StringFilter(equals=laid.agents[self.agent].agent_id)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingTheFirst(When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]):
    """앞에서 몇 건만 요청한다. 크기가 아니라 커서 쪽의 개수다."""

    first: int

    @override
    def operation(self) -> str:
        return "search_agent_resources"

    @override
    def describe(self, laid: ReportedSlotsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 앞에서 {self.first}건만 요청해 조회합니다",
            english=f"{laid.caller.username} reads asking for only the first {self.first}",
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ReportedSlotsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_agent_resources(
                AdminSearchAgentResourcesInput(first=self.first)
            )


@dataclass(frozen=True)
class TheSuperadminFindsEveryReportedSlot(
    Scenario[TestSeedingSession, ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-finds-every-slot-the-agents-report"

    @override
    def describe(self) -> str:
        return Says(
            "슬롯을 보고한 에이전트 둘이 있을 때 superadmin 이 필터 없이 조회하면 보고된 슬롯이 "
            "모두 반환됩니다",
            english=(
                "when two agents report slots and the superadmin reads without a filter, every "
                "reported slot comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ReportedSlotsAndACaller]:
        return AgentsReportingSlots(agents=2, slots=1)

    @override
    def when(self) -> When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[ReportedSlotsAndACaller, Searched]:
        return TheReportedSlots(
            rows=(Reported(agent=0, slot=0), Reported(agent=1, slot=0)), in_order=False
        )


@dataclass(frozen=True)
class ASlotNameFilterNarrows(
    Scenario[TestSeedingSession, ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-slot-name-filter-narrows-the-answer-to-that-slot"

    @override
    def describe(self) -> str:
        return Says(
            "슬롯 둘을 보고한 에이전트 하나가 있을 때 한 슬롯의 이름을 필터로 조회하면, 응답에는 "
            "그 슬롯의 row 만 남습니다",
            english=(
                "when one agent reports two slots and the call reads with the name of one slot "
                "as a filter, only the row of that slot stays in the answer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ReportedSlotsAndACaller]:
        return AgentsReportingSlots(agents=1, slots=2)

    @override
    def when(self) -> When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingBySlotName(slot=1)

    @override
    def then(self) -> Then[ReportedSlotsAndACaller, Searched]:
        return TheReportedSlots(rows=(Reported(agent=0, slot=1),))


@dataclass(frozen=True)
class AnAgentFilterNarrows(
    Scenario[TestSeedingSession, ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-agent-filter-narrows-the-answer-to-that-agent-s-slots"

    @override
    def describe(self) -> str:
        return Says(
            "슬롯을 보고한 에이전트 둘이 있을 때 한 에이전트를 필터로 조회하면, 응답에는 그 "
            "에이전트의 row 만 남습니다",
            english=(
                "when two agents report slots and the call reads with one agent as a filter, "
                "only the rows of that agent stay in the answer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ReportedSlotsAndACaller]:
        return AgentsReportingSlots(agents=2, slots=1)

    @override
    def when(self) -> When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingByAgent(agent=1)

    @override
    def then(self) -> Then[ReportedSlotsAndACaller, Searched]:
        return TheReportedSlots(rows=(Reported(agent=1, slot=0),))


@dataclass(frozen=True)
class OmittingThePageSizeAnswersTheDefaultPage(
    Scenario[TestSeedingSession, ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-slots-and-a-next-page"

    @override
    def describe(self) -> str:
        return Says(
            "보고된 슬롯 11개가 있을 때 크기 없이 조회하면 슬롯 이름 순서로 앞선 10건까지 "
            "반환되고 다음 페이지가 있다고 응답합니다",
            english=(
                "when 11 slots are reported and the call reads without a size, the first 10 in "
                "slot name order come back and the answer says a next page exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ReportedSlotsAndACaller]:
        return AgentsReportingSlots(agents=1, slots=DEFAULT_PAGE + 1)

    @override
    def when(self) -> When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[ReportedSlotsAndACaller, Searched]:
        return TheFirstReportedSlots(size=DEFAULT_PAGE)


@dataclass(frozen=True)
class AskingForTheFirstAnswersOne(
    Scenario[TestSeedingSession, ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "asking-for-the-first-slot-answers-one-and-a-next-page"

    @override
    def describe(self) -> str:
        return Says(
            "보고된 슬롯 둘이 있을 때 앞에서 1건만 요청해 조회하면 슬롯 이름 순서로 앞선 한 건이 "
            "반환되고 다음 페이지가 있다고 응답합니다",
            english=(
                "when two slots are reported and the call asks for only the first one, the "
                "first one in slot name order comes back and the answer says a next page exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ReportedSlotsAndACaller]:
        return AgentsReportingSlots(agents=1, slots=2)

    @override
    def when(self) -> When[ReportedSlotsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheFirst(first=1)

    @override
    def then(self) -> Then[ReportedSlotsAndACaller, Searched]:
        return TheFirstReportedSlots(size=1)


@dataclass(frozen=True)
class NoSlotReportedMeansNoneFound(
    Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-agent-reporting-no-slot-means-none-is-found"

    @override
    def describe(self) -> str:
        return Says(
            "아직 슬롯을 보고하지 않은 에이전트만 있을 때 superadmin 이 필터 없이 조회하면 "
            "응답이 비어 있습니다",
            english=(
                "when only an agent that does not report any slot exists and the superadmin "
                "reads without a filter, the answer is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AMonitorMaySearch(
    Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-monitor-may-search-agent-resources"

    @override
    def describe(self) -> str:
        return Says(
            "모니터가 필터 없이 조회하면 응답이 반환됩니다. superadmin 인지 검사하는 조회는 "
            "모니터도 통과합니다",
            english=(
                "when a monitor reads without a filter, the answer comes back. A read that "
                "checks whether the caller is the superadmin also passes for a monitor"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-agent-resources"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 조회하면 역할 부족으로 거부됩니다",
            english=("when a user granted nothing reads, the call is rejected for lack of role"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone()

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheRole(
    Scenario[TestSeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-refuses-a-user-searching-agent-resources"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 꺼도 superadmin 이나 모니터가 아니면 조회할 수 없습니다. superadmin "
            "검사는 그 설정을 읽지 않습니다",
            english=(
                "turning permission checks off still does not let a user who is neither the "
                "superadmin nor a monitor read. The superadmin check does not read that setting"
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
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    NoSlotReportedMeansNoneFound(),
    AMonitorMaySearch(),
    AUserGrantedNothingMayNotSearch(),
    EnforcementOffStillNeedsTheRole(),
]


REPORTED: list[SearchingReportedStep] = [
    TheSuperadminFindsEveryReportedSlot(),
    ASlotNameFilterNarrows(),
    AnAgentFilterNarrows(),
    OmittingThePageSizeAnswersTheDefaultPage(),
    AskingForTheFirstAnswersOne(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_agent_resources(
    scenario: SearchingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", REPORTED, ids=lambda s: s.summary())
async def test_searching_reported_slots(
    scenario: SearchingReportedStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
