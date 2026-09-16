"""에이전트 자원 검색 — 전역 역할을 검사한다.

에이전트가 보고한 슬롯을 미리 만들어 두는 seed가 아직 없어, 보고된 슬롯이 집계되거나 필터로
좁혀지는 시나리오는 여기 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.request import AdminSearchAgentResourcesInput
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
)
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When
from bai_scenario.components.agent_resource import AnAgentAndACaller, AnAgentAndSomeone
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchAgentResourcesPayload
type SearchingStep = Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryAgentResource(When[AnAgentAndACaller, ResourceSlotAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search_agent_resources"

    @override
    def describe(self, laid: AnAgentAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: AnAgentAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_agent_resources(AdminSearchAgentResourcesInput())


@dataclass(frozen=True)
class NoSlotReportedMeansNoneFound(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-agent-reporting-no-slot-means-none-is-found"

    @override
    def describe(self) -> str:
        return "아직 슬롯을 보고하지 않은 에이전트만 있을 때 슈퍼관리자가 필터 없이 조회하면 응답이 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AMonitorMaySearch(Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]):
    @override
    def summary(self) -> str:
        return "a-monitor-may-search-agent-resources"

    @override
    def describe(self) -> str:
        return "모니터가 필터 없이 조회하면 응답이 반환된다. 전역 역할을 검사하는 조회는 모니터도 통과한다"

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-agent-resources"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 조회하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone()

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAgentResource()

    @override
    def then(self) -> Then[AnAgentAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheRole(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, Searched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-refuses-a-user-searching-agent-resources"

    @override
    def describe(self) -> str:
        return "권한 검사를 꺼도 슈퍼관리자나 모니터가 아니면 조회할 수 없다. 전역 역할 검사는 그 설정을 읽지 않는다"

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
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


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_agent_resources(
    scenario: SearchingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
