"""보존 정책 완전 삭제 — 누가 완전 삭제할 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    PurgeRetentionPolicyPayload,
)
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.retention_policy import (
    APolicyAndACaller,
    APolicyAndSomeone,
    TheDeletedPolicyId,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RetiringStep = Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, Any]


@dataclass(frozen=True)
class Purging(When[APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]):
    """미리 만들어 둔 정책을 완전 삭제한다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge"

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
            f"{laid.caller.username} 이 {target_ko}"
            f"{' 를' if self.unknown else '을'} 영구 삭제합니다",
            english=f"{laid.caller.username} purges {target_en}",
        )

    @override
    async def call(
        self, adapter: RetentionPolicyAdapter, laid: APolicyAndACaller
    ) -> PurgeRetentionPolicyPayload:
        with ActingAs(laid.caller):
            return await adapter.purge(
                RetentionPolicyID(uuid4()) if self.unknown else laid.policy.id
            )


@dataclass(frozen=True)
class TheSuperadminPurgesAPolicy(
    Scenario[
        TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 정책을 영구 삭제하면 삭제한 정책의 id 를 담은 응답이 반환됩니다",
            english=(
                "when the superadmin purges a policy, the answer carries the id of the policy "
                "that was purged"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]:
        return Purging()

    @override
    def then(self) -> Then[APolicyAndACaller, PurgeRetentionPolicyPayload]:
        return TheDeletedPolicyId()


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[
        TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload
    ]
):
    @override
    def summary(self) -> str:
        return "purging-a-policy-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 를 영구 삭제하면 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when the superadmin purges an id nothing answers to, the call is rejected as "
                "not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller, PurgeRetentionPolicyPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[
        TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 정책을 영구 삭제하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing purges a policy, the call is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]:
        return Purging()

    @override
    def then(self) -> Then[APolicyAndACaller, PurgeRetentionPolicyPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyonePurge(
    Scenario[
        TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-purge-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 정책을 영구 삭제할 수 있습니다",
            english=("turning permission checks off lets a user granted nothing purge a policy"),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]:
        return Purging()

    @override
    def then(self) -> Then[APolicyAndACaller, PurgeRetentionPolicyPayload]:
        return TheDeletedPolicyId()


SCENARIOS: list[RetiringStep] = [
    TheSuperadminPurgesAPolicy(),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotPurge(),
    EnforcementOffLetsAnyonePurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
