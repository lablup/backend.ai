"""정의 훑기 — 전역 역할이 지킨다.

정의마다 읽을 수 있어도 전체 훑기는 역할이 지킨다. 하나를 읽는 문과 전체를 훑는 문이
다르다는 것을 마지막 줄이 못박는다.
"""

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
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Searched = SearchAppConfigDefinitionsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverything(When[ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]):
    """필터 없이 전체를 훑는다."""

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
    """골라낼 하나의 이름으로 거른다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDefinitionsAndACaller) -> str:
        return f"{laid.caller.username}이 이름 {laid.named.config_name}으로 걸러 조회"

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
    """이름 오름차순으로 정렬해 훑는다."""

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
class TheSuperadminCountsEveryOne(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-definition"

    @override
    def describe(self) -> str:
        return "정의 셋이 있고 슈퍼관리자가 필터 없이 전체를 훑으면, 셋을 모두 센다. 이 문은 전역 역할이다"

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
        return (
            "이름이 다른 정의 여럿이 있고 슈퍼관리자가 이름으로 걸러 훑으면, 그 이름의 것만 남는다"
        )

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
        return "정의 셋이 있고 슈퍼관리자가 이름 오름차순으로 훑으면, 이름 순서대로 온다"

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
class NoPageSizeMeansTen(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "leaving-the-page-size-out-answers-ten-with-a-next-page"

    @override
    def describe(self) -> str:
        return "정의 열하나가 있고 슈퍼관리자가 크기 없이 훑으면, 열 건까지 오고 다음 쪽이 있다고 답한다"

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
class AGrantDoesNotOpenTheGlobalDoor(
    Scenario[SeedingSession, ManyDefinitionsAndACaller, AppConfigDefinitionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-search-every-definition"

    @override
    def describe(self) -> str:
        return (
            "설정 정의 읽기 권한을 받았지만 슈퍼관리자가 아닌 사용자가 전체를 훑으면, 역할로 "
            "거부된다. 하나를 읽는 문과 전체를 훑는 문이 다르다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyDefinitionsAndACaller]:
        return ManyDefinitionsAndSomeone(count=3, granted=(Permission.READ,))

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
    NoPageSizeMeansTen(),
    AGrantDoesNotOpenTheGlobalDoor(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
