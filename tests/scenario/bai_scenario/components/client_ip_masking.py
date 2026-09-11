"""What a client IP masking policy scenario table says besides the call.

A masking policy is the one row of its target and is created in no scope. A table needs
the caller, and the policy or policies the call reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.client_ip_masking.policy import SeedClientIPMaskingPolicy

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.client_ip_masking.response import (
    AdminSearchClientIPMaskingPoliciesPayload,
    ClientIPMaskingPolicyNode,
)
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
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

IPV4 = 24
IPV6 = 48
"""시드가 심는 정책의 접두 길이."""


@dataclass(frozen=True)
class AMaskingPolicyAndACaller:
    """정책 하나와, 그것을 부를 사람."""

    policy: ClientIPMaskingPolicyData
    caller: UserData


@dataclass(frozen=True)
class ManyMaskingPoliciesAndACaller:
    """훑을 정책 여럿과, 훑을 사람. ``laid``는 답에 나와야 하는 것만이고 ``named``는 그중 하나다."""

    laid: tuple[ClientIPMaskingPolicyData, ...]
    named: ClientIPMaskingPolicyData
    caller: UserData


@dataclass(frozen=True)
class AMaskingPolicyAndSomeone(Given[Any, AMaskingPolicyAndACaller]):
    """정책 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    target: ClientIPMaskingTarget = ClientIPMaskingTarget.DEFAULT
    mode: ClientIPMaskingMode = ClientIPMaskingMode.TRUNCATE

    @override
    def describe(self) -> str:
        return f"클라이언트 IP 마스킹 정책 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> AMaskingPolicyAndACaller:
        policy = await seeding.creating(
            SeedClientIPMaskingPolicy(
                target_type=self.target, mode=self.mode, ipv4_prefix=IPV4, ipv6_prefix=IPV6
            )
        )
        caller = await lay_a_caller(seeding, self.role)
        return AMaskingPolicyAndACaller(seeding.made(policy), seeding.made(caller))


