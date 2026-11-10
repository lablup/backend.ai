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
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AChannelAndACaller,
    AChannelAndSomeone,
    TheValidatedChannelId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Validated = ValidateNotificationChannelPayload
type ValidatingStep = Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Any]

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
        if self.unknown:
            target_ko = "존재하지 않는 id"
            target_en = "an unknown id"
        else:
            target_ko = f"채널 {laid.channel.name}"
            target_en = f"the channel {laid.channel.name}"
        return Says(
            f"{laid.caller.username}이 {target_ko} 를 시험 메시지로 검증합니다",
            english=(f"{laid.caller.username} validates {target_en} with a test message"),
        )

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
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-validates-a-webhook-channel"

    @override
    def describe(self) -> str:
        return Says(
            "webhook 채널 하나가 있고 superadmin 이 시험 메시지로 검증하면 "
            "검증한 채널의 id 가 반환됩니다",
            english=(
                "with one webhook channel, when the superadmin validates it with a "
                "test message, the id of the validated channel comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Validated]:
        return Validating()

    @override
    def then(self) -> Then[AChannelAndACaller, Validated]:
        return TheValidatedChannelId()


@dataclass(frozen=True)
class TheSuperadminValidatingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-validating-a-channel-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 를 검증하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin validates an id nothing answers to, "
                "it is rejected because no target is found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, Validated]:
        return Validating(unknown=True)

    @override
    def then(self) -> Then[AChannelAndACaller, Validated]:
        return TheCallIsRefused(NotificationChannelNotFound)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotValidate(
    Scenario[TestSeedingSession, AChannelAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-validate-a-channel"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 검증하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing validates a channel, "
                "it is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AChannelAndACaller]:
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
