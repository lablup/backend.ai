"""채널 조회 — 하나를 id로, 여럿을 한 번에. 어느 쪽이든 권한 검사를 거친다."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.response import NotificationChannelNode
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AChannelAndACaller,
    AChannelAndSomeone,
    EachItemIsRefused,
    LoadedChannels,
    ManyChannelsAndACaller,
    NothingComesBack,
    TheChannelNode,
    TheChannelsInTheOrderAsked,
    TwoChannelsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[SeedingSession, Any, NotificationAdapter, Any]


@dataclass(frozen=True)
class ReadingById(When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]):
    """id로 조회한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get_channel"

    @override
    def describe(self, laid: AChannelAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else f"채널 {laid.channel.name}"
        return f"{laid.caller.username}이 {target} 조회"

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: AChannelAndACaller
    ) -> NotificationChannelNode:
        with ActingAs(laid.caller):
            payload = await adapter.get_channel(uuid4() if self.unknown else laid.channel.id)
        return payload.item


@dataclass(frozen=True)
class ReadingManyByIds(When[ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]):
    """미리 만들어 둔 채널들의 id 뒤에 없는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_channels_by_ids"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return f"{laid.caller.username}이 미리 만들어 둔 {len(laid.laid)}개와 없는 id 하나를 한 번에 조회"

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller
    ) -> LoadedChannels:
        ids: Sequence[NotificationChannelID] = [
            *(one.id for one in laid.laid),
            NotificationChannelID(uuid4()),
        ]
        with ActingAs(laid.caller):
            return await adapter.batch_load_channels_by_ids(ids)


@dataclass(frozen=True)
class ReadingTheLaidByIds(When[ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]):
    """미리 만들어 둔 채널들만 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_channels_by_ids"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return f"{laid.caller.username}이 미리 만들어 둔 {len(laid.laid)}개를 한 번에 조회"

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller
    ) -> LoadedChannels:
        with ActingAs(laid.caller):
            return await adapter.batch_load_channels_by_ids([one.id for one in laid.laid])


@dataclass(frozen=True)
class ReadingNoIds(When[ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]):
    """빈 id 목록으로 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_channels_by_ids"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return f"{laid.caller.username}이 빈 id 목록으로 조회"

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller
    ) -> LoadedChannels:
        with ActingAs(laid.caller):
            return await adapter.batch_load_channels_by_ids([])


@dataclass(frozen=True)
class TheSuperadminReadsAChannel(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-channel-by-id"

    @override
    def describe(self) -> str:
        return "채널 하나가 있고 슈퍼관리자가 id로 조회하면, 그 채널 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheChannelNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-channel"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 id로 조회하면 권한 부족으로 거부된다. "
            "만든 사람으로 기록되어 있어도 같다"
        )

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone()

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheMonitorReadsAChannel(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-monitor-reads-a-channel-by-id"

    @override
    def describe(self) -> str:
        return (
            "모니터가 id로 조회하면 그 채널 전체가 반환된다. "
            "검색의 슈퍼관리자 검사와 같이 권한 검사도 읽기에 한해 모니터를 통과시킨다"
        )

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheChannelNode(started=self.started)


@dataclass(frozen=True)
class TheSuperadminReadingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reading-a-channel-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingReadingAnUnknownIdIsRefusedForPermission(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-an-unknown-channel-id-is-refused-for-permission"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 id로 조회하면 대상 없음이 아니라 권한 부족으로 "
            "거부된다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone()

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissing(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 미리 만들어 둔 채널 둘과 없는 id 하나를 한 번에 조회하면, "
            "요청한 순서대로 반환되고 없는 id에 해당하는 항목은 비어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]:
        return ReadingManyByIds()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, LoadedChannels]:
        return TheChannelsInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerItem(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-batch-loading-channels-is-refused-per-item"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 채널 둘을 한 번에 조회하면, "
            "호출은 거부되지 않고 항목마다 권한 부족 거부가 담긴다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone()

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]:
        return ReadingTheLaidByIds()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, LoadedChannels]:
        return EachItemIsRefused(asked=2)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    Scenario[SeedingSession, ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-channel-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return "빈 id 목록으로 조회하면 하위 계층을 부르지 않고 빈 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone()

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]:
        return ReadingNoIds()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, LoadedChannels]:
        return NothingComesBack()


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsAChannel(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    TheMonitorReadsAChannel(started=datetime.now(UTC)),
    TheSuperadminReadingAnUnknownIdIsNotFound(),
    AUserGrantedNothingReadingAnUnknownIdIsRefusedForPermission(),
    TheSuperadminLoadsLaidAndMissing(started=datetime.now(UTC)),
    AUserGrantedNothingIsRefusedPerItem(),
    ABatchLoadOfNothingAnswersNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_channels(
    scenario: ReadingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
