"""프로젝트 범위에서 레지스트리 search — 그 프로젝트와 relation이 있는 레지스트리만, 그 범위를 읽을 수 있는 사람에게."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.dto.manager.v2.container_registry.request import (
    ScopedSearchContainerRegistriesInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    ScopedSearchContainerRegistriesPayload,
)
from ai.backend.common.dto.manager.v2.container_registry.types import ContainerRegistryScope
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
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
    RegistriesOfAProjectAndACaller,
    RegistriesOfAProjectAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = RegistriesOfAProjectAndACaller
type Searched = ScopedSearchContainerRegistriesPayload
type RegistryStep = Scenario[TestSeedingSession, Laid, ContainerRegistryAdapter, Searched]


@dataclass(frozen=True)
class SearchingInTheProject(When[Laid, ContainerRegistryAdapter, Searched]):
    """그 프로젝트 범위에서 필터 없이 search 한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username}이 프로젝트 {laid.project.name} 범위에서 search 합니다",
            english=f"{laid.caller.username} searches in the project {laid.project.name}",
        )

    @override
    async def call(self, adapter: ContainerRegistryAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchContainerRegistriesInput(
                    scope=ContainerRegistryScope(project=[UUIDScope(value=laid.project.id)])
                )
            )


@dataclass(frozen=True)
class OnlyTheRelatedRegistriesAreLeft(Then[Laid, Searched]):
    """그 프로젝트와 relation이 있는 레지스트리만 남는다."""

    @override
    def says(self) -> str:
        return Says(
            "그 프로젝트와 relation이 있는 레지스트리만 남습니다",
            english="only the registries related to the project are left",
        )

    @override
    def look(self, laid: Laid, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                sorted(one.registry_name for one in payload.items),
                sorted(one.registry_name for one in laid.related),
            ),
            Same("total_count", payload.total_count, len(laid.related)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class AUserReadingInTheProjectSearches(
    Scenario[TestSeedingSession, Laid, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-the-project-searches-its-registries"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트 범위에서 레지스트리 읽기 역할을 받은 사용자가 그 범위에서 search 하면, "
            "그 프로젝트와 relation이 있는 레지스트리만 응답으로 옵니다",
            english=(
                "when a user granted the registry read role in a project scope searches in that "
                "scope, only the registries related to the project come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return RegistriesOfAProjectAndSomeone()

    @override
    def when(self) -> When[Laid, ContainerRegistryAdapter, Searched]:
        return SearchingInTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return OnlyTheRelatedRegistriesAreLeft()


@dataclass(frozen=True)
class AUserSearchesAProjectWithNoRelation(
    Scenario[TestSeedingSession, Laid, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-searches-the-registries-of-a-project-with-no-relation"

    @override
    def describe(self) -> str:
        return Says(
            "relation이 없는 프로젝트 범위에서 search 하면 빈 목록이 옵니다",
            english="searching in the scope of a project with no relation returns an empty list",
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return RegistriesOfAProjectAndSomeone(related=0)

    @override
    def when(self) -> When[Laid, ContainerRegistryAdapter, Searched]:
        return SearchingInTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return OnlyTheRelatedRegistriesAreLeft()


@dataclass(frozen=True)
class AUserReadingOnlyProjectsMayNotSearch(
    Scenario[TestSeedingSession, Laid, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-without-registry-read-may-not-search-the-registries-of-a-project"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트 범위에서 레지스트리 읽기 역할 없이 프로젝트 읽기 역할만 받은 사용자가 search 하면 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted only the project read role, not the registry read role, in a "
                "project scope searches, the call is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return RegistriesOfAProjectAndSomeone(entity_type=ProjectEntityType())

    @override
    def when(self) -> When[Laid, ContainerRegistryAdapter, Searched]:
        return SearchingInTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RegistryStep] = [
    AUserReadingInTheProjectSearches(),
    AUserSearchesAProjectWithNoRelation(),
    AUserReadingOnlyProjectsMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching_by_project(
    scenario: RegistryStep, adapter: ContainerRegistryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
