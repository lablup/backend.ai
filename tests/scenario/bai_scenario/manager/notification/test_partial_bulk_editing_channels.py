"""채널 여럿 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.notification.request import (
    PartialBulkUpdateNotificationChannelItemInput,
    PartialBulkUpdateNotificationChannelsInput,
)
from ai.backend.common.dto.manager.v2.notification.response import NotificationChannelNode
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.notification import (
    ManyChannelsAndACaller,
    NothingIsProcessed,
    TheChannelsComeBack,
    TwoChannelsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Edited = PartialBulkPayload[NotificationChannelNode]
type EditingStep = Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, Edited]

NEW_DESCRIPTION = Says("한 번에 변경한 설명", english="the description changed all at once")


@dataclass(frozen=True)
class DescribingEveryOne(When[ManyChannelsAndACaller, NotificationAdapter, Edited]):
    """미리 만들어 둔 채널의 설명을 한 번에 같은 값으로 바꾼다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update_channels"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 채널 {len(laid.laid)}개의 설명을 한 번에 수정합니다",
            english=(
                f"{laid.caller.username} edits the description of {len(laid.laid)} channels at once"
            ),
        )

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller) -> Edited:
        request = PartialBulkUpdateNotificationChannelsInput(
            items=[
                PartialBulkUpdateNotificationChannelItemInput(
                    id=one.id, description=NEW_DESCRIPTION
                )
                for one in laid.laid
            ]
        )
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update_channels(request)


@dataclass(frozen=True)
class TheSuperadminDescribesSeveral(
    Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-describes-several-channels-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 채널 둘의 설명을 한 번에 변경하면, 둘 다 새 설명으로 오고 "
            "실패한 것은 없습니다",
            english=(
                "when the superadmin changes the description of two channels at once, "
                "both come back with the new description and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Edited]:
        return DescribingEveryOne()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Edited]:
        return TheChannelsComeBack(started=self.started, described=NEW_DESCRIPTION)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-channels"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 채널 여럿을 한 번에 수정하려 하면, 수정된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing edits several channels at once, nothing "
                "is edited and every one comes back in the failed list because "
                "permission is not enough"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone()

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Edited]:
        return DescribingEveryOne()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    TheSuperadminDescribesSeveral(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing_channels(
    scenario: EditingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
