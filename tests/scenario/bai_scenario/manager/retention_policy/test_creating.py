"""보존 정책 생성 — 카테고리마다 하나이고, 누가 생성할 수 있는가.

보존 일수가 하루보다 짧은 요청은 여기 없다. 요청 타입이 이미 막기 때문이다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.retention_policy import (
    APolicyAndACaller,
    APolicyAndSomeone,
    TheNewPolicyNode,
)
from bai_scenario.components.system import ENFORCEMENT, ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.request import CreateRetentionPolicyInput
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.retention import RetentionPolicyConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

DAYS = 90

type CreatingStep = Scenario[SeedingSession, Any, RetentionPolicyAdapter, RetentionPolicyNode]


@dataclass(frozen=True)
class Creating(When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]):
    """정책 하나를 생성한다. 응답에 담긴 노드를 꺼내서 준다."""

    category: RetentionCategory = RetentionCategory.SESSIONS
    enabled: bool = True

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACaller) -> str:
        state = "" if self.enabled else " 비활성으로"
        return f"{laid.caller.username}이 {self.category.value} 카테고리 정책을{state} 생성"

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ACaller) -> RetentionPolicyNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateRetentionPolicyInput(
                    category=self.category, retention_period_days=DAYS, enabled=self.enabled
                )
            )
        return payload.policy


@dataclass(frozen=True)
class CreatingTheLaidCategoryAgain(
    When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    """미리 만들어 둔 정책과 같은 카테고리로 다시 생성한다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: APolicyAndACaller) -> str:
        return f"{laid.caller.username}이 이미 있는 {laid.policy.category.value} 카테고리 정책을 다시 생성"

    @override
    async def call(
        self, adapter: RetentionPolicyAdapter, laid: APolicyAndACaller
    ) -> RetentionPolicyNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateRetentionPolicyInput(
                    category=laid.policy.category, retention_period_days=DAYS
                )
            )
        return payload.policy


@dataclass(frozen=True)
class TheSuperadminMakesOneNeverSwept(
    Scenario[SeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-policy-that-is-active-and-never-swept"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 카테고리와 보존 일수만 지정해 생성하면, 활성 여부는 참이고 마지막 정리 시각은 "
            "비어 있는 노드가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheNewPolicyNode(
            started=self.started, category=RetentionCategory.SESSIONS, days=DAYS
        )


@dataclass(frozen=True)
class AnInactiveOneIsMadeInactive(
    Scenario[SeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-policy-made-inactive-comes-back-inactive"

    @override
    def describe(self) -> str:
        return "활성 여부를 거짓으로 지정해 생성하면 비활성 상태가 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating(enabled=False)

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheNewPolicyNode(
            started=self.started, category=RetentionCategory.SESSIONS, days=DAYS, enabled=False
        )


@dataclass(frozen=True)
class EachCategoryIsAccepted(
    Scenario[SeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime
    category: RetentionCategory

    @override
    def summary(self) -> str:
        return f"a-policy-for-the-{self.category.value.replace('_', '-')}-category-is-made"

    @override
    def describe(self) -> str:
        return f"슈퍼관리자가 {self.category.value} 카테고리의 정책을 생성하면 그 카테고리가 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating(category=self.category)

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheNewPolicyNode(started=self.started, category=self.category, days=DAYS)


@dataclass(frozen=True)
class ASecondPolicyForACategoryIsRefused(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-second-policy-for-the-same-category-is-refused"

    @override
    def describe(self) -> str:
        return "어떤 카테고리의 정책이 이미 있을 때 같은 카테고리로 다시 생성하면, 카테고리 중복으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return CreatingTheLaidCategoryAgain()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(RetentionPolicyConflict)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[SeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-policy"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 정책을 생성하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheMonitorMayNotCreate(
    Scenario[SeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-create-a-policy"

    @override
    def describe(self) -> str:
        return "모니터 역할이 정책을 생성하면 역할 부족으로 거부된다. 모니터는 전역 역할 검사에서 읽기만 통과한다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[SeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-create-a-policy"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 꺼도 슈퍼관리자가 아니면 정책을 생성하지 못한다. "
            "생성은 권한 그래프가 아니라 역할로 보호되므로 스위치와 무관하다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesOneNeverSwept(started=datetime.now(UTC)),
    AnInactiveOneIsMadeInactive(started=datetime.now(UTC)),
    *(
        EachCategoryIsAccepted(started=datetime.now(UTC), category=category)
        for category in RetentionCategory
    ),
    ASecondPolicyForACategoryIsRefused(),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    TheMonitorMayNotCreate(),
    EnforcementOffStillNeedsTheSuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
