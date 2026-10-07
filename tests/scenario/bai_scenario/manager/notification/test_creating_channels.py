"""채널 생성 — 누가 만들 수 있고, 무엇이 요청을 막는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.notification import NotificationChannelType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.request import (
    CreateNotificationChannelInput,
    EmailMessageInputDTO,
    EmailSpecInputDTO,
    NotificationChannelSpecInputDTO,
    SMTPAuthInputDTO,
    SMTPConnectionInputDTO,
    WebhookSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import NotificationChannelNode
from ai.backend.common.dto.manager.v2.notification.types import NotificationChannelTypeDTO
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.notification import InvalidNotificationSpec
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import TheNewChannelNode
from bai_scenario.components.system import ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.notification.channel import (
    FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    TO_EMAIL,
    WEBHOOK_URL,
)

type CreatingStep = Scenario[SeedingSession, ACaller, NotificationAdapter, NotificationChannelNode]


def spec_input(kind: NotificationChannelType | None) -> NotificationChannelSpecInputDTO:
    """The spec of that kind, or one naming neither when ``kind`` is None."""
    match kind:
        case NotificationChannelType.WEBHOOK:
            return NotificationChannelSpecInputDTO(webhook=WebhookSpecInputDTO(url=WEBHOOK_URL))
        case NotificationChannelType.EMAIL:
            return NotificationChannelSpecInputDTO(
                email=EmailSpecInputDTO(
                    smtp=SMTPConnectionInputDTO(host=SMTP_HOST, port=SMTP_PORT),
                    message=EmailMessageInputDTO(from_email=FROM_EMAIL, to_emails=[TO_EMAIL]),
                    auth=SMTPAuthInputDTO(username=SMTP_USERNAME, password=SMTP_PASSWORD),
                )
            )
        case None:
            return NotificationChannelSpecInputDTO()


@dataclass(frozen=True)
class Creating(When[ACaller, NotificationAdapter, NotificationChannelNode]):
    """채널을 만든다. 호출한 사용자가 만든 사람으로 기록된다.

    ``spec``은 명세의 종류다. None이면 webhook도 email도 없는 명세를 준다.
    """

    named: str
    channel_type: NotificationChannelTypeDTO = NotificationChannelTypeDTO.WEBHOOK
    spec: NotificationChannelType | None = NotificationChannelType.WEBHOOK
    enabled: bool = True

    @override
    def operation(self) -> str:
        return "create_channel"

    @override
    def describe(self, laid: ACaller) -> str:
        return f"{laid.caller.username}이 {self.channel_type.value} 채널 {self.named}을 생성"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ACaller) -> NotificationChannelNode:
        with ActingAs(laid.caller):
            payload = await adapter.create_channel(
                CreateNotificationChannelInput(
                    name=self.named,
                    channel_type=self.channel_type,
                    spec=spec_input(self.spec),
                    enabled=self.enabled,
                ),
                laid.caller.id,
            )
        return payload.channel


@dataclass(frozen=True)
class TheSuperadminMakesAWebhookChannel(
    Scenario[SeedingSession, ACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-webhook-channel"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 이름과 주소만 주고 webhook 채널을 만들면, "
            "활성 상태이고 설명이 비어 있는 채널 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, NotificationAdapter, NotificationChannelNode]:
        return Creating(named="alerts")

    @override
    def then(self) -> Then[ACaller, NotificationChannelNode]:
        return TheNewChannelNode(started=self.started, named="alerts")


@dataclass(frozen=True)
class TheSuperadminMakesAnEmailChannel(
    Scenario[SeedingSession, ACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-an-email-channel"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 SMTP 접속과 보내는 사람, 받는 사람, 인증 계정을 주고 email 채널을 만들면, "
            "인증 계정의 이름은 있고 비밀번호는 없는 채널 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, NotificationAdapter, NotificationChannelNode]:
        return Creating(
            named="mail",
            channel_type=NotificationChannelTypeDTO.EMAIL,
            spec=NotificationChannelType.EMAIL,
        )

    @override
    def then(self) -> Then[ACaller, NotificationChannelNode]:
        return TheNewChannelNode(
            started=self.started, named="mail", channel_type=NotificationChannelType.EMAIL
        )


@dataclass(frozen=True)
class ADisabledChannelIsMade(
    Scenario[SeedingSession, ACaller, NotificationAdapter, NotificationChannelNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-channel-made-disabled-answers-disabled"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 비활성으로 지정해 채널을 만들면 비활성인 채널이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, NotificationAdapter, NotificationChannelNode]:
        return Creating(named="muted", enabled=False)

    @override
    def then(self) -> Then[ACaller, NotificationChannelNode]:
        return TheNewChannelNode(started=self.started, named="muted", enabled=False)


@dataclass(frozen=True)
class ASpecNamingNeitherIsRefused(
    Scenario[SeedingSession, ACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "a-spec-naming-neither-webhook-nor-email-is-refused"

    @override
    def describe(self) -> str:
        return "webhook도 email도 주지 않은 명세로 만들려 하면 잘못된 입력으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, NotificationAdapter, NotificationChannelNode]:
        return Creating(named="empty", spec=None)

    @override
    def then(self) -> Then[ACaller, NotificationChannelNode]:
        return TheCallIsRefused(InvalidNotificationSpec)


@dataclass(frozen=True)
class ATypeAndSpecThatDisagreeAreRefused(
    Scenario[SeedingSession, ACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "a-channel-type-and-a-spec-that-disagree-are-refused"

    @override
    def describe(self) -> str:
        return (
            "email 종류라고 하면서 webhook 명세를 주고 만들려 하면, "
            "쓴 행을 읽어 돌려주는 자리에서 명세가 종류에 맞지 않아 거부되고 쓴 것은 되돌려진다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, NotificationAdapter, NotificationChannelNode]:
        return Creating(named="mismatched", channel_type=NotificationChannelTypeDTO.EMAIL)

    @override
    def then(self) -> Then[ACaller, NotificationChannelNode]:
        return TheCallIsRefused(BackendAISchemaValidationFailed)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[SeedingSession, ACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-make-a-channel"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 채널을 만들려 하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, NotificationAdapter, NotificationChannelNode]:
        return Creating(named="by-a-user")

    @override
    def then(self) -> Then[ACaller, NotificationChannelNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheMonitorMayNotCreate(
    Scenario[SeedingSession, ACaller, NotificationAdapter, NotificationChannelNode]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-make-a-channel"

    @override
    def describe(self) -> str:
        return "모니터가 채널을 만들려 하면 역할 부족으로 거부된다. 모니터는 읽기만 통과한다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ACaller, NotificationAdapter, NotificationChannelNode]:
        return Creating(named="by-the-monitor")

    @override
    def then(self) -> Then[ACaller, NotificationChannelNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesAWebhookChannel(started=datetime.now(UTC)),
    TheSuperadminMakesAnEmailChannel(started=datetime.now(UTC)),
    ADisabledChannelIsMade(started=datetime.now(UTC)),
    ASpecNamingNeitherIsRefused(),
    ATypeAndSpecThatDisagreeAreRefused(),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    TheMonitorMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating_channels(
    scenario: CreatingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
