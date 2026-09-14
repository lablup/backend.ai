"""세션 조회, 그리고 누가 물을 수 있는가.

세션을 대기열에 넣는 행은 아직 없다. 컨트롤러도 배선되어 있고, 리소스 그룹은 도메인에
걸려 있고, 이미지와 프로젝트도 있고, 훅도 아무에게도 가지 않는다. 막히는 자리는 그 그룹이
어떤 리소스 슬롯도 제공하지 않는다는 것이고, 그러려면 에이전트가 있어야 한다. 에이전트는
write spec이 아예 없다 — 하트비트로 스스로 등록하므로 다른 행처럼 심을 수 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.domain import ADomainAndACaller, ADomainAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.common.dto.manager.v2.session.response import AdminSearchSessionsPayload
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Searched = AdminSearchSessionsPayload
type SessionStep = Scenario[SeedingSession, ADomainAndACaller, SessionAdapter, Searched]


@dataclass(frozen=True)
class SearchingEverySession(When[ADomainAndACaller, SessionAdapter, Searched]):
    """필터 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: SessionAdapter, laid: ADomainAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchSessionsInput())


@dataclass(frozen=True)
class NoSessionLaidMeansNoneFound(
    Scenario[SeedingSession, ADomainAndACaller, SessionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-scenario-that-laid-no-session-finds-none"

    @override
    def describe(self) -> str:
        return "세션을 하나도 심지 않은 상태에서 슈퍼관리자가 조회하면, 답은 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, SessionAdapter, Searched]:
        return SearchingEverySession()

    @override
    def then(self) -> Then[ADomainAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[SeedingSession, ADomainAndACaller, SessionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-sessions"

    @override
    def describe(self) -> str:
        return (
            "세션 조회는 역할이 아니라 스코프 권한이 지키므로, "
            "아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, SessionAdapter, Searched]:
        return SearchingEverySession()

    @override
    def then(self) -> Then[ADomainAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SessionStep] = [
    NoSessionLaidMeansNoneFound(),
    AUserGrantedNothingMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_session(
    scenario: SessionStep, adapter: SessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
