"""세션 그룹 전체 검색 — 슈퍼관리자에게만, 배포의 replica group이 가진 세션 그룹까지."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.session_group.request import (
    AdminSearchSessionGroupsInput,
    SessionGroupFilter,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    AdminSearchSessionGroupsPayload,
)
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.session_group import (
    GrantedIn,
    SessionGroupsAndACaller,
    SessionGroupsInTwoProjects,
    TheseGroups,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = SessionGroupsAndACaller
type Searched = AdminSearchSessionGroupsPayload
type SearchingStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, Searched]


@dataclass(frozen=True)
class SearchingTheProject(When[Laid, SessionGroupAdapter, Searched]):
    """세션 그룹들이 있는 프로젝트로 걸러 전체 검색한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 {laid.project.name} 프로젝트로 걸러 전체 검색"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchSessionGroupsInput(
                    filter=SessionGroupFilter(project_id=UUIDFilter(equals=laid.project.id))
                )
            )


@dataclass(frozen=True)
class BothGroupsOfTheProject(Then[Laid, Searched]):
    """그 프로젝트의 사용자가 만든 세션 그룹과 배포의 replica group이 가진 세션 그룹이 모두 온다."""

    @override
    def says(self) -> str:
        return "그 프로젝트의 사용자가 만든 세션 그룹과 배포의 replica group이 가진 세션 그룹이 모두 온다"

    @override
    def look(self, laid: Laid, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "items",
                [one.entity_id for one in payload.items],
                TheseGroups(
                    frozenset({laid.users_group.id, laid.deployment_group.id}),
                    "사용자가 만든 세션 그룹과 배포의 replica group이 가진 세션 그룹",
                ),
            ),
            Same("total_count", payload.total_count, 2),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheSuperadminFindsBothGroups(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-finds-a-users-group-and-a-deployments-group"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 슈퍼관리자가 한 프로젝트로 걸러 전체 검색하면, 그 프로젝트의 "
            "사용자가 만든 세션 그룹과 배포의 replica group이 가진 세션 그룹이 모두 온다. 이 문은 역할이라 행위자가 "
            "슈퍼관리자다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return BothGroupsOfTheProject()


@dataclass(frozen=True)
class AGrantedUserMayNotSearchEverything(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-a-superadmin-may-not-search-every-session-group"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에서 세션 그룹 읽기 권한을 받았어도 슈퍼관리자가 아닌 사용자가 전체 "
            "검색하면, 역할로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminFindsBothGroups(),
    AGrantedUserMayNotSearchEverything(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: SessionGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
