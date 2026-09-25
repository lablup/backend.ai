"""채널 검증 — 시험 메시지를 그 채널로 보낸다. 보내는 자리는 대역이다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.request import (
    ValidateNotificationChannelInput,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    ValidateNotificationChannelPayload,
)
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.notification import NotificationChannelNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AChannelAndACaller,
    AChannelAndSomeone,
    TheValidatedChannelId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Validated = ValidateNotificationChannelPayload
type ValidatingStep = Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Any]

TEST_MESSAGE = "scenario test message"


@dataclass(frozen=True)
class Validating(When[AChannelAndACaller, NotificationAdapter, Validated]):
    """시험 메시지를 주고 채널을 검증한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "validate_channel"

    @override
    def describe(self, laid: AChannelAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else f"채널 {laid.channel.name}"
        return f"{laid.caller.username}이 {target}을 시험 메시지로 검증"

    @override
    async def call(self, adapter: NotificationAdapter, laid: AChannelAndACaller) -> Validated:
        with ActingAs(laid.caller):
            return await adapter.validate_channel(
                ValidateNotificationChannelInput(
                    id=uuid4() if self.unknown else laid.channel.id, test_message=TEST_MESSAGE
                )
            )


@dataclass(frozen=True)
class TheSuperadminValidatesAWebhookChannel(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-validates-a-webhook-channel"

    @override
    def describe(self) -> str:
        return "webhook 채널 하나가 있고 슈퍼관리자가 시험 메시지로 검증하면 검증한 채널의 id가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Validated]:
        return Validating()

    @override
    def then(self) -> Then[AChannelAndACaller, Validated]:
        return TheValidatedChannelId()


@dataclass(frozen=True)
class TheSuperadminValidatingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-validating-a-channel-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 검증하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Validated]:
        return Validating(unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, Validated]:
        return TheCallIsRefused(NotificationChannelNotFound)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotValidate(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-validate-a-channel"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 검증하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone()

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Validated]:
        return Validating()

    @override
    def then(self) -> Then[AChannelAndACaller, Validated]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[ValidatingStep] = [
    TheSuperadminValidatesAWebhookChannel(),
    TheSuperadminValidatingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotValidate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_validating_channels(
    scenario: ValidatingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
