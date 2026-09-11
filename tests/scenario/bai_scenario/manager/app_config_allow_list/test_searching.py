"""허용 항목 훑기 — 전역 역할이 지킨다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_allow_list import (
    EntriesComeInRankOrder,
    EntriesLaidAcross,
    EveryLaidEntryIsFound,
    ManyEntriesAndACaller,
    OnlyOneKindsEntriesAreFound,
    OnlyTheNamedNamesEntriesAreFound,
    TenEntriesComeWithANextPage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    AppConfigAllowListFilter,
    AppConfigAllowListOrder,
    SearchAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    SearchAppConfigAllowListPayload,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
    AppConfigAllowListOrderField,
    AppConfigScopeTypeFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Searched = SearchAppConfigAllowListPayload
type SearchingStep = Scenario[
    SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched
]

EVERY_KIND = (AppConfigScopeType.PUBLIC, AppConfigScopeType.DOMAIN, AppConfigScopeType.USER)


@dataclass(frozen=True)
class SearchingEverything(When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]):
    """필터 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyEntriesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: ManyEntriesAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchAppConfigAllowListInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]):
    """골라낼 이름으로 거른다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyEntriesAndACaller) -> str:
        return f"{laid.caller.username}이 이름 {laid.named}으로 걸러 조회"

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: ManyEntriesAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchAppConfigAllowListInput(
                    filter=AppConfigAllowListFilter(config_name=StringFilter(equals=laid.named))
                )
            )


@dataclass(frozen=True)
class SearchingOneKind(When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]):
    """스코프 종류 하나로 거른다."""

    kind: AppConfigScopeType

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyEntriesAndACaller) -> str:
        return f"{laid.caller.username}이 {SCOPE_NAMES[self.kind]} 종류로 걸러 조회"

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: ManyEntriesAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchAppConfigAllowListInput(
                    filter=AppConfigAllowListFilter(
                        scope_type=AppConfigScopeTypeFilter(equals=self.kind)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingInRankOrder(When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]):
    """순위 오름차순으로 정렬해 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyEntriesAndACaller) -> str:
        return f"{laid.caller.username}이 순위 오름차순으로 전체 조회"

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: ManyEntriesAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchAppConfigAllowListInput(
                    order=[
                        AppConfigAllowListOrder(
                            field=AppConfigAllowListOrderField.RANK, direction=OrderDirection.ASC
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class TheSuperadminCountsEveryOne(
    Scenario[SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-entry"

    @override
    def describe(self) -> str:
        return "이름 둘에 항목 넷이 있고 슈퍼관리자가 필터 없이 전체를 훑으면, 넷을 모두 센다. 이 문은 전역 역할이다"

    @override
    def given(self) -> Given[SeedingSession, ManyEntriesAndACaller]:
        return EntriesLaidAcross(
            names=2,
            kinds=(AppConfigScopeType.PUBLIC, AppConfigScopeType.USER),
            role=UserRole.SUPERADMIN,
        )

    @override
    def when(self) -> When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyEntriesAndACaller, Searched]:
        return EveryLaidEntryIsFound()


@dataclass(frozen=True)
class FilteringByNameKeepsThatNames(
    Scenario[SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-by-name-keeps-only-that-names-entries"

    @override
    def describe(self) -> str:
        return "이름 둘에 항목 넷이 있고 슈퍼관리자가 이름으로 걸러 훑으면, 그 이름의 것만 남는다"

    @override
    def given(self) -> Given[SeedingSession, ManyEntriesAndACaller]:
        return EntriesLaidAcross(
            names=2,
            kinds=(AppConfigScopeType.PUBLIC, AppConfigScopeType.USER),
            role=UserRole.SUPERADMIN,
        )

    @override
    def when(self) -> When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyEntriesAndACaller, Searched]:
        return OnlyTheNamedNamesEntriesAreFound()


@dataclass(frozen=True)
class FilteringByKindKeepsThatKind(
    Scenario[SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-by-scope-kind-keeps-only-that-kinds-entries"

    @override
    def describe(self) -> str:
        return "세 종류에 항목이 하나씩 있고 슈퍼관리자가 사용자 종류로 걸러 훑으면, 사용자 항목만 남는다"

    @override
    def given(self) -> Given[SeedingSession, ManyEntriesAndACaller]:
        return EntriesLaidAcross(names=1, kinds=EVERY_KIND, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]:
        return SearchingOneKind(kind=AppConfigScopeType.USER)

    @override
    def then(self) -> Then[ManyEntriesAndACaller, Searched]:
        return OnlyOneKindsEntriesAreFound(kind=AppConfigScopeType.USER)


@dataclass(frozen=True)
class OrderingByRankSortsThem(
    Scenario[SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "ordering-by-rank-answers-in-rank-order"

    @override
    def describe(self) -> str:
        return (
            "순위가 다른 항목 셋이 있고 슈퍼관리자가 순위 오름차순으로 훑으면, 순위 순서대로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyEntriesAndACaller]:
        return EntriesLaidAcross(names=1, kinds=EVERY_KIND, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]:
        return SearchingInRankOrder()

    @override
    def then(self) -> Then[ManyEntriesAndACaller, Searched]:
        return EntriesComeInRankOrder()


@dataclass(frozen=True)
class NoPageSizeMeansTen(
    Scenario[SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "leaving-the-page-size-out-answers-ten-with-a-next-page"

    @override
    def describe(self) -> str:
        return "항목 열하나가 있고 슈퍼관리자가 크기 없이 훑으면, 열 건까지 오고 다음 쪽이 있다고 답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyEntriesAndACaller]:
        return EntriesLaidAcross(names=11, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyEntriesAndACaller, Searched]:
        return TenEntriesComeWithANextPage()


@dataclass(frozen=True)
class AGrantDoesNotOpenTheGlobalDoor(
    Scenario[SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-search-every-entry"

    @override
    def describe(self) -> str:
        return (
            "허용 항목 읽기 권한을 받았지만 슈퍼관리자가 아닌 사용자가 전체를 훑으면, 역할로 "
            "거부된다. 하나를 읽는 문과 전체를 훑는 문이 다르다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyEntriesAndACaller]:
        return EntriesLaidAcross(names=2, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyEntriesAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryOne(),
    FilteringByNameKeepsThatNames(),
    FilteringByKindKeepsThatKind(),
    OrderingByRankSortsThem(),
    NoPageSizeMeansTen(),
    AGrantDoesNotOpenTheGlobalDoor(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
