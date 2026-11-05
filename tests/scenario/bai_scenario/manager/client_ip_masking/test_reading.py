"""클라이언트 IP 마스킹 정책 여럿을 한 번에 조회."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.client_ip_masking.response import ClientIPMaskingPolicyNode
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.client_ip_masking.adapter import ClientIPMaskingAdapter
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
from bai_scenario.components.client_ip_masking import (
    ManyMaskingPoliciesAndACaller,
    TwoMaskingPoliciesAndSomeone,
)
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[ClientIPMaskingPolicyNode | Exception | None]
type ReadingStep = Scenario[
    TestSeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Loaded
]


@dataclass(frozen=True)
class LoadingTheLaidAndAMissingOne(
    When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Loaded]
):
    """미리 저장한 정책들의 id 뒤에 없는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyMaskingPoliciesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 정책 {len(laid.laid)}개와 없는 id 하나를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch-loads the {len(laid.laid)} policies created "
                "in advance and one unknown id"
            ),
        )

    @override
    async def call(
        self, adapter: ClientIPMaskingAdapter, laid: ManyMaskingPoliciesAndACaller
    ) -> Loaded:
        ids: list[ClientIPMaskingPolicyID] = [
            *(one.id for one in laid.laid),
            ClientIPMaskingPolicyID(uuid4()),
        ]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class LoadingAsNobody(When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Loaded]):
    """사용자 컨텍스트 없이 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyMaskingPoliciesAndACaller) -> str:
        return Says(
            f"사용자 컨텍스트 없이 정책 {len(laid.laid)}개를 한 번에 조회합니다",
            english=f"batch-loads {len(laid.laid)} policies without a user context",
        )

    @override
    async def call(
        self, adapter: ClientIPMaskingAdapter, laid: ManyMaskingPoliciesAndACaller
    ) -> Loaded:
        return await adapter.batch_load_by_ids([one.id for one in laid.laid])


@dataclass(frozen=True)
class TheyComeBackInTheOrderAsked(Then[ManyMaskingPoliciesAndACaller, Loaded]):
    """요청한 순서대로 한 항목씩 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다."""

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다",
            english="they come back in the order asked and the item for an unknown id is empty",
        )

    @override
    def look(
        self, laid: ManyMaskingPoliciesAndACaller, answered: Answered[Loaded]
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(UnreachableError, answered.raised)]
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        for i, policy in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if not isinstance(got, ClientIPMaskingPolicyNode):
                seen.append(Same(f"items[{i}]", got, Says("노드", english="a node")))
                continue
            seen += [
                Held[UUID](
                    f"items[{i}].id",
                    got.id,
                    SameAs(
                        policy.id,
                        Says("미리 저장한 정책", english="the policy created in advance"),
                    ),
                ),
                Held[UUID](
                    f"items[{i}].entity_id",
                    got.entity_id,
                    SameAs(
                        policy.id,
                        Says("미리 저장한 정책", english="the policy created in advance"),
                    ),
                ),
                Same(f"items[{i}].target_type", got.target_type.value, policy.target_type.value),
                Same(f"items[{i}].mode", got.mode.value, policy.mode.value),
                Same(f"items[{i}].ipv4_prefix", got.ipv4_prefix, policy.ipv4_prefix),
                Same(f"items[{i}].ipv6_prefix", got.ipv6_prefix, policy.ipv6_prefix),
                Held(f"items[{i}].created_at", got.created_at, WrittenByThisRun(self.started)),
                Held(f"items[{i}].updated_at", got.updated_at, WrittenByThisRun(self.started)),
            ]
        last = items[asked - 1] if len(items) >= asked else "none"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissing(
    Scenario[TestSeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 정책 둘과 없는 id 하나를 한 번에 조회하면, "
            "요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "when the superadmin batch-loads two policies created in advance and one "
                "unknown id, they come back in the order asked and the item for the unknown "
                "id is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyMaskingPoliciesAndACaller]:
        return TwoMaskingPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Loaded]:
        return LoadingTheLaidAndAMissingOne()

    @override
    def then(self) -> Then[ManyMaskingPoliciesAndACaller, Loaded]:
        return TheyComeBackInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class ABatchLoadCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "정책 둘이 있고 사용자 컨텍스트 없이 한 번에 조회하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when two policies exist and they are batch-loaded without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyMaskingPoliciesAndACaller]:
        return TwoMaskingPoliciesAndSomeone()

    @override
    def when(self) -> When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Loaded]:
        return LoadingAsNobody()

    @override
    def then(self) -> Then[ManyMaskingPoliciesAndACaller, Loaded]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[ReadingStep] = [
    TheSuperadminLoadsLaidAndMissing(started=datetime.now(UTC)),
    ABatchLoadCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep,
    adapter: ClientIPMaskingAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
