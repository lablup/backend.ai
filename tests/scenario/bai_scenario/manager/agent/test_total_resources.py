"""클러스터 전체 자원 합 — 관리자 경로라 superadmin 만 지나간다."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.agent import (
    AgentsAndACaller,
    AgentsAndSomeone,
    TheTotalResources,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type TotalStep = Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, TotalResourceData]


@dataclass(frozen=True)
class ReadingTheTotal(When[AgentsAndACaller, AgentAdapter, TotalResourceData]):
    @override
    def operation(self) -> str:
        return "get_total_resources"

    @override
    def describe(self, laid: AgentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 클러스터 전체 자원 합을 조회합니다",
            english=f"{laid.caller.username} reads the cluster-wide total resources",
        )

    @override
    async def call(
        self, adapter: AgentAdapter, laid: AgentsAndACaller
    ) -> TotalResourceData:
        with ActingAs(laid.caller):
            return await adapter.get_total_resources()


@dataclass(frozen=True)
class TheSuperadminReadsTheTotal(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, TotalResourceData]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-total-of-the-slots-the-agents-report"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 전체 자원 합을 조회하면 살아 있는 에이전트가 보고한 슬롯의 용량과 "
            "사용량의 합이 옵니다",
            english=(
                "when the superadmin reads the total, the sum of the capacity and usage the "
                "live agents report comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return AgentsAndSomeone(
            readable=2,
            slots=((Decimal(10), Decimal(1)),),
            role=UserRole.SUPERADMIN,
        )

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, TotalResourceData]:
        return ReadingTheTotal()

    @override
    def then(self) -> Then[AgentsAndACaller, TotalResourceData]:
        return TheTotalResources()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheTotal(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, TotalResourceData]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-total"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 만 부를 수 있는 조회라, 아무 권한도 없는 일반 사용자가 부르면 권한 "
            "부족으로 거부됩니다",
            english=(
                "the read is open to the superadmin alone, so a regular user holding no "
                "permission is rejected for lack of privilege"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return AgentsAndSomeone(readable=1)

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, TotalResourceData]:
        return ReadingTheTotal()

    @override
    def then(self) -> Then[AgentsAndACaller, TotalResourceData]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[TotalStep] = [
    TheSuperadminReadsTheTotal(),
    AUserGrantedNothingMayNotReadTheTotal(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_total_resources(
    scenario: TotalStep, adapter: AgentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
