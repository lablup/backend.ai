"""정책 여럿 삭제하기 — 정책마다 따로 지우고, 지우지 못한 것은 이유와 함께 답한다."""

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
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.resource_policy import (
    FAMILIES,
    EveryUnusedTargetIsProcessed,
    Family,
    NoTargetIsProcessed,
    OnlyTheHeldOneFails,
    SeveralPoliciesAndACaller,
    SeveralPoliciesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[Any]
type PurgingStep = Scenario[
    TestSeedingSession, SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryTarget(When[SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Purged]):
    """대상 정책들을 한 번에 삭제한다. ``missing``이 있으면 그 id 도 함께 넣는다."""

    family: Family[Any, Any]
    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return self.family.calls.partial_bulk_purge

    @override
    def describe(self, laid: SeveralPoliciesAndACaller[Any]) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return (
            f"{laid.caller.username}이 {self.family.kind} {len(laid.targets)}개{besides}를 "
            "한 번에 삭제"
        )

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: SeveralPoliciesAndACaller[Any]
    ) -> Purged:
        ids: list[UUID] = [policy.uuid for policy in laid.targets]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await self.family.partial_bulk_purge(adapter, ids)


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Purged]
):
    family: Family[Any, Any]
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return f"purging-several-{self.family.label}s-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 아무도 사용하지 않는 {self.family.kind} 둘과 없는 id 하나를 한 번에 "
            "삭제하면, 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, SeveralPoliciesAndACaller[Any]]:
        return SeveralPoliciesAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Purged]:
        return PurgingEveryTarget(self.family, missing=self.missing)

    @override
    def then(self) -> Then[SeveralPoliciesAndACaller[Any], Purged]:
        return EveryUnusedTargetIsProcessed(self.family, self.started, missing=self.missing)


@dataclass(frozen=True)
class AHeldPolicyIsAnsweredFor(
    Scenario[TestSeedingSession, SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Purged]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"purging-several-{self.family.label}s-answers-for-the-one-still-held"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 아직 할당된 {self.family.kind}과 아무도 사용하지 않는 것을 한 번에 "
            "삭제하면, 사용하지 않는 것은 처리된 목록에 오고 할당된 것은 아직 참조 중이라는 "
            "이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, SeveralPoliciesAndACaller[Any]]:
        return SeveralPoliciesAndSomeone(
            self.family, role=UserRole.SUPERADMIN, unused=1, with_held=True
        )

    @override
    def when(self) -> When[SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Purged]:
        return PurgingEveryTarget(self.family)

    @override
    def then(self) -> Then[SeveralPoliciesAndACaller[Any], Purged]:
        return OnlyTheHeldOneFails(self.family, self.started, reason="Foreign key")


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Purged]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-granted-nothing-purges-none-of-several-{self.family.label}s"

    @override
    def describe(self) -> str:
        return (
            f"아무 권한도 받지 않은 사용자가 {self.family.kind} 여럿을 한 번에 삭제하려 하면, "
            "삭제된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, SeveralPoliciesAndACaller[Any]]:
        return SeveralPoliciesAndSomeone(self.family)

    @override
    def when(self) -> When[SeveralPoliciesAndACaller[Any], ResourcePolicyAdapter, Purged]:
        return PurgingEveryTarget(self.family)

    @override
    def then(self) -> Then[SeveralPoliciesAndACaller[Any], Purged]:
        return NoTargetIsProcessed(self.family, reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    *(PurgingAnswersForTheMissingOne(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(AHeldPolicyIsAnsweredFor(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(AUserGrantedNothingPurgesNone(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
