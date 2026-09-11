"""보존 정책 지우기 — 지우기와 완전히 지우기가 같은 일을 하고, 누가 지울 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.retention_policy import (
    APolicyAndACaller,
    APolicyAndSomeone,
    TheDeletedPolicyId,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    DeleteRetentionPolicyPayload,
    PurgeRetentionPolicyPayload,
)
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type RetiringStep = Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, Any]


@dataclass(frozen=True)
class Deleting(When[APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload]):
    """심은 정책을 지운다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: APolicyAndACaller) -> str:
        target = "없는 id" if self.unknown else f"{laid.policy.category.value} 정책"
        return f"{laid.caller.username}이 {target}을 지움"

    @override
    async def call(
        self, adapter: RetentionPolicyAdapter, laid: APolicyAndACaller
    ) -> DeleteRetentionPolicyPayload:
        with ActingAs(laid.caller):
            return await adapter.delete(
                RetentionPolicyID(uuid4()) if self.unknown else laid.policy.id
            )


@dataclass(frozen=True)
class Purging(When[APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]):
    """심은 정책을 완전히 지운다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: APolicyAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.policy.category.value} 정책을 완전히 지움"

    @override
    async def call(
        self, adapter: RetentionPolicyAdapter, laid: APolicyAndACaller
    ) -> PurgeRetentionPolicyPayload:
        with ActingAs(laid.caller):
            return await adapter.purge(laid.policy.id)


@dataclass(frozen=True)
class TheSuperadminDeletesAPolicy(
    Scenario[
        SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-policy"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 정책을 지우면 지운 정책의 id를 실은 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload]:
        return Deleting()

    @override
    def then(self) -> Then[APolicyAndACaller, DeleteRetentionPolicyPayload]:
        return TheDeletedPolicyId()


@dataclass(frozen=True)
class PurgingIsTheSameHardDelete(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]
):
    @override
    def summary(self) -> str:
        return "purging-a-policy-answers-like-deleting-it"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 정책을 완전히 지우면 지우기와 같은 답이 온다. 둘 다 행을 없애고 soft delete는 없다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
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
        SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload
    ]
):
    @override
    def summary(self) -> str:
        return "deleting-a-policy-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무 정책도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller, DeleteRetentionPolicyPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[
        SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-policy"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 정책을 지우면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload]:
        return Deleting()

    @override
    def then(self) -> Then[APolicyAndACaller, DeleteRetentionPolicyPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-policy"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 정책을 완전히 지우면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, PurgeRetentionPolicyPayload]:
        return Purging()

    @override
    def then(self) -> Then[APolicyAndACaller, PurgeRetentionPolicyPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneDelete(
    Scenario[
        SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-delete-a-policy"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정책을 지운다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, DeleteRetentionPolicyPayload]:
        return Deleting()

    @override
    def then(self) -> Then[APolicyAndACaller, DeleteRetentionPolicyPayload]:
        return TheDeletedPolicyId()


SCENARIOS: list[RetiringStep] = [
    TheSuperadminDeletesAPolicy(),
    PurgingIsTheSameHardDelete(),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotDelete(),
    AUserGrantedNothingMayNotPurge(),
    EnforcementOffLetsAnyoneDelete(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
