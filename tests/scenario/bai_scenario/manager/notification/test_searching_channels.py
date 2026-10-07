"""채널 검색 — 필터가 무엇을 좁히고, 누가 검색할 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationChannelFilter,
    NotificationChannelTypeFilter,
    SearchNotificationChannelsInput,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    SearchNotificationChannelsPayload,
)
from ai.backend.common.dto.manager.v2.notification.types import NotificationChannelTypeDTO
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AnEnabledAndADisabledChannel,
    AWebhookAndAnEmailChannel,
    ManyChannelsAndACaller,
    OnlyTheNamedChannelIsLeft,
    TheFirstChannelPage,
    TheLaidChannelsAreLeft,
    TwoChannelsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchNotificationChannelsPayload
type SearchingStep = Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryChannel(When[ManyChannelsAndACaller, NotificationAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search_channels"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_channels(SearchNotificationChannelsInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyChannelsAndACaller, NotificationAdapter, Searched]):
    """골라낸 하나의 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_channels"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return f"{laid.caller.username}이 이름 {laid.named.name} 필터로 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_channels(
                SearchNotificationChannelsInput(
                    filter=NotificationChannelFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class SearchingEmailChannels(When[ManyChannelsAndACaller, NotificationAdapter, Searched]):
    """email 종류만 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_channels"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return f"{laid.caller.username}이 email 종류 필터로 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_channels(
                SearchNotificationChannelsInput(
                    filter=NotificationChannelFilter(
                        channel_type=NotificationChannelTypeFilter(
                            equals=NotificationChannelTypeDTO.EMAIL
                        )
                    )
                )
            )


@dataclass(frozen=True)
class SearchingTheEnabledOnes(When[ManyChannelsAndACaller, NotificationAdapter, Searched]):
    """활성인 채널만 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_channels"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return f"{laid.caller.username}이 활성 필터로 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_channels(
                SearchNotificationChannelsInput(filter=NotificationChannelFilter(enabled=True))
            )


@dataclass(frozen=True)
class SearchingTheFirstOne(When[ManyChannelsAndACaller, NotificationAdapter, Searched]):
    """앞에서 한 건만 요청한다."""

    @override
    def operation(self) -> str:
        return "search_channels"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return f"{laid.caller.username}이 앞에서 한 건만 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_channels(SearchNotificationChannelsInput(first=1))


@dataclass(frozen=True)
class TheSuperadminCountsEveryChannel(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-channel-laid"

    @override
    def describe(self) -> str:
        return "채널 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Searched]:
        return SearchingEveryChannel()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Searched]:
        return TheLaidChannelsAreLeft()


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-that-channel"

    @override
    def describe(self) -> str:
        return "채널 둘 중 한쪽 이름을 필터로 조회하면 그 채널 하나만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Searched]:
        return OnlyTheNamedChannelIsLeft()


@dataclass(frozen=True)
class AChannelTypeFilterNarrows(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-channel-type-filter-narrows-the-answer-to-that-kind"

    @override
    def describe(self) -> str:
        return "webhook 채널과 email 채널이 있을 때 email 종류를 필터로 조회하면 email 채널 하나만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return AWebhookAndAnEmailChannel(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Searched]:
        return SearchingEmailChannels()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Searched]:
        return OnlyTheNamedChannelIsLeft()


@dataclass(frozen=True)
class AnEnabledFilterNarrows(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-enabled-filter-leaves-only-the-enabled-channels"

    @override
    def describe(self) -> str:
        return "활성 채널과 비활성 채널이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return AnEnabledAndADisabledChannel(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Searched]:
        return SearchingTheEnabledOnes()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Searched]:
        return TheLaidChannelsAreLeft()


@dataclass(frozen=True)
class TheFirstPageSaysThereIsMore(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "asking-for-the-first-channel-only-says-there-is-a-next-page"

    @override
    def describe(self) -> str:
        return "채널 둘이 있을 때 앞에서 한 건만 요청하면 한 건이 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Searched]:
        return SearchingTheFirstOne()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Searched]:
        return TheFirstChannelPage()


@dataclass(frozen=True)
class TheMonitorSearchesLikeTheSuperadmin(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-searches-channels-like-the-superadmin"

    @override
    def describe(self) -> str:
        return "모니터가 필터 없이 조회하면 슈퍼관리자와 같은 응답을 받는다"

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Searched]:
        return SearchingEveryChannel()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Searched]:
        return TheLaidChannelsAreLeft()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-channels"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 필터 없이 조회하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone()

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Searched]:
        return SearchingEveryChannel()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryChannel(),
    ANameFilterNarrows(),
    AChannelTypeFilterNarrows(),
    AnEnabledFilterNarrows(),
    TheFirstPageSaysThereIsMore(),
    TheMonitorSearchesLikeTheSuperadmin(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_channels(
    scenario: SearchingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
