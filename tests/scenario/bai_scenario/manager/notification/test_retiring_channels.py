"""채널 삭제 — 행을 지우고, 그 채널을 가리키는 규칙은 막지 않는다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.response import PurgeNotificationChannelPayload
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AChannelAndACaller,
    AChannelAndSomeone,
    AChannelARuleAndSomeone,
    TheDeletedChannelId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = PurgeNotificationChannelPayload
type RetiringStep = Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Any]


@dataclass(frozen=True)
class Deleting(When[AChannelAndACaller, NotificationAdapter, Deleted]):
    """채널을 삭제한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge_channel"

    @override
    def describe(self, laid: AChannelAndACaller) -> str:
        if self.unknown:
            target_ko = "존재하지 않는 id"
            target_en = "an unknown id"
        else:
            target_ko = f"채널 {laid.channel.name}"
            target_en = f"the channel {laid.channel.name}"
        return Says(
            f"{laid.caller.username}이 {target_ko} 삭제합니다",
            english=f"{laid.caller.username} deletes {target_en}",
        )

    @override
    async def call(self, adapter: NotificationAdapter, laid: AChannelAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.purge_channel(uuid4() if self.unknown else laid.channel.id)


@dataclass(frozen=True)
class TheSuperadminDeletesAChannel(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-channel"

    @override
    def describe(self) -> str:
        return Says(
            "채널 하나가 있고 superadmin 이 삭제하면 삭제한 채널의 id 가 반환됩니다",
            english=(
                "with one channel, when the superadmin deletes it, "
                "the id of the deleted channel comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[AChannelAndACaller, Deleted]:
        return TheDeletedChannelId()


@dataclass(frozen=True)
class AChannelARulePointsAtIsDeletedAllTheSame(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-channel-a-rule-points-at-is-deleted-all-the-same"

    @override
    def describe(self) -> str:
        return Says(
            "규칙이 가리키는 채널을 superadmin 이 삭제하면 차단되지 않고 삭제한 채널의 "
            "id 가 반환됩니다. 두 테이블 사이에 외래 키가 없어 규칙은 남습니다",
            english=(
                "when the superadmin deletes a channel a rule points at, it is deleted "
                "all the same and the id of the deleted channel comes back. There is no "
                "foreign key between the two tables, so the rule stays"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[AChannelAndACaller, Deleted]:
        return TheDeletedChannelId()


@dataclass(frozen=True)
class TheSuperadminDeletingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deleting-a-channel-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 를 삭제하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin deletes an id nothing answers to, "
                "it is rejected because no target is found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Deleted]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-channel"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 삭제하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing deletes a channel, "
                "it is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone()

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[AChannelAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RetiringStep] = [
    TheSuperadminDeletesAChannel(),
    AChannelARulePointsAtIsDeletedAllTheSame(),
    TheSuperadminDeletingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotDelete(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring_channels(
    scenario: RetiringStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
