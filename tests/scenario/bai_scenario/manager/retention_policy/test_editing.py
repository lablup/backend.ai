"""보존 정책 수정 — 무엇이 바뀌고 무엇이 그대로 남으며, 누가 수정할 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.request import UpdateRetentionPolicyInput
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

LONGER = 180

type EditingStep = Scenario[TestSeedingSession, Any, RetentionPolicyAdapter, RetentionPolicyNode]


@dataclass(frozen=True)
class Editing(When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]):
    """미리 만들어 둔 정책을 수정한다. 응답에 담긴 노드를 꺼내서 준다."""

    days: int | None = None
    enabled: bool | None = None
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: APolicyAndACaller) -> str:
        target_ko = (
            "존재하지 않는 id" if self.unknown else f"{laid.policy.category.value} 카테고리 정책"
        )
        target_en = (
            "an id nothing answers to"
            if self.unknown
            else f"the policy of the {laid.policy.category.value} category"
        )
        changing_ko = []
        changing_en = []
        if self.days is not None:
            changing_ko.append("보존 일수")
            changing_en.append("retention days")
        if self.enabled is not None:
            changing_ko.append("활성 여부")
            changing_en.append("enabled flag")
        if not changing_ko:
            return Says(
                f"{laid.caller.username} 이 {target_ko}에서 값을 지정하지 않고 수정합니다",
                english=f"{laid.caller.username} edits {target_en} without giving a value",
            )
        return Says(
            f"{laid.caller.username} 이 {target_ko}의 {' 및 '.join(changing_ko)} 변경을 요청합니다",
            english=(
                f"{laid.caller.username} edits the {' and '.join(changing_en)} of {target_en}"
            ),
        )

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
    """골라낸 하나의 카테고리를 함께 만들어 둔 다른 정책의 카테고리로 바꾼다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        other = next(one for one in laid.laid if one.id != laid.named.id)
        return Says(
            f"{laid.caller.username} 이 {laid.named.category.value} 카테고리 정책의 카테고리를 "
            f"{other.category.value} 로 수정합니다",
            english=(
                f"{laid.caller.username} changes the category of the "
                f"{laid.named.category.value} policy to {other.category.value}"
            ),
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
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "editing-the-retention-days-leaves-the-rest-alone"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 보존 일수만 수정하면, 일수는 새 값이 되고 카테고리와 활성 여부는 "
            "그대로 유지됩니다",
            english=(
                "when the superadmin edits only the retention days, the days become the new "
                "value and the category and enabled flag stay"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(days=LONGER)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started, days=LONGER)


@dataclass(frozen=True)
class DisablingIt(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "disabling-a-policy-answers-it-inactive"

    @override
    def describe(self) -> str:
        return Says(
            "활성 정책의 활성 여부를 끄면 비활성 상태가 담긴 노드가 반환됩니다",
            english=(
                "turning off the enabled flag of an active policy brings back a node that is "
                "not enabled"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(enabled=False)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started, enabled=False)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-policy-edit-giving-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환됩니다",
            english=("editing without giving any value brings back a node that changed nothing"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started)


@dataclass(frozen=True)
class MovingToATakenCategoryIsRefused(
    Scenario[
        TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, RetentionPolicyNode
    ]
):
    @override
    def summary(self) -> str:
        return "moving-a-policy-to-a-category-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "정책 둘 중 한쪽의 카테고리를 다른 쪽 카테고리로 바꾸면, 카테고리 중복으로 거부됩니다. "
            "생성할 때와 달리 저장소의 제약 위반이 그대로 전파됩니다",
            english=(
                "when the category of one of two policies is changed to the category of the "
                "other, the call is rejected as a duplicate. Unlike at creation, the constraint "
                "violation from the repository propagates as it is"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return MovingToATakenCategory()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-policy-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin edits an id nothing answers to, the call is rejected as "
                "not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(days=LONGER, unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 정책을 수정하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing edits a policy, the call is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Editing(days=LONGER)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneEdit(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-edit-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 정책을 수정할 수 있습니다",
            english=("turning permission checks off lets a user granted nothing edit a policy"),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
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
