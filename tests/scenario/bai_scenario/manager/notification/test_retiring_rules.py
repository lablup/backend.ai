"""규칙 삭제 — 행을 지운다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.response import PurgeNotificationRulePayload
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    ARuleAndACaller,
    ARuleAndSomeone,
    TheDeletedRuleId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = PurgeNotificationRulePayload
type RetiringStep = Scenario[TestSeedingSession, ARuleAndACaller, NotificationAdapter, Any]


@dataclass(frozen=True)
class Deleting(When[ARuleAndACaller, NotificationAdapter, Deleted]):
    """규칙을 삭제한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge_rule"

    @override
    def describe(self, laid: ARuleAndACaller) -> str:
        if self.unknown:
            target_ko = "존재하지 않는 id"
            target_en = "an unknown id"
        else:
            target_ko = f"규칙 {laid.rule.name}"
            target_en = f"the rule {laid.rule.name}"
        return Says(
            f"{laid.caller.username}이 {target_ko} 삭제합니다",
            english=f"{laid.caller.username} deletes {target_en}",
        )

    @override
    async def call(self, adapter: NotificationAdapter, laid: ARuleAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.purge_rule(uuid4() if self.unknown else laid.rule.id)


@dataclass(frozen=True)
class TheSuperadminDeletesARule(
    Scenario[TestSeedingSession, ARuleAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-rule"

    @override
    def describe(self) -> str:
        return Says(
            "규칙 하나가 있고 superadmin 이 삭제하면 삭제한 규칙의 id 가 반환됩니다",
            english=(
                "with one rule, when the superadmin deletes it, "
                "the id of the deleted rule comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[ARuleAndACaller, Deleted]:
        return TheDeletedRuleId()


@dataclass(frozen=True)
class TheSuperadminDeletingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, ARuleAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deleting-a-rule-id-nothing-answers-to-is-not-found"

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
    def given(self) -> Given[TestSeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, Deleted]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[ARuleAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[TestSeedingSession, ARuleAndACaller, NotificationAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-rule"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 삭제하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing deletes a rule, "
                "it is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARuleAndACaller]:
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
