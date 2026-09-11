"""보존 정책 고치기 — 무엇이 바뀌고 무엇이 그대로 남으며, 누가 고칠 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.retention_policy import (
    APolicyAndACaller,
    APolicyAndSomeone,
    ManyPoliciesAndACaller,
    ThePolicyNode,
    TwoPoliciesAndSomeone,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.request import UpdateRetentionPolicyInput
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

LONGER = 180

type EditingStep = Scenario[SeedingSession, Any, RetentionPolicyAdapter, RetentionPolicyNode]


@dataclass(frozen=True)
class Editing(When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]):
    """심은 정책을 고친다. 답이 실은 노드를 벗겨서 준다."""

    days: int | None = None
    enabled: bool | None = None
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: APolicyAndACaller) -> str:
        target = "없는 id" if self.unknown else f"{laid.policy.category.value} 정책"
        changing = []
        if self.days is not None:
            changing.append("보존 일수")
        if self.enabled is not None:
            changing.append("활성 여부")
        return f"{laid.caller.username}이 {target}의 {' 및 '.join(changing) or '아무것도'} 고침"

    @override
    async def call(
        self, adapter: RetentionPolicyAdapter, laid: APolicyAndACaller
    ) -> RetentionPolicyNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateRetentionPolicyInput(
                    id=RetentionPolicyID(uuid4()) if self.unknown else laid.policy.id,
                    retention_period_days=self.days,
                    enabled=self.enabled,
                )
            )
        return payload.policy


@dataclass(frozen=True)
class MovingToATakenCategory(
    When[ManyPoliciesAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    """골라낸 하나의 카테고리를 옆에 있는 다른 정책의 카테고리로 바꾼다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        other = next(one for one in laid.laid if one.id != laid.named.id)
        return (
            f"{laid.caller.username}이 {laid.named.category.value} 정책의 카테고리를 "
            f"{other.category.value}로 고침"
        )

    @override
    async def call(
        self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller
    ) -> RetentionPolicyNode:
        other = next(one for one in laid.laid if one.id != laid.named.id)
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateRetentionPolicyInput(id=laid.named.id, category=other.category)
            )
        return payload.policy


@dataclass(frozen=True)
class TheDaysChangeAndTheRestStays(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "editing-the-retention-days-leaves-the-rest-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 보존 일수만 고치면, 일수는 새 값이 되고 카테고리와 활성 여부는 그대로 남는다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(days=LONGER)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started, days=LONGER)


@dataclass(frozen=True)
class DisablingIt(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "disabling-a-policy-answers-it-inactive"

    @override
    def describe(self) -> str:
        return "활성 정책의 활성 여부를 내리면 비활성 상태를 실은 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(enabled=False)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started, enabled=False)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-policy-edit-giving-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return "값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started)


@dataclass(frozen=True)
class MovingToATakenCategoryIsRefused(
    Scenario[SeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "moving-a-policy-to-a-category-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return (
            "정책 둘 중 한쪽의 카테고리를 다른 쪽 것으로 바꾸면, 카테고리가 겹친다는 이유로 거부된다. "
            "만들 때와 달리 저장소의 제약 위반이 그대로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return MovingToATakenCategory()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-policy-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무 정책도 갖지 않은 id를 고치면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(days=LONGER, unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-policy"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 정책을 고치면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(days=LONGER)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneEdit(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-edit-a-policy"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정책을 고친다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(days=LONGER)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started, days=LONGER)


SCENARIOS: list[EditingStep] = [
    TheDaysChangeAndTheRestStays(started=datetime.now(UTC)),
    DisablingIt(started=datetime.now(UTC)),
    AnEmptyEditChangesNothing(started=datetime.now(UTC)),
    MovingToATakenCategoryIsRefused(),
    TheSuperadminEditingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotEdit(),
    EnforcementOffLetsAnyoneEdit(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
