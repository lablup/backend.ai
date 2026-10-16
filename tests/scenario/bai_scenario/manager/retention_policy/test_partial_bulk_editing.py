"""보존 정책 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    PartialBulkUpdateRetentionPoliciesInput,
    UpdateRetentionPolicyInput,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.retention_policy import (
    ManyPoliciesAndACaller,
    NothingIsProcessed,
    TwoPoliciesAndSomeone,
    policy_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

LONGER = 180

type Edited = PartialBulkPayload[RetentionPolicyNode]
type PolicyStep = Scenario[
    TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Edited
]


@dataclass(frozen=True)
class EditingEveryPolicy(When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Edited]):
    """미리 만들어 둔 정책들의 보존 일수를 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        return f"{laid.caller.username}이 정책 {len(laid.laid)}개의 보존 일수를 한 번에 수정"

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateRetentionPoliciesInput(
                    items=[
                        UpdateRetentionPolicyInput(id=policy.id, retention_period_days=LONGER)
                        for policy in laid.laid
                    ]
                )
            )


@dataclass(frozen=True)
class EveryPolicyIsEdited(Then[ManyPoliciesAndACaller, Edited]):
    """대상이 모두 새 보존 일수를 싣고 처리된 목록에 오고, 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "대상 정책이 모두 새 보존 일수로 오고, 실패한 것은 없다"

    @override
    def look(self, laid: ManyPoliciesAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.laid)),
            Same("failed", payload.failed, []),
        ]
        for node, policy in zip(payload.successes, laid.laid, strict=False):
            verdicts += policy_verdicts(
                node,
                category=policy.category,
                days=LONGER,
                enabled=policy.enabled,
                written=WrittenByThisRun(self.started),
            )
        return verdicts


@dataclass(frozen=True)
class TheSuperadminEditsSeveralPolicies(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-policies-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 정책 여럿의 보존 일수를 한 번에 바꾸면, 모두 새 일수로 오고 실패한 것은 없다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Edited]:
        return EditingEveryPolicy()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Edited]:
        return EveryPolicyIsEdited(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-policies"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 정책 여럿을 한 번에 수정하려 하면, 수정된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone()

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Edited]:
        return EditingEveryPolicy()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PolicyStep] = [
    TheSuperadminEditsSeveralPolicies(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: PolicyStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
