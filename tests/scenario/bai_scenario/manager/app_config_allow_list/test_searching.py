"""allow_list 검색 — 슈퍼관리자 검사와 커서 다음 페이지를 확인한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    SearchAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    SearchAppConfigAllowListPayload,
)
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_allow_list import (
    EntriesLaidAcross,
    EveryLaidEntryIsFound,
    ManyEntriesAndACaller,
    TheEntryAfterTheCursorIsFound,
    in_page_order,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchAppConfigAllowListPayload
type SearchingStep = Scenario[
    SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverything(When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyEntriesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 검색"

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: ManyEntriesAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchAppConfigAllowListInput())


@dataclass(frozen=True)
class SearchingAfterTheFirst(When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]):
    """기본 순서의 첫 항목을 가리키는 커서 뒤로 한 건을 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyEntriesAndACaller) -> str:
        return f"{laid.caller.username}이 기본 순서 첫 항목의 커서 뒤로 한 건 검색"

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: ManyEntriesAndACaller
    ) -> Searched:
        ordered = in_page_order(laid.laid)
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchAppConfigAllowListInput(first=1, after=encode_cursor(ordered[0].id))
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
        return "설정 이름 둘에 allow_list 넷이 있고 슈퍼관리자가 필터 없이 검색하면, 네 allow_list가 모두 반환된다"

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
class AForwardCursorAnswersTheNextOne(
    Scenario[SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-forward-cursor-answers-the-one-right-after-it"

    @override
    def describe(self) -> str:
        return "생성 시각이 모두 같은 allow_list 넷이 있고 슈퍼관리자가 기본 순서 첫 항목의 커서 뒤로 한 건을 검색하면, 바로 다음 allow_list 하나와 앞뒤 페이지가 모두 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyEntriesAndACaller]:
        return EntriesLaidAcross(names=4, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]:
        return SearchingAfterTheFirst()

    @override
    def then(self) -> Then[ManyEntriesAndACaller, Searched]:
        return TheEntryAfterTheCursorIsFound()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[SeedingSession, ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-entries"

    @override
    def describe(self) -> str:
        return "일반 사용자가 allow_list를 검색하면, 슈퍼관리자 권한이 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyEntriesAndACaller]:
        return EntriesLaidAcross(names=2)

    @override
    def when(self) -> When[ManyEntriesAndACaller, AppConfigAllowListAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyEntriesAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryOne(),
    AForwardCursorAnswersTheNextOne(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
