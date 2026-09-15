"""설정 정의 검색 — 슈퍼관리자 검사와 검색 조건을 확인한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_definition import (
    DefinitionsComeInNameOrder,
    EveryLaidDefinitionIsFound,
    ManyDefinitionsAndACaller,
    ManyDefinitionsAndSomeone,
    OnlyTheNamedDefinitionIsFound,
    TenComeWithANextPage,
    TheMiddleOffsetPageIsFound,
    TwoNamedDefinitionsAreFound,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    AppConfigDefinitionFilter,
    AppConfigDefinitionOrder,
    SearchAppConfigDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    SearchAppConfigDefinitionsPayload,
)
from ai.backend.common.dto.manager.v2.app_config_definition.types import (
    AppConfigDefinitionOrderField,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
)
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Searched = SearchAppConfigDefinitionsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverything(When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ManyDefinitionsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchAppConfigDefinitionsInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]):
    """골라낸 하나의 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.config_name} 이름 필터로 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ManyDefinitionsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchAppConfigDefinitionsInput(
                    filter=AppConfigDefinitionFilter(
                        config_name=StringFilter(equals=laid.named.config_name)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingInNameOrder(When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]):
    """이름 오름차순으로 정렬해 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        return f"{laid.caller.username}이 이름 오름차순으로 전체 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ManyDefinitionsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchAppConfigDefinitionsInput(
                    order=[
                        AppConfigDefinitionOrder(
                            field=AppConfigDefinitionOrderField.CONFIG_NAME,
                            direction=OrderDirection.ASC,
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class SearchingByEitherName(When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]):
    """두 이름 중 하나와 같은 정의를 이름순으로 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        first, second = laid.laid[:2]
        return f"{laid.caller.username}이 {first.config_name} 또는 {second.config_name}인 정의 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ManyDefinitionsAndACaller
    ) -> Searched:
        filters = [
            AppConfigDefinitionFilter(config_name=StringFilter(equals=one.config_name))
            for one in laid.laid[:2]
        ]
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchAppConfigDefinitionsInput(
                    filter=AppConfigDefinitionFilter(OR=filters),
                    order=[
                        AppConfigDefinitionOrder(
                            field=AppConfigDefinitionOrderField.CONFIG_NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                )
            )


@dataclass(frozen=True)
class SearchingAMiddleOffsetPage(
    When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    """이름순 결과에서 오프셋으로 중간 두 항목을 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        return f"{laid.caller.username}이 이름순 결과의 두 번째 항목부터 두 건 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ManyDefinitionsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchAppConfigDefinitionsInput(
                    order=[
                        AppConfigDefinitionOrder(
                            field=AppConfigDefinitionOrderField.CONFIG_NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=2,
                    offset=1,
                )
            )


@dataclass(frozen=True)
class SearchingWithMixedPagination(
    When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    """커서와 오프셋 페이지네이션을 함께 요청한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        return f"{laid.caller.username}이 커서와 오프셋 페이지네이션을 함께 지정해 조회"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ManyDefinitionsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchAppConfigDefinitionsInput(first=1, limit=1))


@dataclass(frozen=True)
class TheSuperadminCountsEveryOne(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-definition"

    @override
    def describe(self) -> str:
        return "설정 정의 셋이 있고 슈퍼관리자가 필터 없이 전체를 검색하면, 셋 다 집계된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return EveryLaidDefinitionIsFound()


@dataclass(frozen=True)
class FilteringByNameKeepsOne(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-by-name-keeps-only-that-definition"

    @override
    def describe(self) -> str:
        return "이름이 다른 설정 정의 여럿이 있고 슈퍼관리자가 이름 필터로 검색하면, 그 이름의 정의만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return OnlyTheNamedDefinitionIsFound()


@dataclass(frozen=True)
class OrderingByNameSortsThem(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "ordering-by-name-answers-in-name-order"

    @override
    def describe(self) -> str:
        return "설정 정의 셋이 있고 슈퍼관리자가 이름 오름차순으로 검색하면, 이름 순서대로 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingInNameOrder()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return DefinitionsComeInNameOrder()


@dataclass(frozen=True)
class AnOrFilterKeepsEitherName(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-or-filter-keeps-either-name"

    @override
    def describe(self) -> str:
        return "설정 정의 셋이 있고 슈퍼관리자가 두 이름을 OR로 묶어 검색하면, 두 이름 중 하나와 일치하는 정의만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingByEitherName()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return TwoNamedDefinitionsAreFound()


@dataclass(frozen=True)
class AnOffsetPageReportsBothDirections(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-middle-offset-page-reports-both-directions"

    @override
    def describe(self) -> str:
        return "설정 정의 넷을 이름순으로 두 번째 항목부터 두 건 조회하면, 중간 두 항목과 앞뒤 페이지가 모두 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=4, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingAMiddleOffsetPage()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return TheMiddleOffsetPageIsFound()


@dataclass(frozen=True)
class PaginationModesMayNotBeMixed(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "cursor-and-offset-pagination-may-not-be-mixed"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 커서와 오프셋 페이지네이션을 함께 지정하면, 서로 다른 방식을 섞었다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingWithMixedPagination()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return TheCallIsRefused(InvalidGraphQLParameters)


@dataclass(frozen=True)
class NoPageSizeMeansTen(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "leaving-the-page-size-out-answers-ten-with-a-next-page"

    @override
    def describe(self) -> str:
        return "설정 정의 11개가 있고 슈퍼관리자가 크기 없이 검색하면, 10건까지 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=11, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return TenComeWithANextPage()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-definitions"

    @override
    def describe(self) -> str:
        return "일반 사용자가 전체를 검색하면, 슈퍼관리자 권한이 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3)

    @override
    def when(self) -> When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyDefinitionsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryOne(),
    FilteringByNameKeepsOne(),
    OrderingByNameSortsThem(),
    AnOrFilterKeepsEitherName(),
    AnOffsetPageReportsBothDirections(),
    PaginationModesMayNotBeMixed(),
    NoPageSizeMeansTen(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
