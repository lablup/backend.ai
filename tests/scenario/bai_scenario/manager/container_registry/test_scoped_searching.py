"""컨테이너 레지스트리 스코프 검색 — 도메인과 relation이 있는 레지스트리를 검색한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.container_registry.request import (
    ContainerRegistryFilter,
    ContainerRegistryOrder,
    ScopedSearchContainerRegistriesInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    ScopedSearchContainerRegistriesPayload,
)
from ai.backend.common.dto.manager.v2.container_registry.types import (
    ContainerRegistryOrderField,
    ContainerRegistryScope,
)
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    RelationsAndACaller,
    RelationsInTwoDomains,
    TheWantedRegistriesAreListedByName,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = ScopedSearchContainerRegistriesPayload
type SearchingStep = Scenario[
    TestSeedingSession, RelationsAndACaller, ContainerRegistryAdapter, Searched
]


@dataclass(frozen=True)
class SearchingInTheDomain(When[RelationsAndACaller, ContainerRegistryAdapter, Searched]):
    """검색할 도메인을 스코프로, 다른 레지스트리를 빼는 이름 필터와 이름순 정렬로 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: RelationsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 검색할 도메인을 스코프로, 다른 레지스트리를 빼는 이름 "
            "필터와 이름순 정렬, 페이지 크기를 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} reads scoped to the domain to search, with a name "
                "filter leaving out the other registry, the name order and a page size in one "
                "request"
            ),
        )

    @override
    async def call(self, adapter: ContainerRegistryAdapter, laid: RelationsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchContainerRegistriesInput(
                    scope=ContainerRegistryScope(domain=[UUIDScope(value=laid.home.id)]),
                    filter=ContainerRegistryFilter(
                        registry_name=StringFilter(not_equals=laid.other_registry.registry_name)
                    ),
                    order=[ContainerRegistryOrder(field=ContainerRegistryOrderField.REGISTRY_NAME)],
                    limit=10,
                )
            )


@dataclass(frozen=True)
class AUserReadingRegistriesInTheDomainSearchesThem(
    Scenario[TestSeedingSession, RelationsAndACaller, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-registries-in-the-domain-scoped-searches-its-registries"

    @override
    def describe(self) -> str:
        return Says(
            "검색할 도메인에서 레지스트리 조회 권한을 받은 사용자가 그 도메인을 스코프로, 이름을 "
            "필터로, 이름순 정렬과 페이지 크기를 한 번에 검색하면, 그 도메인과 relation이 있는 "
            "레지스트리 가운데 필터에 맞는 것만 이름순으로 반환됩니다",
            english=(
                "when a user granted permission to read registries in the domain to search "
                "searches scoped to that domain, with a name as the filter, the name order and a "
                "page size in one request, only the registries related to that domain that match "
                "the filter come back in name order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RelationsAndACaller]:
        return RelationsInTwoDomains()

    @override
    def when(self) -> When[RelationsAndACaller, ContainerRegistryAdapter, Searched]:
        return SearchingInTheDomain()

    @override
    def then(self) -> Then[RelationsAndACaller, Searched]:
        return TheWantedRegistriesAreListedByName()


@dataclass(frozen=True)
class AUserNotReadingRegistriesInTheDomainIsRefused(
    Scenario[TestSeedingSession, RelationsAndACaller, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-not-reading-registries-in-the-domain-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "검색할 도메인에서 레지스트리 조회 권한을 받지 않은 사용자가 그 도메인을 스코프로 "
            "검색하면 권한 부족으로 거부됩니다",
            english=(
                "when a user not granted permission to read registries in the domain to search "
                "searches scoped to that domain, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RelationsAndACaller]:
        return RelationsInTwoDomains(reads_in_domain=False)

    @override
    def when(self) -> When[RelationsAndACaller, ContainerRegistryAdapter, Searched]:
        return SearchingInTheDomain()

    @override
    def then(self) -> Then[RelationsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    AUserReadingRegistriesInTheDomainSearchesThem(),
    AUserNotReadingRegistriesInTheDomainIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: SearchingStep,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
