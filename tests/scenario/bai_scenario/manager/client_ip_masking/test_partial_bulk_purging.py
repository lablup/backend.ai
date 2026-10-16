"""마스킹 정책 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    PartialBulkPurgeClientIPMaskingPoliciesInput,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.response import ClientIPMaskingPolicyNode
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.manager.api.adapters.client_ip_masking.adapter import ClientIPMaskingAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.client_ip_masking import (
    ManyMaskingPoliciesAndACaller,
    NoMaskingPolicyIsProcessed,
    TwoMaskingPoliciesAndSomeone,
    masking_verdicts,
)
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[ClientIPMaskingPolicyNode]
type PurgingStep = Scenario[
    TestSeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryPolicy(When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Purged]):
    """미리 만들어 둔 정책들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyMaskingPoliciesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 정책 {len(laid.laid)}개{besides}를 한 번에 purge 함"

    @override
    async def call(
        self, adapter: ClientIPMaskingAdapter, laid: ManyMaskingPoliciesAndACaller
    ) -> Purged:
        ids: list[UUID] = [policy.id for policy in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeClientIPMaskingPoliciesInput(ids=ids)
            )


@dataclass(frozen=True)
class EveryPolicyIsPurged(Then[ManyMaskingPoliciesAndACaller, Purged]):
    """정책이 모두 지워지기 전 모습으로 처리된 목록에 오고, 없는 id 만 실패 목록에 온다."""

    started: datetime
    missing: UUID

    @override
    def says(self) -> str:
        return "정책이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"

    @override
    def look(
        self, laid: ManyMaskingPoliciesAndACaller, answered: Answered[Purged]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.laid)),
        ]
        for node, policy in zip(payload.successes, laid.laid, strict=False):
            verdicts += masking_verdicts(
                node,
                identity=Held[UUID]("id", node.id, SameAs[UUID](policy.id, "미리 만들어 둔 정책")),
                target=policy.target_type,
                mode=policy.mode,
                ipv4=policy.ipv4_prefix,
                ipv6=policy.ipv6_prefix,
                written=WrittenByThisRun(self.started),
            )
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Purged]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-masking-policies-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 정책 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 처리된 목록에 오고 "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyMaskingPoliciesAndACaller]:
        return TwoMaskingPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Purged]:
        return PurgingEveryPolicy(missing=self.missing)

    @override
    def then(self) -> Then[ManyMaskingPoliciesAndACaller, Purged]:
        return EveryPolicyIsPurged(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-masking-policies"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 정책 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyMaskingPoliciesAndACaller]:
        return TwoMaskingPoliciesAndSomeone()

    @override
    def when(self) -> When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Purged]:
        return PurgingEveryPolicy()

    @override
    def then(self) -> Then[ManyMaskingPoliciesAndACaller, Purged]:
        return NoMaskingPolicyIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: ClientIPMaskingAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
