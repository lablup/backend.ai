"""규칙 검색 — 필터가 무엇을 좁히고, 누가 검색할 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.notification import NotificationRuleType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationRuleFilter,
    NotificationRuleTypeFilter,
    SearchNotificationRulesInput,
)
from ai.backend.common.dto.manager.v2.notification.response import SearchNotificationRulesPayload
from ai.backend.common.dto.manager.v2.notification.types import NotificationRuleTypeDTO
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AnEnabledAndADisabledRule,
    ManyRulesAndACaller,
    OnlyTheNamedRuleIsLeft,
    TheLaidRulesAreLeft,
    TwoRulesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchNotificationRulesPayload
type SearchingStep = Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryRule(When[ManyRulesAndACaller, NotificationAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search_rules"

    @override
    def describe(self, laid: ManyRulesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_rules(SearchNotificationRulesInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyRulesAndACaller, NotificationAdapter, Searched]):
    """골라낸 하나의 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_rules"

    @override
    def describe(self, laid: ManyRulesAndACaller) -> str:
        return f"{laid.caller.username}이 이름 {laid.named.name} 필터로 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_rules(
                SearchNotificationRulesInput(
                    filter=NotificationRuleFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class SearchingByRuleType(When[ManyRulesAndACaller, NotificationAdapter, Searched]):
    """골라낸 하나의 종류를 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_rules"

    @override
    def describe(self, laid: ManyRulesAndACaller) -> str:
        return f"{laid.caller.username}이 종류 {laid.named.rule_type.value} 필터로 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_rules(
                SearchNotificationRulesInput(
                    filter=NotificationRuleFilter(
                        rule_type=NotificationRuleTypeFilter(
                            equals=NotificationRuleTypeDTO(laid.named.rule_type.value)
                        )
                    )
                )
            )


@dataclass(frozen=True)
class SearchingTheEnabledOnes(When[ManyRulesAndACaller, NotificationAdapter, Searched]):
    """활성인 규칙만 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_rules"

    @override
    def describe(self, laid: ManyRulesAndACaller) -> str:
        return f"{laid.caller.username}이 활성 필터로 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_rules(
                SearchNotificationRulesInput(filter=NotificationRuleFilter(enabled=True))
            )


@dataclass(frozen=True)
class TheSuperadminCountsEveryRule(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-rule-laid"

    @override
    def describe(self) -> str:
        return "규칙 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, Searched]:
        return SearchingEveryRule()

    @override
    def then(self) -> Then[ManyRulesAndACaller, Searched]:
        return TheLaidRulesAreLeft()


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-that-rule"

    @override
    def describe(self) -> str:
        return "규칙 둘 중 한쪽 이름을 필터로 조회하면 그 규칙 하나만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyRulesAndACaller, Searched]:
        return OnlyTheNamedRuleIsLeft()


@dataclass(frozen=True)
class ARuleTypeFilterNarrows(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-rule-type-filter-narrows-the-answer-to-that-kind"

    @override
    def describe(self) -> str:
        return "종류가 다른 규칙 둘 중 한쪽 종류를 필터로 조회하면 그 규칙 하나만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone(
            role=UserRole.SUPERADMIN, other_rule_type=NotificationRuleType.SESSION_TERMINATED
        )

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, Searched]:
        return SearchingByRuleType()

    @override
    def then(self) -> Then[ManyRulesAndACaller, Searched]:
        return OnlyTheNamedRuleIsLeft()


@dataclass(frozen=True)
class AnEnabledFilterNarrows(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-enabled-filter-leaves-only-the-enabled-rules"

    @override
    def describe(self) -> str:
        return "활성 규칙과 비활성 규칙이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return AnEnabledAndADisabledRule(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, Searched]:
        return SearchingTheEnabledOnes()

    @override
    def then(self) -> Then[ManyRulesAndACaller, Searched]:
        return TheLaidRulesAreLeft()


@dataclass(frozen=True)
class TheMonitorSearchesLikeTheSuperadmin(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-searches-rules-like-the-superadmin"

    @override
    def describe(self) -> str:
        return "모니터가 필터 없이 조회하면 슈퍼관리자와 같은 응답을 받는다"

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, Searched]:
        return SearchingEveryRule()

    @override
    def then(self) -> Then[ManyRulesAndACaller, Searched]:
        return TheLaidRulesAreLeft()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-rules"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 필터 없이 조회하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone()

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, Searched]:
        return SearchingEveryRule()

    @override
    def then(self) -> Then[ManyRulesAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryRule(),
    ANameFilterNarrows(),
    ARuleTypeFilterNarrows(),
    AnEnabledFilterNarrows(),
    TheMonitorSearchesLikeTheSuperadmin(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_rules(
    scenario: SearchingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
