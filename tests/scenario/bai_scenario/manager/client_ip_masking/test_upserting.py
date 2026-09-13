"""마스킹 정책 등록 — 대상마다 하나이고, 등록은 있던 행을 통째로 바꾸며, 누가 등록할 수 있는가.

접두 길이가 범위를 벗어나는 요청은 여기 없다. 요청 타입이 이미 막기 때문이다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.client_ip_masking import (
    IPV4,
    IPV6,
    AMaskingPolicyAndACaller,
    AMaskingPolicyAndSomeone,
    TheNewMaskingPolicyNode,
    TheSameRowRewritten,
)
from bai_scenario.components.system import ENFORCEMENT, ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminUpsertClientIPMaskingPolicyInput,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.response import ClientIPMaskingPolicyNode
from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
    ClientIPMaskingMode as ModeInput,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
    ClientIPMaskingTarget as TargetInput,
)
from ai.backend.manager.api.adapters.client_ip_masking.adapter import ClientIPMaskingAdapter
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type UpsertingStep = Scenario[
    SeedingSession, Any, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
]


@dataclass(frozen=True)
class Upserting(When[ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]):
    """한 대상에 정책을 등록한다. 응답에 담긴 노드를 꺼내서 준다."""

    target: ClientIPMaskingTarget = ClientIPMaskingTarget.DEFAULT
    mode: ClientIPMaskingMode = ClientIPMaskingMode.TRUNCATE
    ipv4: int | None = IPV4
    ipv6: int | None = IPV6

    @override
    def operation(self) -> str:
        return "admin_upsert"

    @override
    def describe(self, laid: ACaller) -> str:
        prefixes = "" if self.ipv4 is None and self.ipv6 is None else " 접두 길이와 함께"
        return (
            f"{laid.caller.username}이 {self.target.value} 대상에 {self.mode.value} 모드 정책을"
            f"{prefixes} 등록"
        )

    @override
    async def call(
        self, adapter: ClientIPMaskingAdapter, laid: ACaller
    ) -> ClientIPMaskingPolicyNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_upsert(
                AdminUpsertClientIPMaskingPolicyInput(
                    target_type=TargetInput(self.target.value),
                    mode=ModeInput(self.mode.value),
                    ipv4_prefix=self.ipv4,
                    ipv6_prefix=self.ipv6,
                )
            )
        return payload.policy


@dataclass(frozen=True)
class UpsertingTheLaidTargetAgain(
    When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]
):
    """미리 만들어 둔 정책의 대상에 다시 등록한다."""

    mode: ClientIPMaskingMode = ClientIPMaskingMode.DROP
    ipv4: int | None = IPV4
    ipv6: int | None = IPV6

    @override
    def operation(self) -> str:
        return "admin_upsert"

    @override
    def describe(self, laid: AMaskingPolicyAndACaller) -> str:
        prefixes = "" if self.ipv4 is None and self.ipv6 is None else " 접두 길이와 함께"
        return (
            f"{laid.caller.username}이 {laid.policy.target_type.value} 대상에 "
            f"{self.mode.value} 모드 정책을{prefixes} 다시 등록"
        )

    @override
    async def call(
        self, adapter: ClientIPMaskingAdapter, laid: AMaskingPolicyAndACaller
    ) -> ClientIPMaskingPolicyNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_upsert(
                AdminUpsertClientIPMaskingPolicyInput(
                    target_type=TargetInput(laid.policy.target_type.value),
                    mode=ModeInput(self.mode.value),
                    ipv4_prefix=self.ipv4,
                    ipv6_prefix=self.ipv6,
                )
            )
        return payload.policy


@dataclass(frozen=True)
class TheSuperadminPutsAPolicyOnATarget(
    Scenario[SeedingSession, ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-puts-a-masking-policy-on-a-target"

    @override
    def describe(self) -> str:
        return "정책이 없을 때 슈퍼관리자가 대상·모드·두 접두 길이를 지정해 등록하면 지정한 값이 그대로 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Upserting()

    @override
    def then(self) -> Then[ACaller, ClientIPMaskingPolicyNode]:
        return TheNewMaskingPolicyNode(
            started=self.started,
            target=ClientIPMaskingTarget.DEFAULT,
            mode=ClientIPMaskingMode.TRUNCATE,
            ipv4=IPV4,
            ipv6=IPV6,
        )


@dataclass(frozen=True)
class OmittedPrefixesStayEmpty(
    Scenario[SeedingSession, ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-masking-policy-put-without-prefixes-carries-empty-prefixes"

    @override
    def describe(self) -> str:
        return "대상과 모드만 지정해 등록하면 두 접두 길이가 비어 있는 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Upserting(ipv4=None, ipv6=None)

    @override
    def then(self) -> Then[ACaller, ClientIPMaskingPolicyNode]:
        return TheNewMaskingPolicyNode(
            started=self.started,
            target=ClientIPMaskingTarget.DEFAULT,
            mode=ClientIPMaskingMode.TRUNCATE,
            ipv4=None,
            ipv6=None,
        )


@dataclass(frozen=True)
class EachTargetTakesAPolicy(
    Scenario[SeedingSession, ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]
):
    started: datetime
    target: ClientIPMaskingTarget

    @override
    def summary(self) -> str:
        return f"a-masking-policy-is-put-on-the-{self.target.value.replace('_', '-')}-target"

    @override
    def describe(self) -> str:
        return f"슈퍼관리자가 {self.target.value} 대상에 등록하면 그 대상이 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Upserting(target=self.target)

    @override
    def then(self) -> Then[ACaller, ClientIPMaskingPolicyNode]:
        return TheNewMaskingPolicyNode(
            started=self.started,
            target=self.target,
            mode=ClientIPMaskingMode.TRUNCATE,
            ipv4=IPV4,
            ipv6=IPV6,
        )


@dataclass(frozen=True)
class EachModeIsKept(
    Scenario[SeedingSession, ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]
):
    started: datetime
    mode: ClientIPMaskingMode

    @override
    def summary(self) -> str:
        return f"a-masking-policy-of-the-{self.mode.value}-mode-is-put"

    @override
    def describe(self) -> str:
        return f"슈퍼관리자가 {self.mode.value} 모드로 등록하면 그 모드가 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Upserting(mode=self.mode)

    @override
    def then(self) -> Then[ACaller, ClientIPMaskingPolicyNode]:
        return TheNewMaskingPolicyNode(
            started=self.started,
            target=ClientIPMaskingTarget.DEFAULT,
            mode=self.mode,
            ipv4=IPV4,
            ipv6=IPV6,
        )


@dataclass(frozen=True)
class PuttingOnATakenTargetRewritesTheRow(
    Scenario[
        SeedingSession, AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "putting-a-policy-on-a-target-that-has-one-rewrites-the-same-row"

    @override
    def describe(self) -> str:
        return "이미 정책이 있는 대상에 다른 모드로 등록하면, 새 행이 아니라 같은 id의 행이 새 모드로 바뀐 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AMaskingPolicyAndACaller]:
        return AMaskingPolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return UpsertingTheLaidTargetAgain(mode=ClientIPMaskingMode.DROP)

    @override
    def then(self) -> Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]:
        return TheSameRowRewritten(started=self.started, mode=ClientIPMaskingMode.DROP)


@dataclass(frozen=True)
class PuttingAgainWithoutPrefixesClearsThem(
    Scenario[
        SeedingSession, AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "putting-a-policy-again-without-prefixes-clears-the-stored-prefixes"

    @override
    def describe(self) -> str:
        return (
            "접두 길이가 있는 정책의 대상에 대상과 모드만 지정해 다시 등록하면 접두 길이가 비워진다. "
            "등록은 기존 값과 병합하지 않고 행을 통째로 바꾼다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMaskingPolicyAndACaller]:
        return AMaskingPolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AMaskingPolicyAndACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return UpsertingTheLaidTargetAgain(mode=ClientIPMaskingMode.TRUNCATE, ipv4=None, ipv6=None)

    @override
    def then(self) -> Then[AMaskingPolicyAndACaller, ClientIPMaskingPolicyNode]:
        return TheSameRowRewritten(started=self.started, ipv4=None, ipv6=None)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotPut(
    Scenario[SeedingSession, ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-put-a-masking-policy"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 정책을 등록하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Upserting()

    @override
    def then(self) -> Then[ACaller, ClientIPMaskingPolicyNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheMonitorMayNotPut(
    Scenario[SeedingSession, ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-put-a-masking-policy"

    @override
    def describe(self) -> str:
        return "모니터 역할이 정책을 등록하면 역할 부족으로 거부된다. 모니터는 전역 역할 검사에서 읽기만 통과한다"

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Upserting()

    @override
    def then(self) -> Then[ACaller, ClientIPMaskingPolicyNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[SeedingSession, ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-put-a-masking-policy"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 꺼도 슈퍼관리자가 아니면 정책을 등록하지 못한다. "
            "등록은 권한 그래프가 아니라 역할로 보호되므로 스위치와 무관하다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, ClientIPMaskingAdapter, ClientIPMaskingPolicyNode]:
        return Upserting()

    @override
    def then(self) -> Then[ACaller, ClientIPMaskingPolicyNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[UpsertingStep] = [
    TheSuperadminPutsAPolicyOnATarget(started=datetime.now(UTC)),
    OmittedPrefixesStayEmpty(started=datetime.now(UTC)),
    *(
        EachTargetTakesAPolicy(started=datetime.now(UTC), target=target)
        for target in ClientIPMaskingTarget
    ),
    *(EachModeIsKept(started=datetime.now(UTC), mode=mode) for mode in ClientIPMaskingMode),
    PuttingOnATakenTargetRewritesTheRow(started=datetime.now(UTC)),
    PuttingAgainWithoutPrefixesClearsThem(started=datetime.now(UTC)),
    AUserWhoIsNotTheSuperadminMayNotPut(),
    TheMonitorMayNotPut(),
    EnforcementOffStillNeedsTheSuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_upserting(
    scenario: UpsertingStep, adapter: ClientIPMaskingAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