@dataclass(frozen=True)
class TwoMaskingPoliciesAndSomeone(Given[Any, ManyMaskingPoliciesAndACaller]):
    """대상이 다른 정책 둘과 사용자 한 명. ``named``는 앞의 것이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"대상이 다른 클라이언트 IP 마스킹 정책 둘과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyMaskingPoliciesAndACaller:
        wanted = await seeding.creating(
            SeedClientIPMaskingPolicy(target_type=ClientIPMaskingTarget.DEFAULT)
        )
        other = await seeding.creating(
            SeedClientIPMaskingPolicy(target_type=ClientIPMaskingTarget.LOGIN_HISTORY)
        )
        caller = await lay_a_caller(seeding, self.role)
        return ManyMaskingPoliciesAndACaller(
            laid=(seeding.made(wanted), seeding.made(other)),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class MaskingPoliciesOfEveryTarget(Given[Any, ManyMaskingPoliciesAndACaller]):
    """세 대상의 정책과 사용자 한 명. ``named``는 기본값 대상의 것이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"세 대상의 클라이언트 IP 마스킹 정책과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyMaskingPoliciesAndACaller:
        laid = [
            await seeding.creating(SeedClientIPMaskingPolicy(target_type=target))
            for target in ClientIPMaskingTarget
        ]
        caller = await lay_a_caller(seeding, self.role)
        return ManyMaskingPoliciesAndACaller(
            laid=tuple(seeding.made(one) for one in laid),
            named=seeding.made(laid[0]),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class MaskingPoliciesOfMixedModes(Given[Any, ManyMaskingPoliciesAndACaller]):
    """자르는 정책 둘과 버리는 정책 하나, 사용자 한 명. ``laid``는 자르는 둘이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"모드가 다른 클라이언트 IP 마스킹 정책 셋과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyMaskingPoliciesAndACaller:
        truncating = [
            await seeding.creating(
                SeedClientIPMaskingPolicy(
                    target_type=ClientIPMaskingTarget.DEFAULT, mode=ClientIPMaskingMode.TRUNCATE
                )
            ),
            await seeding.creating(
                SeedClientIPMaskingPolicy(
                    target_type=ClientIPMaskingTarget.AUDIT_LOGS, mode=ClientIPMaskingMode.TRUNCATE
                )
            ),
        ]
        await seeding.creating(
            SeedClientIPMaskingPolicy(
                target_type=ClientIPMaskingTarget.LOGIN_HISTORY, mode=ClientIPMaskingMode.DROP
            )
        )
        caller = await lay_a_caller(seeding, self.role)
        return ManyMaskingPoliciesAndACaller(
            laid=tuple(seeding.made(one) for one in truncating),
            named=seeding.made(truncating[0]),
            caller=seeding.made(caller),
        )


def masking_verdicts(
    node: ClientIPMaskingPolicyNode,
    *,
    identity: Verdict,
    target: ClientIPMaskingTarget,
    mode: ClientIPMaskingMode,
    ipv4: int | None,
    ipv6: int | None,
    written: WrittenByThisRun,
) -> list[Verdict]:
    """Every place of one masking policy node. The id verdict is the caller's, since an
    upsert either makes a row or keeps one."""
    return [
        identity,
        Same("target_type", node.target_type.value, target.value),
        Same("mode", node.mode.value, mode.value),
        Same("ipv4_prefix", node.ipv4_prefix, ipv4),
        Same("ipv6_prefix", node.ipv6_prefix, ipv6),
        Held("created_at", node.created_at, written),
        Held("updated_at", node.updated_at, written),
    ]


@dataclass(frozen=True)
class TheNewMaskingPolicyNode(Then[Any, ClientIPMaskingPolicyNode]):
    """방금 넣은 정책이 통째로 온다. 요청이 정한 것만 여기로 받는다."""

    started: datetime
    target: ClientIPMaskingTarget
    mode: ClientIPMaskingMode
    ipv4: int | None
    ipv6: int | None

    @override
    def says(self) -> str:
        return "넣은 정책 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[ClientIPMaskingPolicyNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return masking_verdicts(
            node,
            identity=Skipped("id", "데이터베이스가 만든다"),
            target=self.target,
            mode=self.mode,
            ipv4=self.ipv4,
            ipv6=self.ipv6,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheSameRowRewritten(Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]):
    """심은 정책이 같은 id로, 준 값으로 통째로 바뀌어 온다."""

    started: datetime
    mode: ClientIPMaskingMode | Kept = KEPT
    ipv4: int | None | Kept = KEPT
    ipv6: int | None | Kept = KEPT

    @override
    def says(self) -> str:
        return "같은 id의 행이 준 값으로 바뀌어 온다"

    @override
    def look(
        self, laid: AMaskingPolicyAndACaller, answered: Answered[ClientIPMaskingPolicyNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seed = laid.policy
        return masking_verdicts(
            node,
            identity=Held[UUID]("id", node.id, SameAs[UUID](seed.id, "심은 정책")),
            target=seed.target_type,
            mode=seed.mode if isinstance(self.mode, Kept) else self.mode,
            ipv4=seed.ipv4_prefix if isinstance(self.ipv4, Kept) else self.ipv4,
            ipv6=seed.ipv6_prefix if isinstance(self.ipv6, Kept) else self.ipv6,
            written=WrittenByThisRun(self.started),
        )


@dataclass(frozen=True)
class TheLaidMaskingPoliciesAreLeft(
    Then[ManyMaskingPoliciesAndACaller, AdminSearchClientIPMaskingPoliciesPayload]
):
    """답에 나와야 하는 것들이 모두, 그리고 그것들만 남는다."""

    @override
    def says(self) -> str:
        return "답에 나와야 하는 정책만 남는다"

    @override
    def look(
        self,
        laid: ManyMaskingPoliciesAndACaller,
        answered: Answered[AdminSearchClientIPMaskingPoliciesPayload],
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.target_type.value for one in page.items),
                sorted(one.target_type.value for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedMaskingPolicyIsLeft(
    Then[ManyMaskingPoliciesAndACaller, AdminSearchClientIPMaskingPoliciesPayload]
):
    """걸러낸 그 하나만 남는다."""

    @override
    def says(self) -> str:
        return "걸러낸 그 정책 하나만 남는다"

    @override
    def look(
        self,
        laid: ManyMaskingPoliciesAndACaller,
        answered: Answered[AdminSearchClientIPMaskingPoliciesPayload],
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                [one.target_type.value for one in page.items],
                [laid.named.target_type.value],
            ),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheDeletedMaskingPolicy(Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]):
    """지운 정책이 통째로 온다. 값은 심은 것에서 읽는다."""

    started: datetime

    @override
    def says(self) -> str:
        return "지운 정책 전체가 온다"

    @override
    def look(
        self, laid: AMaskingPolicyAndACaller, answered: Answered[ClientIPMaskingPolicyNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seed = laid.policy
        return masking_verdicts(
            node,
            identity=Held[UUID]("id", node.id, SameAs[UUID](seed.id, "심은 정책")),
            target=seed.target_type,
            mode=seed.mode,
            ipv4=seed.ipv4_prefix,
            ipv6=seed.ipv6_prefix,
            written=WrittenByThisRun(self.started),
        )
