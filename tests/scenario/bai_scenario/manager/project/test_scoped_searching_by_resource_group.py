"""리소스 그룹 범위에서 프로젝트 search — 그 그룹을 쓸 수 있는 프로젝트만, 그 범위를 읽을 수 있는 사람에게."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.group.request import ScopedSearchProjectsInput
from ai.backend.common.dto.manager.v2.group.response import AdminSearchGroupsPayload
from ai.backend.common.dto.manager.v2.group.types import ProjectScope
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.project import ProjectsOfAGroupAndACaller, ProjectsOfAGroupAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchGroupsPayload
type ProjectStep = Scenario[
    TestSeedingSession, ProjectsOfAGroupAndACaller, ProjectAdapter, Searched
]


@dataclass(frozen=True)
class SearchingInTheGroup(When[ProjectsOfAGroupAndACaller, ProjectAdapter, Searched]):
    """그 리소스 그룹 범위에서 필터 없이 search 한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ProjectsOfAGroupAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 리소스 그룹 {laid.group.name} 범위에서 search 합니다",
            english=(f"{laid.caller.username} searches in the resource group {laid.group.name}"),
        )

    @override
    async def call(self, adapter: ProjectAdapter, laid: ProjectsOfAGroupAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchProjectsInput(
                    scope=ProjectScope(resource_group=[UUIDScope(value=laid.group.id)])
                )
            )


@dataclass(frozen=True)
class OnlyTheLinkedProjectsAreLeft(Then[ProjectsOfAGroupAndACaller, Searched]):
    """그 그룹을 쓸 수 있는 프로젝트만 남는다."""

    @override
    def says(self) -> str:
        return Says(
            "그 그룹을 쓸 수 있는 프로젝트만 남습니다",
            english="only the projects that can use the group are left",
        )

    @override
    def look(self, laid: ProjectsOfAGroupAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                sorted(one.basic_info.name for one in payload.items),
                sorted(one.name for one in laid.linked),
            ),
            Same("total_count", payload.total_count, len(laid.linked)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheSuperadminSearchesInAGroup(
    Scenario[TestSeedingSession, ProjectsOfAGroupAndACaller, ProjectAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searches-the-projects-of-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 리소스 그룹 범위에서 search 하면, "
            "그 그룹을 쓸 수 있는 프로젝트만 응답으로 옵니다",
            english=(
                "when the superadmin searches in a resource group scope, "
                "only the projects that can use the group come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsOfAGroupAndACaller]:
        return ProjectsOfAGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ProjectsOfAGroupAndACaller, ProjectAdapter, Searched]:
        return SearchingInTheGroup()

    @override
    def then(self) -> Then[ProjectsOfAGroupAndACaller, Searched]:
        return OnlyTheLinkedProjectsAreLeft()


@dataclass(frozen=True)
class AUserReadingInTheGroupSearches(
    Scenario[TestSeedingSession, ProjectsOfAGroupAndACaller, ProjectAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-the-group-searches-its-projects"

    @override
    def describe(self) -> str:
        return Says(
            "리소스 그룹 범위에서 프로젝트 읽기 역할을 받은 사용자가 그 범위에서 search 하면, "
            "superadmin 과 같은 프로젝트들이 응답으로 옵니다",
            english=(
                "when a user granted the project read role in a resource group scope "
                "searches in that scope, the same projects as the superadmin sees come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsOfAGroupAndACaller]:
        return ProjectsOfAGroupAndSomeone(reading=True)

    @override
    def when(self) -> When[ProjectsOfAGroupAndACaller, ProjectAdapter, Searched]:
        return SearchingInTheGroup()

    @override
    def then(self) -> Then[ProjectsOfAGroupAndACaller, Searched]:
        return OnlyTheLinkedProjectsAreLeft()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchInTheGroup(
    Scenario[TestSeedingSession, ProjectsOfAGroupAndACaller, ProjectAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-the-projects-of-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 리소스 그룹 범위에서 search 하면 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing searches in a resource group scope, "
                "the call is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsOfAGroupAndACaller]:
        return ProjectsOfAGroupAndSomeone()

    @override
    def when(self) -> When[ProjectsOfAGroupAndACaller, ProjectAdapter, Searched]:
        return SearchingInTheGroup()

    @override
    def then(self) -> Then[ProjectsOfAGroupAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[ProjectStep] = [
    TheSuperadminSearchesInAGroup(),
    AUserReadingInTheGroupSearches(),
    AUserGrantedNothingMayNotSearchInTheGroup(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: ProjectStep, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
