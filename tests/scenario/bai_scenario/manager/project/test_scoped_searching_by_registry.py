"""레지스트리 범위에서 프로젝트 search — 그 레지스트리와 relation이 있는 프로젝트만, 그 범위를 읽을 수 있는 사람에게."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
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
from bai_scenario.components.container_registry import (
    ProjectsOfARegistryAndACaller,
    ProjectsOfARegistryAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchGroupsPayload
type ProjectStep = Scenario[
    TestSeedingSession, ProjectsOfARegistryAndACaller, ProjectAdapter, Searched
]


@dataclass(frozen=True)
class SearchingInTheRegistry(When[ProjectsOfARegistryAndACaller, ProjectAdapter, Searched]):
    """그 레지스트리 범위에서 필터 없이 search 한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ProjectsOfARegistryAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 레지스트리 {laid.registry.registry_name} 범위에서 search 합니다",
            english=(
                f"{laid.caller.username} searches in the registry {laid.registry.registry_name}"
            ),
        )

    @override
    async def call(self, adapter: ProjectAdapter, laid: ProjectsOfARegistryAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchProjectsInput(
                    scope=ProjectScope(container_registry=[UUIDScope(value=laid.registry.id)])
                )
            )


@dataclass(frozen=True)
class OnlyTheRelatedProjectsAreLeft(Then[ProjectsOfARegistryAndACaller, Searched]):
    """그 레지스트리와 relation이 있는 프로젝트만 남는다."""

    @override
    def says(self) -> str:
        return Says(
            "그 레지스트리와 relation이 있는 프로젝트만 남습니다",
            english="only the projects related to the registry are left",
        )

    @override
    def look(
        self, laid: ProjectsOfARegistryAndACaller, answered: Answered[Searched]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                sorted(one.basic_info.name for one in payload.items),
                sorted(one.name for one in laid.related),
            ),
            Same("total_count", payload.total_count, len(laid.related)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class AUserReadingInTheRegistrySearches(
    Scenario[TestSeedingSession, ProjectsOfARegistryAndACaller, ProjectAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-the-registry-searches-its-projects"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리 범위에서 프로젝트 읽기 역할을 받은 사용자가 그 범위에서 search 하면, "
            "그 레지스트리와 relation이 있는 프로젝트만 응답으로 옵니다",
            english=(
                "when a user granted the project read role in a registry scope searches in that "
                "scope, only the projects related to the registry come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsOfARegistryAndACaller]:
        return ProjectsOfARegistryAndSomeone()

    @override
    def when(self) -> When[ProjectsOfARegistryAndACaller, ProjectAdapter, Searched]:
        return SearchingInTheRegistry()

    @override
    def then(self) -> Then[ProjectsOfARegistryAndACaller, Searched]:
        return OnlyTheRelatedProjectsAreLeft()


@dataclass(frozen=True)
class AUserSearchesARegistryWithNoRelation(
    Scenario[TestSeedingSession, ProjectsOfARegistryAndACaller, ProjectAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-searches-the-projects-of-a-registry-with-no-relation"

    @override
    def describe(self) -> str:
        return Says(
            "relation이 없는 레지스트리 범위에서 search 하면 빈 목록이 옵니다",
            english="searching in the scope of a registry with no relation returns an empty list",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsOfARegistryAndACaller]:
        return ProjectsOfARegistryAndSomeone(related=0)

    @override
    def when(self) -> When[ProjectsOfARegistryAndACaller, ProjectAdapter, Searched]:
        return SearchingInTheRegistry()

    @override
    def then(self) -> Then[ProjectsOfARegistryAndACaller, Searched]:
        return OnlyTheRelatedProjectsAreLeft()


@dataclass(frozen=True)
class AUserReadingOnlyRegistriesMayNotSearch(
    Scenario[TestSeedingSession, ProjectsOfARegistryAndACaller, ProjectAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-without-project-read-may-not-search-the-projects-of-a-registry"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리 범위에서 프로젝트 읽기 역할 없이 레지스트리 읽기 역할만 받은 사용자가 search 하면 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted only the registry read role, not the project read role, in a "
                "registry scope searches, the call is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectsOfARegistryAndACaller]:
        return ProjectsOfARegistryAndSomeone(entity_type=ContainerRegistryEntityType())

    @override
    def when(self) -> When[ProjectsOfARegistryAndACaller, ProjectAdapter, Searched]:
        return SearchingInTheRegistry()

    @override
    def then(self) -> Then[ProjectsOfARegistryAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[ProjectStep] = [
    AUserReadingInTheRegistrySearches(),
    AUserSearchesARegistryWithNoRelation(),
    AUserReadingOnlyRegistriesMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching_by_registry(
    scenario: ProjectStep, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
