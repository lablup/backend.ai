"""로그인 이력 검색 — superadmin 의 전체 검색과 자기 이력 검색."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.login_history.request import (
    AdminSearchLoginHistoryInput,
    LoginHistoryFilter,
    LoginHistoryOrder,
    LoginHistoryResultFilter,
    MySearchLoginHistoryInput,
)
from ai.backend.common.dto.manager.v2.login_history.types import (
    LoginAttemptResult,
    LoginHistoryOrderField,
    OrderDirection,
)
from ai.backend.manager.api.adapters.login_history.adapter import LoginHistoryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_history import (
    AdminHistoryToPage,
    ARegularUserReadingTheDomain,
    HistoryToSearch,
    MyHistoryToPage,
    SearchAnswer,
    ThePageOfHistory,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

_FAILED_ONLY = LoginHistoryFilter(
    result=LoginHistoryResultFilter(not_equals=LoginAttemptResult.SUCCESS)
)
_BY_RESULT = [LoginHistoryOrder(field=LoginHistoryOrderField.RESULT, direction=OrderDirection.ASC)]

type SearchingStep = Scenario[
    TestSeedingSession, HistoryToSearch, LoginHistoryAdapter, SearchAnswer
]


@dataclass(frozen=True)
class SearchingEveryUser(When[HistoryToSearch, LoginHistoryAdapter, SearchAnswer]):
    """모든 사용자의 이력을 훑는다."""

    input: AdminSearchLoginHistoryInput

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: HistoryToSearch) -> str:
        return Says(
            f"{laid.caller.username}이 모든 사용자의 로그인 이력을 조회합니다",
            english=f"{laid.caller.username} searches the login history of every user",
        )

    @override
    async def call(self, adapter: LoginHistoryAdapter, laid: HistoryToSearch) -> SearchAnswer:
        with ActingAs(laid.caller):
            return await adapter.admin_search(self.input)


@dataclass(frozen=True)
class SearchingMyHistory(When[HistoryToSearch, LoginHistoryAdapter, SearchAnswer]):
    """자기 이력을 훑는다."""

    input: MySearchLoginHistoryInput

    @override
    def operation(self) -> str:
        return "my_search"

    @override
    def describe(self, laid: HistoryToSearch) -> str:
        return Says(
            f"{laid.caller.username}이 자기 로그인 이력을 조회합니다",
            english=f"{laid.caller.username} searches their own login history",
        )

    @override
    async def call(self, adapter: LoginHistoryAdapter, laid: HistoryToSearch) -> SearchAnswer:
        with ActingAs(laid.caller):
            return await adapter.my_search(self.input)


@dataclass(frozen=True)
class TheSuperadminSearchesEveryUsersHistory(
    Scenario[TestSeedingSession, HistoryToSearch, LoginHistoryAdapter, SearchAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-the-login-history-of-every-user"

    @override
    def describe(self) -> str:
        return Says(
            "전역 역할이 막는 전체 검색을 superadmin 이 필터, 정렬, 페이지와 함께 호출하면, "
            "사용자와 무관하게 필터에 걸리는 이력의 첫 페이지가 정렬 순서대로 반환됩니다",
            english=(
                "when the superadmin calls the search gated by the global role with a "
                "filter, an order and a page, the first page of the filtered records comes "
                "back in the requested order regardless of the user"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, HistoryToSearch]:
        return AdminHistoryToPage()

    @override
    def when(self) -> When[HistoryToSearch, LoginHistoryAdapter, SearchAnswer]:
        return SearchingEveryUser(
            AdminSearchLoginHistoryInput(filter=_FAILED_ONLY, order=_BY_RESULT, limit=2, offset=0)
        )

    @override
    def then(self) -> Then[HistoryToSearch, SearchAnswer]:
        return ThePageOfHistory(started=self.started)


@dataclass(frozen=True)
class ARegularUserMayNotSearchEveryUsersHistory(
    Scenario[TestSeedingSession, HistoryToSearch, LoginHistoryAdapter, SearchAnswer]
):
    @override
    def summary(self) -> str:
        return "a-regular-user-may-not-search-the-login-history-of-every-user"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 스코프에서 사용자 READ 를 받은 일반 사용자가 전체 검색을 호출하면, "
            "전역 역할이 막습니다",
            english=(
                "when a regular user granted READ on users in the domain scope calls the "
                "search gated by the global role, it is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, HistoryToSearch]:
        return ARegularUserReadingTheDomain()

    @override
    def when(self) -> When[HistoryToSearch, LoginHistoryAdapter, SearchAnswer]:
        return SearchingEveryUser(AdminSearchLoginHistoryInput())

    @override
    def then(self) -> Then[HistoryToSearch, SearchAnswer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AGrantedUserSearchesTheirOwnHistory(
    Scenario[TestSeedingSession, HistoryToSearch, LoginHistoryAdapter, SearchAnswer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-themselves-searches-their-own-login-history"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 를 받은 사용자가 필터, 정렬, 페이지와 함께 조회하면, "
            "자기 이력 중 필터에 걸리는 첫 페이지가 정렬 순서대로 반환되고 다른 사용자의 "
            "이력은 빠집니다",
            english=(
                "when a user granted READ on themselves searches with a filter, an order and "
                "a page, the first page of their own filtered records comes back in the "
                "requested order and the records of other users are left out"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, HistoryToSearch]:
        return MyHistoryToPage(permitted=True)

    @override
    def when(self) -> When[HistoryToSearch, LoginHistoryAdapter, SearchAnswer]:
        return SearchingMyHistory(
            MySearchLoginHistoryInput(filter=_FAILED_ONLY, order=_BY_RESULT, limit=2, offset=0)
        )

    @override
    def then(self) -> Then[HistoryToSearch, SearchAnswer]:
        return ThePageOfHistory(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheirHistory(
    Scenario[TestSeedingSession, HistoryToSearch, LoginHistoryAdapter, SearchAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-their-own-login-history"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 이력을 조회하면, 본인이어도 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing searches their own history, it is rejected "
                "with a permission failure even for themselves"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, HistoryToSearch]:
        return MyHistoryToPage(permitted=False)

    @override
    def when(self) -> When[HistoryToSearch, LoginHistoryAdapter, SearchAnswer]:
        return SearchingMyHistory(MySearchLoginHistoryInput())

    @override
    def then(self) -> Then[HistoryToSearch, SearchAnswer]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSearchesEveryUsersHistory(started=datetime.now(UTC)),
    ARegularUserMayNotSearchEveryUsersHistory(),
    AGrantedUserSearchesTheirOwnHistory(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchTheirHistory(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: LoginHistoryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
