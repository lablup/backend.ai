"""정책 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Language,
    Says,
    Scenario,
    Then,
    When,
    in_language,
)
from bai_scenario.components.resource_policy import (
    FAMILIES,
    EveryUnusedTargetIsProcessed,
    Family,
    NoTargetIsProcessed,
    SeveralPoliciesAndACaller,
    SeveralPoliciesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Edited = PartialBulkPayload[Any]
type EditingStep = Scenario[
    TestSeedingSession, SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Edited
]


@dataclass(frozen=True)
class EditingEveryTarget(When[SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Edited]):
    """대상 정책들에 같은 한도 수정을 한 번에 건다."""

    family: Family[Any, Any]

    @override
    def operation(self) -> str:
        return self.family.calls.partial_bulk_update

    @override
    def describe(self, laid: SeveralPoliciesAndACaller[Any]) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        edit = self.family.one_limit().says
        return Says(
            f"{laid.caller.username}이 {kind} {len(laid.targets)}개를 한 번에 수정합니다 ({edit})",
            english=(
                f"{laid.caller.username} updates {len(laid.targets)} policies of the {kind_en} "
                f"kind at once ({in_language(edit, Language.ENGLISH)})"
            ),
        )

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: SeveralPoliciesAndACaller[Any]
    ) -> Edited:
        ids: list[UUID] = [policy.uuid for policy in laid.targets]
        with ActingAs(laid.caller):
            return await self.family.partial_bulk_update(
                adapter, ids, self.family.one_limit().asked
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralPolicies(
    Scenario[TestSeedingSession, SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Edited]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"the-superadmin-edits-several-{self.family.label}s-at-once"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"superadmin 이 {kind} 여럿의 한도 하나를 한 번에 변경하면, 모두 그 한도만 새 값으로 "
            "오고 실패한 것은 없습니다",
            english=(
                f"when the superadmin changes one limit of several policies of the {kind_en} "
                "kind at once, they all come back with only that limit at the new value and "
                "nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SeveralPoliciesAndACaller[Any]]:
        return SeveralPoliciesAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Edited]:
        return EditingEveryTarget(self.family)

    @override
    def then(self) -> Then[SeveralPoliciesAndACaller[Any], Edited]:
        return EveryUnusedTargetIsProcessed(
            self.family, self.started, changed=self.family.one_limit().changed
        )


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Edited]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-granted-nothing-edits-none-of-several-{self.family.label}s"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"아무 권한도 받지 않은 사용자가 {kind} 여럿을 한 번에 수정하려 하면, 수정된 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                f"a user granted nothing trying to edit several policies of the {kind_en} kind "
                "at once gets none edited and every one in the failed list for not enough "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SeveralPoliciesAndACaller[Any]]:
        return SeveralPoliciesAndSomeone(self.family)

    @override
    def when(self) -> When[SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Edited]:
        return EditingEveryTarget(self.family)

    @override
    def then(self) -> Then[SeveralPoliciesAndACaller[Any], Edited]:
        return NoTargetIsProcessed(self.family, reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    *(TheSuperadminEditsSeveralPolicies(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(AUserGrantedNothingEditsNone(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
