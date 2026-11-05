"""채널 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.notification.request import (
    PartialBulkPurgeNotificationChannelsInput,
)
from ai.backend.common.dto.manager.v2.notification.response import NotificationChannelNode
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    ManyChannelsAndACaller,
    NothingIsProcessed,
    TheChannelsComeBack,
    TwoChannelsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[NotificationChannelNode]
type PurgingStep = Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, Purged]


@dataclass(frozen=True)
class PurgingEveryOne(When[ManyChannelsAndACaller, NotificationAdapter, Purged]):
    """미리 만들어 둔 채널을 한 번에 purge 한다. ``missing``이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge_channels"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        besides_ko = "와 없는 id 하나" if self.missing is not None else ""
        besides_en = " and one unknown id" if self.missing is not None else ""
        return Says(
            f"{laid.caller.username}이 채널 {len(laid.laid)}개{besides_ko}를 한 번에 purge 합니다",
            english=(
                f"{laid.caller.username} purges {len(laid.laid)} channels{besides_en} at once"
            ),
        )

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller) -> Purged:
        ids: list[UUID] = [one.id for one in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge_channels(
                PartialBulkPurgeNotificationChannelsInput(ids=ids)
            )


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, Purged]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-channels-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 채널 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 삭제 전 모습으로 "
            "오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when the superadmin purges two channels and one unknown id at once, "
                "the two come back as they were before the purge and the unknown id "
                "comes back in the failed list because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Purged]:
        return PurgingEveryOne(missing=self.missing)

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Purged]:
        return TheChannelsComeBack(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-channels"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 채널 여럿을 한 번에 purge 하려 하면, 삭제된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing purges several channels at once, nothing "
                "is purged and every one comes back in the failed list because "
                "permission is not enough"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone()

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Purged]:
        return PurgingEveryOne()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Purged]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class PurgingChannelsAsNobody(When[ManyChannelsAndACaller, NotificationAdapter, Purged]):
    """사용자 컨텍스트 없이 한 번에 purge 한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_purge_channels"

    @override
    def describe(self, laid: ManyChannelsAndACaller) -> str:
        return Says(
            f"사용자 컨텍스트 없이 채널 {len(laid.laid)}개를 한 번에 purge 합니다",
            english=f"purges {len(laid.laid)} channels at once without a user context",
        )

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyChannelsAndACaller) -> Purged:
        return await adapter.partial_bulk_purge_channels(
            PartialBulkPurgeNotificationChannelsInput(ids=[one.id for one in laid.laid])
        )


@dataclass(frozen=True)
class APurgeCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, ManyChannelsAndACaller, NotificationAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-channel-purge-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "채널 둘이 있고 사용자 컨텍스트 없이 한 번에 purge 하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when two channels exist and they are purged at once without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyChannelsAndACaller]:
        return TwoChannelsAndSomeone()

    @override
    def when(self) -> When[ManyChannelsAndACaller, NotificationAdapter, Purged]:
        return PurgingChannelsAsNobody()

    @override
    def then(self) -> Then[ManyChannelsAndACaller, Purged]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
    APurgeCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging_channels(
    scenario: PurgingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
