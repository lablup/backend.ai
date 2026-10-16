"""What a fair share scenario table says besides the call.

A fair share weight is written against a resource group, so a role sitting on the group
is how a user other than the superadmin reaches it. A table needs the group, the domains
whose weights the call writes, and the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertDomainFairShareWeightPayload,
    DomainFairShareNode,
)
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.resource_group import SomeoneGrantedOnTheGroup
from bai_scenario.components.system import role_named
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.resource_group.resource_group import TestSeedResourceGroup

WEIGHT = Decimal("2.5")


@dataclass(frozen=True)
class DomainsInAGroupAndACaller:
    """리소스 그룹 하나, 가중치를 정할 도메인들, 그리고 호출할 사용자. 첫 도메인이 호출자의 집이다."""

    group: ResourceGroupData
    domains: tuple[DomainData, ...]
    caller: UserData


@dataclass(frozen=True)
class DomainsInAGroupAndSomeone(Given[Any, DomainsInAGroupAndACaller]):
    """그룹 하나와 도메인 ``1 + besides``개, 사용자 한 명. ``granted``를 주면 그 그룹에 앉힌 역할로 그 권한을 받는다."""

    role: UserRole = UserRole.USER
    granted: Permission | None = None
    besides: int = 0

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        if self.granted is not None:
            who = f"그 그룹 범위의 {self.granted.name} 역할을 받은 {who}"
        return f"리소스 그룹 하나와 도메인 {1 + self.besides}개, 그리고 {who} 한 명"

    @override
    async def lay(self, seeding: Any) -> DomainsInAGroupAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        others = [
            await seeding.creating(TestSeedDomain(name_hint="other", description=WAS_HERE))
            for _ in range(self.besides)
        ]
        group = await seeding.creating(TestSeedResourceGroup())
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        if self.granted is not None:
            await seeding.within(SomeoneGrantedOnTheGroup(group, caller, self.granted))
        return DomainsInAGroupAndACaller(
            group=seeding.made(group),
            domains=tuple(seeding.made(domain) for domain in (home, *others)),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheDomainWeight(Then[DomainsInAGroupAndACaller, DomainFairShareNode]):
    """첫 도메인의 기록이 정한 가중치를 싣고 온다. 나머지 설정은 그룹 기본값이다."""

    started: datetime

    @override
    def says(self) -> str:
        return "정한 가중치를 실은 기록이 오고, 나머지 설정은 그룹 기본값이다"

    @override
    def look(
        self, laid: DomainsInAGroupAndACaller, answered: Answered[DomainFairShareNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("raised", answered.raised, None)]
        spec = node.spec
        snapshot = node.calculation_snapshot
        written = WrittenByThisRun(self.started)
        return [
            Skipped("id", "데이터베이스가 만든다"),
            Same("resource_group_name", node.resource_group_name, laid.group.name),
            Same("domain_name", node.domain_name, laid.domains[0].name),
            Same("spec.weight", spec.weight, WEIGHT),
            Same("spec.uses_default", spec.uses_default, False),
            Same("spec.half_life_days", spec.half_life_days, 7),
            Same("spec.lookback_days", spec.lookback_days, 28),
            Same("spec.decay_unit_days", spec.decay_unit_days, 1),
            Same("spec.resource_weights", list(spec.resource_weights), []),
            Same("calculation_snapshot.fair_share_factor", snapshot.fair_share_factor, Decimal(1)),
            Same(
                "calculation_snapshot.total_decayed_usage",
                list(snapshot.total_decayed_usage.entries),
                [],
            ),
            Same("calculation_snapshot.normalized_usage", snapshot.normalized_usage, Decimal(0)),
            Skipped("calculation_snapshot.lookback_start", "쓴 날짜에 따라 달라진다"),
            Skipped("calculation_snapshot.lookback_end", "쓴 날짜에 따라 달라진다"),
            Held("calculation_snapshot.last_calculated_at", snapshot.last_calculated_at, written),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class EveryWeightIsWritten(Then[DomainsInAGroupAndACaller, BulkUpsertDomainFairShareWeightPayload]):
    """도메인마다 가중치가 정해지고 그 개수가 온다."""

    @override
    def says(self) -> str:
        return "도메인 수만큼 정했다는 개수가 온다"

    @override
    def look(
        self,
        laid: DomainsInAGroupAndACaller,
        answered: Answered[BulkUpsertDomainFairShareWeightPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        return [Same("upserted_count", payload.upserted_count, len(laid.domains))]
