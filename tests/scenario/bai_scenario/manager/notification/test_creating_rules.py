"""규칙 생성 — 채널을 id로 가리키며, 그 채널이 있는지는 보지 않는다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.request import CreateNotificationRuleInput
from ai.backend.common.dto.manager.v2.notification.response import NotificationRuleNode
from ai.backend.common.dto.manager.v2.notification.types import NotificationRuleTypeDTO
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AChannelAndACaller,
    AChannelAndSomeone,
    TheNewRuleNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.notification.rule import TEMPLATE

type CreatingStep = Scenario[
    SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationRuleNode
]


@dataclass(frozen=True)
class Creating(When[AChannelAndACaller, NotificationAdapter, NotificationRuleNode]):
    """규칙을 만든다. 채널을 대지 않으면 미리 만들어 둔 채널을 가리킨다.

    ``channel_id``는 미리 만들어 둔 채널 대신 가리킬 id다.
    """

    named: str
    channel_id: UUID | None = None
    enabled: bool = True

    @override
    def operation(self) -> str:
        return "create_rule"

    @override
    def describe(self, laid: AChannelAndACaller) -> str:
        target = "없는 채널 id" if self.channel_id is not None else f"채널 {laid.channel.name}"
        return f"{laid.caller.username}이 {target}를 가리키는 규칙 {self.named}을 생성"

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: AChannelAndACaller
    ) -> NotificationRuleNode:
        with ActingAs(laid.caller):
            payload = await adapter.create_rule(
                CreateNotificationRuleInput(
                    name=self.named,
                    rule_type=NotificationRuleTypeDTO.SESSION_STARTED,
                    channel_id=laid.channel.id if self.channel_id is None else self.channel_id,
                    message_template=TEMPLATE,
                    enabled=self.enabled,
                ),
                laid.caller.id,
            )
        return payload.rule


@dataclass(frozen=True)
class TheSuperadminMakesARule(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-rule-through-a-channel"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 종류와 채널과 템플릿을 주고 규칙을 만들면, "
            "활성 상태이고 설명이 비어 있는 규칙 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Creating(named="on-start")

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationRuleNode]:
        return TheNewRuleNode(started=self.started, named="on-start")


@dataclass(frozen=True)
class ADisabledRuleIsMade(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-rule-made-disabled-answers-disabled"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 비활성으로 지정해 규칙을 만들면 비활성인 규칙이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Creating(named="muted", enabled=False)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationRuleNode]:
        return TheNewRuleNode(started=self.started, named="muted", enabled=False)


@dataclass(frozen=True)
class ARulePointingAtNoChannelIsMade(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime
    orphan: UUID

    @override
    def summary(self) -> str:
        return "a-rule-pointing-at-a-channel-id-nothing-answers-to-is-made-all-the-same"

    @override
    def describe(self) -> str:
        return (
            "어느 행에도 없는 채널 id를 가리켜 규칙을 만들면 막히지 않고 그대로 만들어진다. "
            "두 테이블 사이에 외래 키가 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Creating(named="orphan", channel_id=self.orphan)

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationRuleNode]:
        return TheNewRuleNode(started=self.started, named="orphan", channel_id=self.orphan)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationRuleNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-make-a-rule"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 규칙을 만들려 하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone()

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Creating(named="by-a-user")

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationRuleNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheMonitorMayNotCreate(
    Scenario[SeedingSession, AChannelAndACaller, NotificationAdapter, NotificationRuleNode]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-make-a-rule"

    @override
    def describe(self) -> str:
        return "모니터가 규칙을 만들려 하면 역할 부족으로 거부된다. 모니터는 읽기만 통과한다"

    @override
    def given(self) -> Given[SeedingSession, AChannelAndACaller]:
        return AChannelAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[AChannelAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Creating(named="by-the-monitor")

    @override
    def then(self) -> Then[AChannelAndACaller, NotificationRuleNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesARule(started=datetime.now(UTC)),
    ADisabledRuleIsMade(started=datetime.now(UTC)),
    ARulePointingAtNoChannelIsMade(started=datetime.now(UTC), orphan=uuid4()),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    TheMonitorMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating_rules(
    scenario: CreatingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
