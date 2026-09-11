"""마스킹 정책 삭제 — id로 지정해 누가 삭제할 수 있고, 권한 검사를 끄면 무엇이 허용되는가.

등록은 대상으로 행을 찾고 삭제는 id로 찾는다. 하나를 읽는 호출이 없어 id는 미리 만들어 둔 행에서
읽는다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.client_ip_masking import (
    AMaskingPolicyAndACaller,
    AMaskingPolicyAndSomeone,
    TheDeletedMaskingPolicy,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.client_ip_masking.response import ClientIPMaskingPolicyNode
from ai.backend.manager.api.adapters.client_ip_masking.adapter import ClientIPMaskingAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type RetiringStep = Scenario[
    SeedingSession, AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
]


@dataclass(frozen=True)
class Purging(When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]):
    """미리 만들어 둔 정책을 id로 삭제한다. 응답에 담긴 노드를 꺼내서 준다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: AMaskingPolicyAndACaller) -> str:
        target = (
            "존재하지 않는 id" if self.unknown else f"{laid.policy.target_type.value} 대상 정책"
        )
        return f"{laid.caller.username}이 {target} 삭제"

    @override
    async def call(
        self, adapter: ClientIPMaskingAdapter, laid: AMaskingPolicyAndACaller
    ) -> ClientIPMaskingPolicyNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_purge(
                ClientIPMaskingPolicyID(uuid4()) if self.unknown else laid.policy.id
            )
        return payload.policy


@dataclass(frozen=True)
class TheSuperadminPurgesAPolicy(
    Scenario[
        SeedingSession, AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-masking-policy"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 정책을 id로 삭제하면 삭제한 정책 전체를 담은 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AMaskingPolicyAndACaller]:
        return AMaskingPolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Purging()

    @override
    def then(self) -> Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]:
        return TheDeletedMaskingPolicy(started=self.started)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[
        SeedingSession, AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
    ]
):
    @override
    def summary(self) -> str:
        return "purging-a-masking-policy-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AMaskingPolicyAndACaller]:
        return AMaskingPolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[
        SeedingSession, AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-masking-policy"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 정책을 삭제하면 권한 부족으로 거부된다. 등록이 역할 부족으로 거부되는 것과는 다른 검사다"

    @override
    def given(self) -> Given[SeedingSession, AMaskingPolicyAndACaller]:
        return AMaskingPolicyAndSomeone()

    @override
    def when(
        self,
    ) -> When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Purging()

    @override
    def then(self) -> Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingPurgingAnUnknownIdIsRefusedForPermission(
    Scenario[
        SeedingSession, AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
    ]
):
    @override
    def summary(self) -> str:
        return (
            "a-user-granted-nothing-purging-an-unknown-masking-policy-id-is-refused-for-permission"
        )

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 id를 삭제하면 대상 없음이 아니라 권한 부족으로 "
            "거부된다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMaskingPolicyAndACaller]:
        return AMaskingPolicyAndSomeone()

    @override
    def when(
        self,
    ) -> When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyonePurge(
    Scenario[
        SeedingSession, AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
    ],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-purge-a-masking-policy"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 정책을 삭제할 수 있다. "
            "삭제는 등록과 달리 권한 그래프로 보호되므로 스위치가 영향을 준다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AMaskingPolicyAndACaller]:
        return AMaskingPolicyAndSomeone()

    @override
    def when(
        self,
    ) -> When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Purging()

    @override
    def then(self) -> Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]:
        return TheDeletedMaskingPolicy(started=self.started)


SCENARIOS: list[RetiringStep] = [
    TheSuperadminPurgesAPolicy(started=datetime.now(UTC)),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotPurge(),
    AUserGrantedNothingPurgingAnUnknownIdIsRefusedForPermission(),
    EnforcementOffLetsAnyonePurge(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: ClientIPMaskingAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
