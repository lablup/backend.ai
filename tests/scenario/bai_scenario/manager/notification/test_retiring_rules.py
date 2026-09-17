"""규칙 삭제 — 행을 지운다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.request import DeleteNotificationRuleInput
from ai.backend.common.dto.manager.v2.notification.response import DeleteNotificationRulePayload
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    ARuleAndACaller,
    ARuleAndSomeone,
    TheDeletedRuleId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = DeleteNotificationRulePayload
type RetiringStep = Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Any]


@dataclass(frozen=True)
class Deleting(When[ARuleAndACaller, NotificationAdapter, Deleted]):
    """규칙을 삭제한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "delete_rule"

    @override
    def describe(self, laid: ARuleAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else f"규칙 {laid.rule.name}"
        return f"{laid.caller.username}이 {target} 삭제"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ARuleAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.delete_rule(
                DeleteNotificationRuleInput(id=uuid4() if self.unknown else laid.rule.id)
            )


@dataclass(frozen=True)
class TheSuperadminDeletesARule(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-rule"

    @override
    def describe(self) -> str:
        return "규칙 하나가 있고 슈퍼관리자가 삭제하면 삭제한 규칙의 id가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[ARuleAndACaller, Deleted]:
        return TheDeletedRuleId()


@dataclass(frozen=True)
class TheSuperadminDeletingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deleting-a-rule-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Deleted]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[ARuleAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-rule"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 삭제하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone()

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[ARuleAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RetiringStep] = [
    TheSuperadminDeletesARule(),
    TheSuperadminDeletingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotDelete(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring_rules(
    scenario: RetiringStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
