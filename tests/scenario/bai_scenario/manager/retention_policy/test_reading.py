"""보존 정책 조회 — 다른 카탈로그와 달리 하나를 조회하는 것도 권한 검사를 거친다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Configured,
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
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.retention_policy import (
    APolicyAndACaller,
    APolicyAndSomeone,
    ManyPoliciesAndACaller,
    ThePolicyNode,
    TwoPoliciesAndSomeone,
    policy_verdicts,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[
    TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode
]
type Loaded = list[RetentionPolicyNode | Exception | None]
type LoadingStep = Scenario[
    TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Loaded
]


@dataclass(frozen=True)
class ReadingById(When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]):
    """id로 조회한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get"

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
        return Says(
            f"{laid.caller.username} 이 {target_ko}{' 를' if self.unknown else '을'} 조회합니다",
            english=f"{laid.caller.username} reads {target_en}",
        )

    @override
    async def call(
        self, adapter: RetentionPolicyAdapter, laid: APolicyAndACaller
    ) -> RetentionPolicyNode:
        with ActingAs(laid.caller):
            return await adapter.get(RetentionPolicyID(uuid4()) if self.unknown else laid.policy.id)


@dataclass(frozen=True)
class TheSuperadminReadsAPolicy(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-policy-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "정책 하나가 있고 superadmin 이 id 로 조회하면, 그 정책 전체가 반환됩니다",
            english=(
                "when one policy exists and the superadmin reads it by id, the whole policy "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 id 로 조회하면 권한 부족으로 거부됩니다. 인증만으로 "
            "조회되는 다른 카탈로그와 달리 이 조회는 권한 검사를 거칩니다",
            english=(
                "when a user granted nothing reads by id, the call is rejected for lack of "
                "permission. Unlike the other catalogs that a read reaches with authentication "
                "alone, this read goes through a permission check"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reading-a-policy-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 로 조회하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin reads with an id nothing answers to, the call is rejected "
                "as not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingReadingAnUnknownIdIsRefusedForPermission(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-an-unknown-policy-id-is-refused-for-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 존재하지 않는 id 로 조회하면 대상 없음이 아니라 권한 "
            "부족으로 거부됩니다. 권한 검사가 먼저 실행되고 없는 row 에는 부여된 권한도 없기 "
            "때문입니다",
            english=(
                "when a user granted nothing reads with an id nothing answers to, the call is "
                "rejected for lack of permission, not as not found, because the permission "
                "check runs first and no permission is granted on a row that does not exist"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneRead(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-read-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 정책을 조회할 수 있습니다",
            english=("turning permission checks off lets a user granted nothing read a policy"),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started)


@dataclass(frozen=True)
class LoadingTheLaidAndAMissingOne(When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Loaded]):
    """미리 만들어 둔 정책의 id 뒤에 없는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 만들어 둔 정책과 없는 id 하나를 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch-loads the policy created in advance and "
                "one unknown id"
            ),
        )

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller) -> Loaded:
        ids = [*(policy.id for policy in laid.laid), RetentionPolicyID(uuid4())]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class LoadingAsNobody(When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Loaded]):
    """사용자 컨텍스트 없이 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        return Says(
            f"사용자 컨텍스트 없이 정책 {len(laid.laid)}개를 한 번에 조회합니다",
            english=f"batch-loads {len(laid.laid)} policies without a user context",
        )

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller) -> Loaded:
        return await adapter.batch_load_by_ids([policy.id for policy in laid.laid])


@dataclass(frozen=True)
class TheyComeBackInTheOrderAsked(Then[ManyPoliciesAndACaller, Loaded]):
    """요청한 순서대로 한 항목씩 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다",
            english="they come back in the order asked and the item for an unknown id is empty",
        )

    @override
    def look(self, laid: ManyPoliciesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(UnreachableError, answered.raised)]
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        for i, policy in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if not isinstance(got, RetentionPolicyNode):
                seen.append(Same(f"items[{i}]", got, Says("노드", english="a node")))
                continue
            seen += [
                Held[UUID](
                    f"items[{i}].id",
                    got.id,
                    SameAs(
                        policy.id,
                        Says("미리 만들어 둔 정책의 id", english="the id of the policy laid"),
                    ),
                ),
                Held[UUID](
                    f"items[{i}].entity_id",
                    got.entity_id,
                    SameAs(
                        policy.id,
                        Says("미리 만들어 둔 정책의 id", english="the id of the policy laid"),
                    ),
                ),
            ]
            seen += policy_verdicts(
                got,
                category=policy.category,
                days=policy.retention_period.days,
                enabled=policy.enabled,
                written=WrittenByThisRun(self.started),
            )
        last = items[asked - 1] if len(items) >= asked else "none"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissing(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "정책이 있고 superadmin 이 그 정책과 없는 id 하나를 한 번에 조회하면, 요청한 "
            "순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "when one policy exists and the superadmin batch-loads it and one unknown id, "
                "they come back in the order asked and the item for the unknown id is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Loaded]:
        return LoadingTheLaidAndAMissingOne()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Loaded]:
        return TheyComeBackInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class ABatchLoadCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-policy-batch-load-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "정책이 있고 사용자 컨텍스트 없이 한 번에 조회하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when one policy exists and is batch-loaded without a user context, it is "
                "rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone()

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Loaded]:
        return LoadingAsNobody()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Loaded]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[ReadingStep | LoadingStep] = [
    TheSuperadminReadsAPolicy(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    TheSuperadminReadingAnUnknownIdIsNotFound(),
    AUserGrantedNothingReadingAnUnknownIdIsRefusedForPermission(),
    EnforcementOffLetsAnyoneRead(started=datetime.now(UTC)),
    TheSuperadminLoadsLaidAndMissing(started=datetime.now(UTC)),
    ABatchLoadCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
