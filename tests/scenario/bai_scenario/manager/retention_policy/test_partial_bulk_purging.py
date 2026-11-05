"""보존 정책 여럿 완전 삭제."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    PartialBulkPurgeRetentionPoliciesInput,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.components.retention_policy import (
    ManyPoliciesAndACaller,
    NothingIsProcessed,
    TwoPoliciesAndSomeone,
    policy_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[RetentionPolicyNode]
type PolicyStep = Scenario[
    TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryPolicy(When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged]):
    """미리 만들어 둔 정책들을 한 번에 완전 삭제한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        besides_ko = "와 없는 id 하나" if self.missing is not None else ""
        besides_en = " and one missing id" if self.missing is not None else ""
        return Says(
            f"{laid.caller.username} 이 정책 {len(laid.laid)}개{besides_ko}를 한 번에 영구 "
            "삭제합니다",
            english=(
                f"{laid.caller.username} purges {len(laid.laid)} policies{besides_en} at once"
            ),
        )

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller) -> Purged:
        ids = [policy.id for policy in laid.laid]
        if self.missing is not None:
            ids.append(RetentionPolicyID(self.missing))
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeRetentionPoliciesInput(ids=ids))


@dataclass(frozen=True)
class EveryPolicyIsPurged(Then[ManyPoliciesAndACaller, Purged]):
    """대상이 모두 지워지기 전 모습으로 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return Says(
                "대상 정책이 모두 처리된 목록에 오고, 실패한 것은 없습니다",
                english=("every target policy comes back in the processed list and nothing failed"),
            )
        return Says(
            "대상 정책이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 "
            "옵니다",
            english=(
                "every target policy comes back in the processed list, and the missing id comes "
                "back in the failed list because nothing answers to it"
            ),
        )

    @override
    def look(self, laid: ManyPoliciesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for node, policy in zip(payload.successes, laid.laid, strict=False):
            verdicts += policy_verdicts(
                node,
                category=policy.category,
                days=policy.retention_period.days,
                enabled=policy.enabled,
                written=WrittenByThisRun(self.started),
            )
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the missing id put in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-policies-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 정책 둘과 없는 id 하나를 한 번에 영구 삭제하면, 둘은 처리된 목록에 "
            "오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when the superadmin purges two policies and one missing id at once, the two "
                "come back in the processed list and the missing id comes back in the failed "
                "list because nothing answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged]:
        return PurgingEveryPolicy(missing=self.missing)

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Purged]:
        return EveryPolicyIsPurged(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-policies"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 정책 여럿을 한 번에 영구 삭제하려 하면, 삭제된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to purge several policies at once, none is "
                "deleted and every one comes back in the failed list because the user has no "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone()

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged]:
        return PurgingEveryPolicy()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Purged]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class PurgingPoliciesAsNobody(When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged]):
    """사용자 컨텍스트 없이 한 번에 완전 삭제한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        return Says(
            f"사용자 컨텍스트 없이 정책 {len(laid.laid)}개를 한 번에 영구 삭제합니다",
            english=f"purges {len(laid.laid)} policies at once without a user context",
        )

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller) -> Purged:
        return await adapter.partial_bulk_purge(
            PartialBulkPurgeRetentionPoliciesInput(ids=[one.id for one in laid.laid])
        )


@dataclass(frozen=True)
class APurgeCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-policy-purge-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "정책 둘이 있고 사용자 컨텍스트 없이 한 번에 영구 삭제하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when two policies exist and are purged at once without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone()

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Purged]:
        return PurgingPoliciesAsNobody()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Purged]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[PolicyStep] = [
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
    APurgeCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PolicyStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
