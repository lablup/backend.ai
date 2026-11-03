"""보존 정책 조회 — 다른 카탈로그와 달리 하나를 조회하는 것도 권한 검사를 거친다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.retention_policy import (
    APolicyAndACaller,
    APolicyAndSomeone,
    ThePolicyNode,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[
    TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode
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


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsAPolicy(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    TheSuperadminReadingAnUnknownIdIsNotFound(),
    AUserGrantedNothingReadingAnUnknownIdIsRefusedForPermission(),
    EnforcementOffLetsAnyoneRead(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
