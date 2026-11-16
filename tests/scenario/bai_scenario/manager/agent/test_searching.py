"""에이전트 검색 — 관리자 경로라 superadmin 만 지나간다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.agent.request import (
    AdminSearchAgentsInput,
    AgentFilter,
    AgentOrder,
)
from ai.backend.common.dto.manager.v2.agent.response import AdminSearchAgentsPayload
from ai.backend.common.dto.manager.v2.agent.types import AgentOrderField, OrderDirection
from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.agent import (
    SUPERADMIN_PERMISSIONS,
    AgentsAndACaller,
    AgentsAndSomeone,
    TheWholeAgentPage,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Found = AdminSearchAgentsPayload
type SearchStep = Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, Found]


@dataclass(frozen=True)
class SearchingAgents(When[AgentsAndACaller, AgentAdapter, Found]):
    """미리 등록한 에이전트 하나만 남기는 조건과 순서를 걸어 한 건씩 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: AgentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 에이전트 {laid.agents[0].agent_id} 하나만 남기는 조건과 "
            "id 오름차순을 걸어 한 건씩 검색합니다",
            english=(
                f"{laid.caller.username} searches the agents with a condition that keeps "
                f"{laid.agents[0].agent_id} and orders by id ascending, one item per page"
            ),
        )

    @override
    async def call(self, adapter: AgentAdapter, laid: AgentsAndACaller) -> Found:
        given = AdminSearchAgentsInput(
            filter=AgentFilter(id=StringFilter(equals=laid.agents[0].agent_id)),
            order=[AgentOrder(field=AgentOrderField.ID, direction=OrderDirection.ASC)],
            limit=1,
        )
        with ActingAs(laid.caller):
            return await adapter.admin_search(given)


@dataclass(frozen=True)
class SearchRow(Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, Found]):
    named: str
    guarantees: str
    situation: AgentsAndSomeone
    started: datetime
    picked: tuple[int, ...]

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return self.situation

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, Found]:
        return SearchingAgents()

    @override
    def then(self) -> Then[AgentsAndACaller, Found]:
        return TheWholeAgentPage(
            started=self.started, picked=self.picked, permissions=SUPERADMIN_PERMISSIONS
        )


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, Found]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-the-agents"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 만 부를 수 있는 검색이라, 아무 권한도 없는 일반 사용자가 부르면 "
            "권한 부족으로 거부됩니다",
            english=(
                "the search is open to the superadmin alone, so a regular user holding no "
                "permission is rejected for lack of privilege"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return AgentsAndSomeone(readable=1)

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, Found]:
        return SearchingAgents()

    @override
    def then(self) -> Then[AgentsAndACaller, Found]:
        return TheCallIsRefused(InsufficientPrivilege)


STARTED = datetime.now(UTC)
TWO_AGENTS = AgentsAndSomeone(readable=2, role=UserRole.SUPERADMIN)

SCENARIOS: list[SearchStep] = [
    SearchRow(
        named="the-superadmin-picks-an-agent-by-its-name",
        guarantees=Says(
            "superadmin 이 에이전트 하나만 남기는 조건과 순서를 걸어 검색하면 그 에이전트만 "
            "한 페이지로 옵니다",
            english=(
                "when the superadmin searches with a condition that keeps one agent and an "
                "order, only that agent comes back as one page"
            ),
        ),
        situation=TWO_AGENTS,
        started=STARTED,
        picked=(0,),
    ),
    AUserGrantedNothingMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: AgentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
