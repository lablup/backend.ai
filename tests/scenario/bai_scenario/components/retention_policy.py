"""What a retention policy scenario table says besides the call.

A policy is the one row of its category and is created in no scope. A table needs the
caller, and the policy or policies the call reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.retention_policy.retention_policy import SeedRetentionPolicy

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    RetentionPolicyNode,
    SearchRetentionPoliciesPayload,
)
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)

KEPT_DAYS = 30
"""시드가 심는 정책의 보존 일수."""


@dataclass(frozen=True)
class APolicyAndACaller:
    """정책 하나와, 그것을 부를 사람."""

    policy: RetentionPolicyData
    caller: UserData


@dataclass(frozen=True)
class ManyPoliciesAndACaller:
    """훑을 정책 여럿과, 훑을 사람. ``laid``는 답에 나와야 하는 것만이고 ``named``는 그중 하나다."""

    laid: tuple[RetentionPolicyData, ...]
    named: RetentionPolicyData
    caller: UserData


@dataclass(frozen=True)
class APolicyAndSomeone(Given[Any, APolicyAndACaller]):
    """정책 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    category: RetentionCategory = RetentionCategory.LOGS
    enabled: bool = True

    @override
    def describe(self) -> str:
        return f"보존 정책 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller:
        policy = await seeding.creating(
            SeedRetentionPolicy(
                category=self.category, retention_days=KEPT_DAYS, enabled=self.enabled
            )
        )
        caller = await lay_a_caller(seeding, self.role)
        return APolicyAndACaller(seeding.made(policy), seeding.made(caller))


@dataclass(frozen=True)
class TwoPoliciesAndSomeone(Given[Any, ManyPoliciesAndACaller]):
    """카테고리가 다른 정책 둘과 사용자 한 명. ``named``는 앞의 것이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"카테고리가 다른 보존 정책 둘과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPoliciesAndACaller:
        wanted = await seeding.creating(SeedRetentionPolicy(category=RetentionCategory.LOGS))
        other = await seeding.creating(SeedRetentionPolicy(category=RetentionCategory.LOGIN))
        caller = await lay_a_caller(seeding, self.role)
        return ManyPoliciesAndACaller(
            laid=(seeding.made(wanted), seeding.made(other)),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AnActiveAndAnInactivePolicy(Given[Any, ManyPoliciesAndACaller]):
    """활성 정책 하나와 비활성 정책 하나, 사용자 한 명. ``laid``는 활성인 것뿐이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"활성 보존 정책 하나와 비활성 하나, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPoliciesAndACaller:
        active = await seeding.creating(SeedRetentionPolicy(category=RetentionCategory.LOGS))
        await seeding.creating(SeedRetentionPolicy(category=RetentionCategory.LOGIN, enabled=False))
        caller = await lay_a_caller(seeding, self.role)
        return ManyPoliciesAndACaller(
            laid=(seeding.made(active),),
            named=seeding.made(active),
            caller=seeding.made(caller),
        )


def policy_verdicts(
    node: RetentionPolicyNode,
    *,
    category: RetentionCategory,
    days: int,
    enabled: bool,
    written: WrittenByThisRun,
) -> list[Verdict]:
    """Every place of one policy node."""
    return [
        Skipped("id", "데이터베이스가 만든다"),
        Same("category", node.category, category),
        Same("retention_period_days", node.retention_period_days, days),
        Same("enabled", node.enabled, enabled),
        Same("last_swept_at", node.last_swept_at, None),
        Held("created_at", node.created_at, written),
        Held("updated_at", node.updated_at, written),
    ]


@dataclass(frozen=True)
class TheNewPolicyNode(Then[Any, RetentionPolicyNode]):
    """방금 만든 정책이 통째로 온다. 요청이 정한 것만 여기로 받는다."""

    started: datetime
    category: RetentionCategory
    days: int
    enabled: bool = True

    @override
    def says(self) -> str:
        return "만든 정책 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[RetentionPolicyNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return policy_verdicts(
            node,
            category=self.category,
            days=self.days,
            enabled=self.enabled,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class ThePolicyNode(Then[APolicyAndACaller, RetentionPolicyNode]):
    """심은 정책이 통째로 온다. 바꾸는 요청은 바뀌어야 하는 자리만 인자로 준다."""

    started: datetime
    days: int | Kept = KEPT
    enabled: bool | Kept = KEPT

    @override
    def says(self) -> str:
        return "심은 정책 전체가 온다"

    @override
    def look(
        self, laid: APolicyAndACaller, answered: Answered[RetentionPolicyNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seed = laid.policy
        return policy_verdicts(
            node,
            category=seed.category,
            days=seed.retention_period.days if isinstance(self.days, Kept) else self.days,
            enabled=seed.enabled if isinstance(self.enabled, Kept) else self.enabled,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheLaidPoliciesAreLeft(Then[ManyPoliciesAndACaller, SearchRetentionPoliciesPayload]):
    """답에 나와야 하는 것들이 모두, 그리고 그것들만 남는다."""

    @override
    def says(self) -> str:
        return "답에 나와야 하는 정책만 남는다"

    @override
    def look(
        self, laid: ManyPoliciesAndACaller, answered: Answered[SearchRetentionPoliciesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.category.value for one in page.items),
                sorted(one.category.value for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedPolicyIsLeft(Then[ManyPoliciesAndACaller, SearchRetentionPoliciesPayload]):
    """걸러낸 그 하나만 남는다."""

    @override
    def says(self) -> str:
        return "걸러낸 그 정책 하나만 남는다"

    @override
    def look(
        self, laid: ManyPoliciesAndACaller, answered: Answered[SearchRetentionPoliciesPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("items", [one.category.value for one in page.items], [laid.named.category.value]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheDeletedPolicyId(Then[APolicyAndACaller, Any]):
    """지운 정책의 id를 실은 답. 지우기와 완전히 지우기가 같은 모양으로 답한다."""

    @override
    def says(self) -> str:
        return "지운 정책의 id가 온다"

    @override
    def look(self, laid: APolicyAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Held[UUID]("id", payload.id, SameAs[UUID](laid.policy.id, "심은 정책"))]
