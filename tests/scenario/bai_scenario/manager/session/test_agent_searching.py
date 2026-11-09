"""한 에이전트가 실행하는 세션과 커널 검색."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
from ai.backend.common.dto.manager.v2.kernel.response import AdminSearchKernelsPayload
from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.common.dto.manager.v2.session.response import AdminSearchSessionsPayload
from ai.backend.common.types import AgentId
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Says,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.resource_allocation import Granted
from bai_scenario.components.session_reads import (
    ASessionWithAKernelAndSomeone,
    LaidSessionAndCaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Kernels = AdminSearchKernelsPayload
type Sessions = AdminSearchSessionsPayload


@dataclass(frozen=True)
class SearchingTheKernelsOfAnAgent(When[LaidSessionAndCaller, SessionAdapter, Kernels]):
    agent: UUID = field(default_factory=uuid4)

    @override
    def operation(self) -> str:
        return "search_kernels_by_agent"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 에이전트 하나가 실행하는 커널을 조회합니다",
            english=f"{laid.caller.username} searches the kernels one agent runs",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Kernels:
        with ActingAs(laid.caller):
            return await adapter.search_kernels_by_agent(
                AgentId(str(self.agent)), AdminSearchKernelsInput()
            )


@dataclass(frozen=True)
class SearchingTheSessionsOfAnAgent(When[LaidSessionAndCaller, SessionAdapter, Sessions]):
    agent: UUID = field(default_factory=uuid4)

    @override
    def operation(self) -> str:
        return "search_sessions_by_agent"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 에이전트 하나가 실행하는 세션을 조회합니다",
            english=f"{laid.caller.username} searches the sessions one agent runs",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Sessions:
        with ActingAs(laid.caller):
            return await adapter.search_sessions_by_agent(
                AgentId(str(self.agent)), AdminSearchSessionsInput()
            )


@dataclass(frozen=True)
class SearchingTheKernelsOfAnAgentScenario(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Kernels]
):
    superadmin: bool

    @override
    def summary(self) -> str:
        who = "superadmin" if self.superadmin else "a-user-who-is-not-a-superadmin"
        return f"an-agent-that-runs-no-kernel-{who}"

    @override
    def describe(self) -> str:
        if self.superadmin:
            return Says(
                "아무 커널도 실행하지 않는 에이전트로 커널을 검색하면, 빈 답이 옵니다. 이 "
                "동작은 역할이라 요청한 사용자가 superadmin 입니다",
                english=(
                    "when the kernels are searched for an agent that runs none, the answer is "
                    "empty; a role checks this operation, so the requesting user is a superadmin"
                ),
            )
        return Says(
            "superadmin 이 아닌 사용자가 에이전트로 커널을 검색하면, 역할 부족으로 거부됩니다",
            english=(
                "when a user who is not a superadmin searches the kernels of an agent, the role "
                "rejects it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        if self.superadmin:
            return ASessionWithAKernelAndSomeone(granted=Granted.NOTHING, role=UserRole.SUPERADMIN)
        return ASessionWithAKernelAndSomeone(granted=Granted.THE_PROJECT)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Kernels]:
        return SearchingTheKernelsOfAnAgent()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Kernels]:
        if self.superadmin:
            return NothingIsFound()
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class SearchingTheSessionsOfAnAgentScenario(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Sessions]
):
    superadmin: bool

    @override
    def summary(self) -> str:
        who = "superadmin" if self.superadmin else "a-user-who-is-not-a-superadmin"
        return f"an-agent-that-runs-no-session-{who}"

    @override
    def describe(self) -> str:
        if self.superadmin:
            return Says(
                "아무 세션도 실행하지 않는 에이전트로 세션을 검색하면, 빈 답이 옵니다. 이 "
                "동작은 역할이라 요청한 사용자가 superadmin 입니다",
                english=(
                    "when the sessions are searched for an agent that runs none, the answer is "
                    "empty; a role checks this operation, so the requesting user is a superadmin"
                ),
            )
        return Says(
            "superadmin 이 아닌 사용자가 에이전트로 세션을 검색하면, 역할 부족으로 거부됩니다",
            english=(
                "when a user who is not a superadmin searches the sessions of an agent, the role "
                "rejects it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        if self.superadmin:
            return ASessionWithAKernelAndSomeone(granted=Granted.NOTHING, role=UserRole.SUPERADMIN)
        return ASessionWithAKernelAndSomeone(granted=Granted.THE_PROJECT)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Sessions]:
        return SearchingTheSessionsOfAnAgent()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Sessions]:
        if self.superadmin:
            return NothingIsFound()
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    SearchingTheKernelsOfAnAgentScenario(superadmin=True),
    SearchingTheKernelsOfAnAgentScenario(superadmin=False),
    SearchingTheSessionsOfAnAgentScenario(superadmin=True),
    SearchingTheSessionsOfAnAgentScenario(superadmin=False),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_agent_searching(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
