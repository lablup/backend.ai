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
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[TestSeedingSession, Any, NotificationAdapter, Any]


@dataclass(frozen=True)
class ReadingById(When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]):
    """id로 조회한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get_channel"

    @override
    def describe(self, laid: AChannelAndACaller) -> str:
        if self.unknown:
            target_ko = "존재하지 않는 id"
            target_en = "an unknown id"
        else:
            target_ko = f"채널 {laid.channel.name}"
            target_en = f"the channel {laid.channel.name}"
        return Says(
            f"{laid.caller.username}이 {target_ko} 조회합니다",
            english=f"{laid.caller.username} gets {target_en}",
        )

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
        return Says(
            f"{laid.caller.username}이 미리 저장한 {len(laid.laid)}개와 없는 id 하나를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch-loads the {len(laid.laid)} channels created "
                "in advance and one unknown id"
            ),
        )

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
        return Says(
            f"{laid.caller.username}이 미리 저장한 {len(laid.laid)}개를 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch-loads the {len(laid.laid)} channels "
                "created in advance"
            ),
        )

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
        return Says(
            f"{laid.caller.username}이 빈 id 목록으로 조회합니다",
            english=f"{laid.caller.username} batch-loads with an empty id list",
        )

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller
    ) -> LoadedChannels:
        with ActingAs(laid.caller):
            return await adapter.batch_load_channels_by_ids([])


@dataclass(frozen=True)
class TheSuperadminReadsAChannel(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-channel-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "채널 하나가 있고 superadmin 이 id 로 조회하면, 그 채널 전체가 응답으로 옵니다",
            english=(
                "with one channel, when the superadmin gets it by id, the whole channel comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheChannelNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-channel"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 id 로 조회하면 권한 부족으로 거부됩니다. "
            "채널의 만든 사람이 그 사용자여도 같습니다",
            english=(
                "when a user granted nothing gets a channel by id, it is rejected for "
                "not enough permission, even when the channel records that user as "
                "its creator"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone()

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheMonitorMayNotRead(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-read-a-channel-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "모니터가 id 로 조회하면 권한 부족으로 거부됩니다. "
            "검색은 통과하지만 id 조회는 권한 검사이고 모니터에게도 부여된 권한이 없습니다",
            english=(
                "when the monitor gets a channel by id, it is rejected for not enough "
                "permission. Search passes, but a get by id is a permission check and "
                "the monitor holds no permission for it either"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reading-a-channel-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 로 조회하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin gets an id nothing answers to, "
                "it is rejected because no target is found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingReadingAnUnknownIdIsRefusedForPermission(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-an-unknown-channel-id-is-refused-for-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 존재하지 않는 id 로 조회하면 대상 없음이 아니라 "
            "권한 부족으로 거부됩니다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 "
            "권한도 없기 때문입니다",
            english=(
                "when a user granted nothing gets an unknown id, it is rejected for not "
                "enough permission rather than for a missing target, because the "
                "permission check runs first and a missing row holds no grant either"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone()

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationChannelNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationChannelNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissing(
    Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 채널 둘과 없는 id 하나를 한 번에 조회하면, "
            "요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "when the superadmin batch-loads two channels created in advance and one "
                "unknown id, they come back in the order asked and the item for the "
                "unknown id is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]:
        return ReadingManyByIds()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, LoadedChannels]:
        return TheChannelsInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerItem(
    Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-batch-loading-channels-is-refused-per-item"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 채널 둘을 한 번에 조회하면, "
            "호출은 거부되지 않고 항목마다 권한 부족 거부가 담깁니다",
            english=(
                "when a user granted nothing batch-loads two channels, the call is not "
                "rejected and each item carries a rejection for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone()

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]:
        return ReadingTheLaidByIds()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, LoadedChannels]:
        return EachItemIsRefused(asked=2)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, LoadedChannels]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-channel-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return Says(
            "빈 id 목록으로 조회하면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다",
            english=(
                "a batch load with an empty id list brings an empty response without "
                "calling the lower layer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyChannelsAndACaller]:
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
    TheMonitorMayNotRead(),
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
