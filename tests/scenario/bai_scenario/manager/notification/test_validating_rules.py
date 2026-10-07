"""규칙 검증 — 시험 데이터를 형식에 맞춰 검사하고 템플릿을 그려 채널로 보낸다. 보내는 자리는 대역이다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.request import ValidateNotificationRuleInput
from ai.backend.common.dto.manager.v2.notification.response import (
    ValidateNotificationRulePayload,
)
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.notification import (
    NotificationChannelNotFound,
    NotificationRuleNotFound,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    AnOrphanRuleAndSomeone,
    ARuleAndACaller,
    ARuleAndSomeone,
    TheRenderedMessage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Validated = ValidateNotificationRulePayload
type ValidatingStep = Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Any]

SESSION_STARTED_DATA: Mapping[str, Any] = {
    "session_id": "sess-1",
    "session_name": "train",
    "session_type": "interactive",
    "cluster_mode": "single-node",
    "status": "running",
}
"""시험 데이터. 템플릿이 읽는 자리는 이름과 상태다."""

RENDERED = "Session train is running"


@dataclass(frozen=True)
class Validating(When[ARuleAndACaller, NotificationAdapter, Validated]):
    """시험 데이터를 주고 규칙을 검증한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "validate_rule"

    @override
    def describe(self, laid: ARuleAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else f"규칙 {laid.rule.name}"
        return f"{laid.caller.username}이 {target}을 시험 데이터로 검증"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ARuleAndACaller) -> Validated:
        with ActingAs(laid.caller):
            return await adapter.validate_rule(
                ValidateNotificationRuleInput(
                    id=uuid4() if self.unknown else laid.rule.id,
                    notification_data=dict(SESSION_STARTED_DATA),
                )
            )


@dataclass(frozen=True)
class TheSuperadminValidatesARule(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-validates-a-rule-with-test-data"

    @override
    def describe(self) -> str:
        return (
            "세션 시작 규칙 하나가 있고 슈퍼관리자가 그 종류에 맞는 시험 데이터로 검증하면, "
            "템플릿에 데이터를 넣어 만든 문자열이 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Validated]:
        return Validating()

    @override
    def then(self) -> Then[ARuleAndACaller, Validated]:
        return TheRenderedMessage(rendered=RENDERED)


@dataclass(frozen=True)
class ARuleWhoseChannelIsGoneIsRefused(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "a-rule-pointing-at-a-channel-id-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return "없는 채널 id를 가리키는 규칙을 검증하면 채널을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return AnOrphanRuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Validated]:
        return Validating()

    @override
    def then(self) -> Then[ARuleAndACaller, Validated]:
        return TheCallIsRefused(NotificationChannelNotFound)


@dataclass(frozen=True)
class TheSuperadminValidatingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-validating-a-rule-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 검증하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Validated]:
        return Validating(unknown=True)

    @override
    def then(self) -> Then[ARuleAndACaller, Validated]:
        return TheCallIsRefused(NotificationRuleNotFound)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotValidate(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Validated]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-validate-a-rule"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 검증하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone()

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Validated]:
        return Validating()

    @override
    def then(self) -> Then[ARuleAndACaller, Validated]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[ValidatingStep] = [
    TheSuperadminValidatesARule(),
    ARuleWhoseChannelIsGoneIsRefused(),
    TheSuperadminValidatingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotValidate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_validating_rules(
    scenario: ValidatingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
