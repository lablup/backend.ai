"""규칙 수정 — 지정한 필드만 바뀌고, 종류와 채널은 바꿀 자리가 없다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.request import UpdateNotificationRuleInput
from ai.backend.common.dto.manager.v2.notification.response import NotificationRuleNode
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import ARuleAndACaller, ARuleAndSomeone, TheRuleNode
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type EditingStep = Scenario[
    SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode
]

WAS_DESCRIBED = "이미 있던 규칙"
NEW_TEMPLATE = "{{ session_id }} started"


@dataclass(frozen=True)
class Editing(When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]):
    """지정한 필드만 바꾼다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    named: str | None = None
    clear_description: bool = False
    message_template: str | None = None
    enabled: bool | None = None
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update_rule"

    @override
    def describe(self, laid: ARuleAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else f"규칙 {laid.rule.name}"
        changes: list[str] = []
        if self.named is not None:
            changes.append(f"이름을 {self.named}으로")
        if self.clear_description:
            changes.append("설명을 비움")
        if self.message_template is not None:
            changes.append("템플릿을 새것으로")
        if self.enabled is not None:
            changes.append(f"활성을 {self.enabled}로")
        what = ", ".join(changes) if changes else "아무것도 지정하지 않고"
        return f"{laid.caller.username}이 {target}을 {what} 수정"

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: ARuleAndACaller
    ) -> NotificationRuleNode:
        fields: dict[str, Any] = {}
        if self.named is not None:
            fields["name"] = self.named
        if self.clear_description:
            fields["description"] = None
        if self.message_template is not None:
            fields["message_template"] = self.message_template
        if self.enabled is not None:
            fields["enabled"] = self.enabled
        request = UpdateNotificationRuleInput(**fields)
        with ActingAs(laid.caller):
            payload = await adapter.update_rule(uuid4() if self.unknown else laid.rule.id, request)
        return payload.rule


@dataclass(frozen=True)
class TheSuperadminRenamesARule(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-renaming-a-rule-leaves-the-rest"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름만 바꾸면 이름은 새 값이고 나머지는 그대로인 규칙 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Editing(named="renamed")

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheRuleNode(started=self.started, named="renamed")


@dataclass(frozen=True)
class ChangingTheTemplate(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "changing-a-rule-template-answers-the-new-template"

    @override
    def describe(self) -> str:
        return "규칙의 템플릿을 바꾸면 템플릿이 새 값인 규칙이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Editing(message_template=NEW_TEMPLATE)

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheRuleNode(started=self.started, message_template=NEW_TEMPLATE)


@dataclass(frozen=True)
class ClearingTheDescription(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-a-rule-description-leaves-it-empty"

    @override
    def describe(self) -> str:
        return "설명이 있는 규칙의 설명을 비우면 설명이 비어 있는 규칙이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN, description=WAS_DESCRIBED)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Editing(clear_description=True)

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheRuleNode(started=self.started, described=None)


@dataclass(frozen=True)
class DisablingARule(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "disabling-a-rule-answers-it-disabled"

    @override
    def describe(self) -> str:
        return "활성 규칙을 비활성으로 바꾸면 비활성인 규칙이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Editing(enabled=False)

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheRuleNode(started=self.started, enabled=False)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-rule-edit-naming-no-field-changes-nothing"

    @override
    def describe(self) -> str:
        return "아무 필드도 지정하지 않고 수정하면 아무것도 바뀌지 않은 규칙이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Editing()

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheRuleNode(started=self.started)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-rule-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Editing(named="nowhere", unknown=True)

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-rule"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 이름을 바꾸려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone()

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return Editing(named="by-a-user")

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[EditingStep] = [
    TheSuperadminRenamesARule(started=datetime.now(UTC)),
    ChangingTheTemplate(started=datetime.now(UTC)),
    ClearingTheDescription(started=datetime.now(UTC)),
    DisablingARule(started=datetime.now(UTC)),
    AnEmptyEditChangesNothing(started=datetime.now(UTC)),
    TheSuperadminEditingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing_rules(
    scenario: EditingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
