"""보존 정책 생성 — 카테고리마다 하나이고, 누가 생성할 수 있는가.

보존 일수가 하루보다 짧은 요청은 여기 없다. 요청 타입이 이미 막기 때문이다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.request import CreateRetentionPolicyInput
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.retention import RetentionPolicyConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.retention_policy import (
    APolicyAndACaller,
    APolicyAndSomeone,
    TheNewPolicyNode,
)
from bai_scenario.components.system import ENFORCEMENT, ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

DAYS = 90

type CreatingStep = Scenario[TestSeedingSession, Any, RetentionPolicyAdapter, RetentionPolicyNode]


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
        if self.enabled:
            return Says(
                f"{laid.caller.username} 이 {self.category.value} 카테고리 정책을 생성합니다",
                english=(
                    f"{laid.caller.username} creates a policy for the {self.category.value} "
                    "category"
                ),
            )
        return Says(
            f"{laid.caller.username} 이 {self.category.value} 카테고리 정책을 비활성으로 생성합니다",
            english=(
                f"{laid.caller.username} creates an inactive policy for the "
                f"{self.category.value} category"
            ),
        )

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
        return Says(
            f"{laid.caller.username} 이 이미 있는 {laid.policy.category.value} 카테고리 정책을 "
            "다시 생성합니다",
            english=(
                f"{laid.caller.username} creates the policy of the {laid.policy.category.value} "
                "category again"
            ),
        )

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
    Scenario[TestSeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-policy-that-is-active-and-never-swept"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 카테고리와 보존 일수만 지정해 생성하면, 활성 여부는 참이고 마지막 "
            "정리 시각은 비어 있는 노드가 반환됩니다",
            english=(
                "when the superadmin creates a policy with only a category and retention days, "
                "the node comes back with enabled true and an empty last sweep time"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
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
    Scenario[TestSeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-policy-made-inactive-comes-back-inactive"

    @override
    def describe(self) -> str:
        return Says(
            "활성 여부를 거짓으로 지정해 생성하면 비활성 상태가 담긴 노드가 반환됩니다",
            english=("creating a policy with enabled false brings back a node that is not enabled"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
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
    Scenario[TestSeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime
    category: RetentionCategory

    @override
    def summary(self) -> str:
        return f"a-policy-for-the-{self.category.value.replace('_', '-')}-category-is-made"

    @override
    def describe(self) -> str:
        return Says(
            f"superadmin 이 {self.category.value} 카테고리의 정책을 생성하면 그 카테고리가 담긴 "
            "노드가 반환됩니다",
            english=(
                f"when the superadmin creates a policy of the {self.category.value} category, the "
                "node comes back with that category"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating(category=self.category)

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheNewPolicyNode(started=self.started, category=self.category, days=DAYS)


@dataclass(frozen=True)
class ASecondPolicyForACategoryIsRefused(
    Scenario[TestSeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-second-policy-for-the-same-category-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "어떤 카테고리의 정책이 이미 있을 때 같은 카테고리로 다시 생성하면, 카테고리 중복으로 "
            "거부됩니다",
            english=(
                "when a policy of a category already exists, creating it again for the same "
                "category is rejected as a duplicate"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return CreatingTheLaidCategoryAgain()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(RetentionPolicyConflict)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[TestSeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 정책을 생성하면 역할 부족으로 거부됩니다",
            english=(
                "a user who is not the superadmin creating a policy is rejected for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheMonitorMayNotCreate(
    Scenario[TestSeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-create-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "모니터 역할이 정책을 생성하면 역할 부족으로 거부됩니다. 모니터는 superadmin 검사에서 "
            "읽기만 통과합니다",
            english=(
                "a monitor role creating a policy is rejected for lack of role. A monitor passes "
                "the superadmin check for reads only"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, RetentionPolicyNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[TestSeedingSession, ACaller, RetentionPolicyAdapter, RetentionPolicyNode], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-create-a-policy"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 꺼도 superadmin 이 아니면 정책을 생성하지 못합니다",
            english=(
                "turning permission checks off still does not let a user who is not the "
                "superadmin create a policy"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
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
