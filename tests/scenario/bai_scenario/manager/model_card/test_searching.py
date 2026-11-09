"""모델 카드 범위 조회: 스코프, 프로젝트, vfolder 소유자로 찾는다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.model_card.request import (
    ModelCardFilter,
    ModelCardOrder,
    ScopedSearchModelCardsInput,
    SearchModelCardsInput,
)
from ai.backend.common.dto.manager.v2.model_card.response import SearchModelCardsPayload
from ai.backend.common.dto.manager.v2.model_card.types import (
    ModelCardOrderField,
    ModelCardScope,
    ModelCardUsage,
    ModelCardUses,
)
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.model_card import (
    SEARCH_TITLE,
    ProjectCards,
    TheFoundPage,
    TwoProjectsOfCardsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchModelCardsPayload
type SearchStep = Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Searched]

FILTER = ModelCardFilter(title=StringFilter(equals=SEARCH_TITLE))
ORDER = [ModelCardOrder(field=ModelCardOrderField.NAME, direction=OrderDirection.DESC)]


@dataclass(frozen=True)
class ScopedSearching(When[ProjectCards, ModelCardAdapter, Searched]):
    """첫 프로젝트 범위에서 제목 필터, 이름 내림차순, 두 건 한 페이지로 찾는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ProjectCards) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트 범위에서 제목 필터, 이름 "
            "내림차순, 두 건 한 페이지로 조회합니다",
            english=(
                f"{laid.caller.username} searches the scope of the project {laid.project.name} "
                "with a title filter, name descending and a page of two"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ProjectCards) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchModelCardsInput(
                    scope=ModelCardScope(project=[UUIDScope(value=laid.project.id)]),
                    filter=FILTER,
                    order=ORDER,
                    limit=2,
                )
            )


@dataclass(frozen=True)
class ProjectSearching(When[ProjectCards, ModelCardAdapter, Searched]):
    """첫 프로젝트에서 제목 필터, 이름 내림차순, 두 건 한 페이지로 찾는다."""

    @override
    def operation(self) -> str:
        return "project_search"

    @override
    def describe(self, laid: ProjectCards) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트에서 제목 필터, 이름 "
            "내림차순, 두 건 한 페이지로 조회합니다",
            english=(
                f"{laid.caller.username} searches the project {laid.project.name} "
                "with a title filter, name descending and a page of two"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ProjectCards) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.project_search(
                laid.project.id,
                SearchModelCardsInput(filter=FILTER, order=ORDER, limit=2),
            )


@dataclass(frozen=True)
class OwnershipSearching(When[ProjectCards, ModelCardAdapter, Searched]):
    """첫 프로젝트가 소유한 vfolder 하나를 쓰는 카드를 제목 필터와 함께 찾는다."""

    @override
    def operation(self) -> str:
        return "ownership_search"

    @override
    def describe(self, laid: ProjectCards) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트가 소유한 vfolder 하나를 쓰는 "
            "카드를 제목 필터, 이름 내림차순, 두 건 한 페이지로 조회합니다",
            english=(
                f"{laid.caller.username} searches the cards using one vfolder owned by the "
                f"project {laid.project.name} with a title filter, name descending and a page "
                "of two"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ProjectCards) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.ownership_search(
                laid.project.id,
                None,
                SearchModelCardsInput(
                    usage=ModelCardUsage(uses=ModelCardUses(vfolder=[laid.found[0].vfolder_id])),
                    filter=FILTER,
                    order=ORDER,
                    limit=2,
                ),
            )


@dataclass(frozen=True)
class AReaderGetsTheFoundPage(
    Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Searched]
):
    started: datetime
    calling: When[ProjectCards, ModelCardAdapter, Searched]
    label: str
    folders: bool = False
    picked: tuple[int, ...] = (2, 1)
    total_count: int = 3
    has_next_page: bool = True

    @override
    def summary(self) -> str:
        return f"a-user-granted-model-card-read-finds-cards-by-{self.label}"

    @override
    def describe(self) -> str:
        return Says(
            "첫 프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 조회하면, 범위 안에서 필터에 "
            "걸리는 카드만 요청한 순서와 페이지대로 옵니다",
            english=(
                "when a user granted model card read in the first project searches, only the "
                "cards in the scope that the filter matches come back in the requested order "
                "and page"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectCards]:
        return TwoProjectsOfCardsAndSomeone(granted=(Permission.READ,), reads_folders=self.folders)

    @override
    def when(self) -> When[ProjectCards, ModelCardAdapter, Searched]:
        return self.calling

    @override
    def then(self) -> Then[ProjectCards, Searched]:
        return TheFoundPage(
            started=self.started,
            picked=self.picked,
            total_count=self.total_count,
            has_next_page=self.has_next_page,
        )


@dataclass(frozen=True)
class AUserWithoutReadIsRefused(
    Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Searched]
):
    calling: When[ProjectCards, ModelCardAdapter, Searched]
    label: str
    folders: bool = False

    @override
    def summary(self) -> str:
        return f"a-user-without-model-card-read-may-not-find-cards-by-{self.label}"

    @override
    def describe(self) -> str:
        return Says(
            "첫 프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 조회하면 권한 "
            "부족으로 거부됩니다",
            english=(
                "when a user granted only model card update and not read in the first project "
                "searches, the call is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectCards]:
        return TwoProjectsOfCardsAndSomeone(
            granted=(Permission.UPDATE,), reads_folders=self.folders
        )

    @override
    def when(self) -> When[ProjectCards, ModelCardAdapter, Searched]:
        return self.calling

    @override
    def then(self) -> Then[ProjectCards, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[SearchStep] = [
    AReaderGetsTheFoundPage(STARTED, ScopedSearching(), "scope"),
    AUserWithoutReadIsRefused(ScopedSearching(), "scope"),
    AReaderGetsTheFoundPage(STARTED, ProjectSearching(), "project"),
    AUserWithoutReadIsRefused(ProjectSearching(), "project"),
    AReaderGetsTheFoundPage(
        STARTED,
        OwnershipSearching(),
        "vfolder-ownership",
        folders=True,
        picked=(0,),
        total_count=1,
        has_next_page=False,
    ),
    AUserWithoutReadIsRefused(OwnershipSearching(), "vfolder-ownership", folders=True),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
