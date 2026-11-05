"""GQL 필터 모양으로 아티팩트 검색하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactsGQLInput,
    ArtifactGQLFilterInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.response import AdminSearchArtifactsPayload
from ai.backend.common.dto.manager.v2.artifact.types import ArtifactType
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.artifact import (
    ArtifactsToSearch,
    ArtifactsWorthSearching,
    TheArtifactPage,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchStep = Scenario[
    TestSeedingSession, ArtifactsToSearch, ArtifactAdapter, AdminSearchArtifactsPayload
]


class Narrowing(StrEnum):
    NONE = "none"
    MODEL = "model"


@dataclass(frozen=True)
class SearchingWithGqlFilter(When[ArtifactsToSearch, ArtifactAdapter, AdminSearchArtifactsPayload]):
    narrowing: Narrowing = Narrowing.NONE

    @override
    def operation(self) -> str:
        return "admin_search_gql"

    @override
    def describe(self, laid: ArtifactsToSearch) -> str:
        who = laid.caller.username
        if self.narrowing is Narrowing.NONE:
            return Says(
                f"{who}이 조건 없이 검색합니다",
                english=f"{who} searches with no condition",
            )
        return Says(
            f"{who}이 모델 종류로 좁혀 검색합니다",
            english=f"{who} searches narrowed to the model type",
        )

    def narrowing_filter(self) -> ArtifactGQLFilterInputDTO | None:
        match self.narrowing:
            case Narrowing.NONE:
                return None
            case Narrowing.MODEL:
                return ArtifactGQLFilterInputDTO(type=[ArtifactType.MODEL])

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: ArtifactsToSearch
    ) -> AdminSearchArtifactsPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search_gql(
                AdminSearchArtifactsGQLInput(filter=self.narrowing_filter())
            )


@dataclass(frozen=True)
class SearchingWithoutAConditionReturnsEvery(
    Scenario[TestSeedingSession, ArtifactsToSearch, ArtifactAdapter, AdminSearchArtifactsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "gql-searching-without-a-condition-returns-every-artifact"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 읽기 권한을 받은 사용자가 GQL 조건 없이 검색하면, 미리 저장한 "
            "아티팩트가 모두 한 페이지로 옵니다",
            english=(
                "when a user granted read permission on artifacts in global searches with no "
                "GQL condition, every artifact made in advance comes back on one page"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ArtifactsToSearch]:
        return ArtifactsWorthSearching(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(self) -> When[ArtifactsToSearch, ArtifactAdapter, AdminSearchArtifactsPayload]:
        return SearchingWithGqlFilter()

    @override
    def then(self) -> Then[ArtifactsToSearch, AdminSearchArtifactsPayload]:
        return TheArtifactPage(started=self.started)


@dataclass(frozen=True)
class ANarrowedSearchLeavesTheModels(
    Scenario[TestSeedingSession, ArtifactsToSearch, ArtifactAdapter, AdminSearchArtifactsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "gql-narrowing-to-the-model-type-leaves-only-model-artifacts"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 읽기 권한을 받은 사용자가 GQL 종류 필터로 좁혀 검색하면, 모델 "
            "아티팩트만 남습니다",
            english=(
                "when a user granted read permission on artifacts in global searches narrowed "
                "by the GQL type filter, only model artifacts remain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ArtifactsToSearch]:
        return ArtifactsWorthSearching(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(self) -> When[ArtifactsToSearch, ArtifactAdapter, AdminSearchArtifactsPayload]:
        return SearchingWithGqlFilter(narrowing=Narrowing.MODEL)

    @override
    def then(self) -> Then[ArtifactsToSearch, AdminSearchArtifactsPayload]:
        return TheArtifactPage(started=self.started, only_models=True)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[TestSeedingSession, ArtifactsToSearch, ArtifactAdapter, AdminSearchArtifactsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-artifacts-with-gql-filters"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 GQL 검색을 하려 하면, 전역 역할이 없어 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to search artifacts with GQL filters, it is "
                "rejected for lack of permission because they hold no global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ArtifactsToSearch]:
        return ArtifactsWorthSearching(role=UserRole.USER)

    @override
    def when(self) -> When[ArtifactsToSearch, ArtifactAdapter, AdminSearchArtifactsPayload]:
        return SearchingWithGqlFilter()

    @override
    def then(self) -> Then[ArtifactsToSearch, AdminSearchArtifactsPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchStep] = [
    SearchingWithoutAConditionReturnsEvery(started=datetime.now(UTC)),
    ANarrowedSearchLeavesTheModels(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_gql(
    scenario: SearchStep,
    adapter: ArtifactAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
