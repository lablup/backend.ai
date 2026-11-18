"""컨테이너 레지스트리 검색 권한과 레지스트리 고유 필드 필터."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import override

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    ContainerRegistryFilter,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    AdminSearchContainerRegistriesPayload,
    ContainerRegistryNode,
)
from ai.backend.common.dto.manager.v2.container_registry.types import (
    ContainerRegistryTypeFilter,
)
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.container_registry import (
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchScenario = Scenario[
    TestSeedingSession,
    ManyRegistriesAndACaller,
    ContainerRegistryAdapter,
    AdminSearchContainerRegistriesPayload,
]
type SearchGiven = Given[TestSeedingSession, ManyRegistriesAndACaller]
type SearchThen = Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]


class ContainerRegistrySearchScenario(
    Scenario[
        TestSeedingSession,
        ManyRegistriesAndACaller,
        ContainerRegistryAdapter,
        AdminSearchContainerRegistriesPayload,
    ]
):
    """Common scenario signature for container registry searches."""


class FilterKind(StrEnum):
    NONE = "none"
    TYPE = "type"
    NON_GLOBAL = "non-global"


def registry_snapshot(
    registry: ContainerRegistryData | ContainerRegistryNode,
) -> tuple[object, ...]:
    return (
        registry.id,
        registry.entity_id if isinstance(registry, ContainerRegistryNode) else registry.entity_id(),
        registry.url,
        registry.registry_name,
        registry.type,
        registry.project,
        registry.username,
        registry.ssl_verify,
        registry.is_global,
        registry.extra,
    )


def registry_items_match(
    got: Sequence[ContainerRegistryNode],
    wanted: Sequence[ContainerRegistryData],
    came_from: str = Says(
        "미리 저장한 컨테이너 레지스트리",
        english="the container registries seeded in advance",
    ),
) -> Verdict:
    return Held(
        "items",
        [registry_snapshot(one) for one in got],
        SameAs([registry_snapshot(one) for one in wanted], came_from),
    )


@dataclass(frozen=True)
class Searching(
    When[ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload]
):
    filter_kind: FilterKind = FilterKind.NONE

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        who = laid.caller.username
        if self.filter_kind is FilterKind.NONE:
            return Says(
                f"{who}이 조건 없이 검색합니다",
                english=f"{who} searches with no condition",
            )
        return Says(
            f"{who}이 {self.filter_kind.value} 필터로 검색합니다",
            english=f"{who} searches with the {self.filter_kind.value} filter",
        )

    def _filter(self, laid: ManyRegistriesAndACaller) -> ContainerRegistryFilter | None:
        match self.filter_kind:
            case FilterKind.NONE:
                return None
            case FilterKind.TYPE:
                return ContainerRegistryFilter(
                    type=ContainerRegistryTypeFilter(equals=ContainerRegistryType.DOCKER)
                )
            case FilterKind.NON_GLOBAL:
                return ContainerRegistryFilter(is_global=False)

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> AdminSearchContainerRegistriesPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchContainerRegistriesInput(filter=self._filter(laid))
            )


@dataclass(frozen=True)
class AllSeededRegistriesAreReturned(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 컨테이너 레지스트리가 모두 집계됩니다",
            english="every container registry seeded in advance is counted",
        )

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            registry_items_match(
                sorted(payload.items, key=lambda registry: registry.id),
                sorted(laid.registries, key=lambda registry: registry.id),
            ),
            Same("total_count", payload.total_count, len(laid.registries)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheMatchingRegistryIsReturned(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    @override
    def says(self) -> str:
        return Says(
            "필터와 일치하는 컨테이너 레지스트리 하나만 남습니다",
            english="only one container registry that matches the filter remains",
        )

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            registry_items_match(payload.items, [laid.matching_registry]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyNonGlobalRegistriesAreReturned(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    @override
    def says(self) -> str:
        return Says(
            "전역이 아닌 컨테이너 레지스트리만 반환됩니다",
            english="only container registries that are not global come back",
        )

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        expected = sorted(
            (registry for registry in laid.registries if not registry.is_global),
            key=lambda registry: registry.id,
        )
        return [
            registry_items_match(
                sorted(payload.items, key=lambda registry: registry.id),
                expected,
            ),
            Same("total_count", payload.total_count, len(expected)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class SearchingWithoutAFilterCountsEvery(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "searching-without-a-filter-counts-every-registry"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 조건 없이 검색하면 미리 저장한 컨테이너 레지스트리가 모두 반환됩니다",
            english=(
                "when the superadmin searches with no condition, every container registry "
                "seeded in advance comes back"
            ),
        )

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching()

    @override
    def then(self) -> SearchThen:
        return AllSeededRegistriesAreReturned()


@dataclass(frozen=True)
class ATypeNarrowsTheSearch(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "filtering-by-type-leaves-only-matching-registries"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 종류 필터로 검색하면 그 종류의 컨테이너 레지스트리만 남습니다",
            english=(
                "when the superadmin searches with the type filter, only container registries "
                "of that type remain"
            ),
        )

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching(filter_kind=FilterKind.TYPE)

    @override
    def then(self) -> SearchThen:
        return OnlyTheMatchingRegistryIsReturned()


@dataclass(frozen=True)
class GlobalVisibilityNarrowsTheSearch(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "filtering-by-global-visibility-leaves-only-non-global-registries"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 전역 여부 필터로 검색하면 전역이 아닌 컨테이너 레지스트리만 남습니다",
            english=(
                "when the superadmin searches with the global visibility filter, only container "
                "registries that are not global remain"
            ),
        )

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching(filter_kind=FilterKind.NON_GLOBAL)

    @override
    def then(self) -> SearchThen:
        return OnlyNonGlobalRegistriesAreReturned()


@dataclass(frozen=True)
class APlainUserMayNotSearch(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-registries"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 컨테이너 레지스트리를 검색하려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다",
            english=(
                "when a user who is not the superadmin tries to search container registries, "
                "it is rejected for lack of permission. This call checks only whether the "
                "caller is the superadmin and does not look at the permissions granted"
            ),
        )

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> Searching:
        return Searching()

    @override
    def then(self) -> SearchThen:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchScenario] = [
    SearchingWithoutAFilterCountsEvery(),
    ATypeNarrowsTheSearch(),
    GlobalVisibilityNarrowsTheSearch(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
