"""채널 삭제 — 행을 지우고, 그 채널을 가리키는 규칙은 막지 않는다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.request import DeleteNotificationChannelInput
from ai.backend.common.dto.manager.v2.notification.response import (
    DeleteNotificationChannelPayload,
)
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AChannelAndACaller,
    AChannelAndSomeone,
    AChannelARuleAndSomeone,
    TheDeletedChannelId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = DeleteNotificationChannelPayload
type RetiringStep = Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Any]


@dataclass(frozen=True)
class Deleting(When[AChannelAndACaller, NotificationAdapter, Deleted]):
    """채널을 삭제한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "delete_channel"

    @override
    def describe(self, laid: AChannelAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else f"채널 {laid.channel.name}"
        return f"{laid.caller.username}이 {target} 삭제"

    @override
    async def call(self, adapter: NotificationAdapter, laid: AChannelAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.delete_channel(
                DeleteNotificationChannelInput(id=uuid4() if self.unknown else laid.channel.id)
            )


@dataclass(frozen=True)
class TheSuperadminDeletesAChannel(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-channel"

    @override
    def describe(self) -> str:
        return "채널 하나가 있고 슈퍼관리자가 삭제하면 삭제한 채널의 id가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[AChannelAndACaller, Deleted]:
        return TheDeletedChannelId()


@dataclass(frozen=True)
class AChannelARulePointsAtIsDeletedAllTheSame(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-channel-a-rule-points-at-is-deleted-all-the-same"

    @override
    def describe(self) -> str:
        return (
            "규칙이 가리키는 채널을 슈퍼관리자가 삭제하면 막히지 않고 삭제한 채널의 id가 반환된다. "
            "두 테이블 사이에 외래 키가 없어 규칙은 남는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[AChannelAndACaller, Deleted]:
        return TheDeletedChannelId()


@dataclass(frozen=True)
class TheSuperadminDeletingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deleting-a-channel-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Deleted]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-channel"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 삭제하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
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
