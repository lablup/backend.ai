"""정책 만들기 — 누가 만들 수 있고, 무엇이 이름을 막는가.

문은 전역 superadmin 역할 하나다. 이름 겹침은 만들기 spec이 아니라 데이터베이스 제약이
막으므로, 그 거부는 저장소의 제약 위반 오류로 온다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    FAMILIES,
    APolicyAndACaller,
    APolicyAndSomeone,
    Ask,
    Family,
    TheNewPolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

FRESH = "fresh-policy"
ENFORCEMENT = "manager.rbac.enforcement_enabled"

type CreatingStep = Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]


@dataclass(frozen=True)
class Creating(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]):
    """정책을 만든다. 요청을 대지 않으면 심은 정책의 이름으로 모든 값을 주고 만든다."""

    family: Family[Any, Any]
    ask: Ask | None = None

    @override
    def operation(self) -> str:
        return self.family.calls.create

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        how = self.ask.says if self.ask is not None else "이미 있는 이름으로"
        return f"{laid.caller.username}이 {how} {self.family.kind}을 만듦"

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> Any:
        ask = self.ask if self.ask is not None else self.family.everything(laid.policy.name)
        with ActingAs(laid.caller):
            return await self.family.create(adapter, ask.asked)


@dataclass(frozen=True)
class TheWholeNodeComesBack(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"the-superadmin-creates-a-{self.family.label}-giving-every-value"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 모든 값을 주고 {self.family.kind}을 만들면, "
            "준 값이 그대로 실린 노드 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.family.everything(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheNewPolicyNode(self.family, self.started, self.family.everything(FRESH))


@dataclass(frozen=True)
class ANameAnotherPolicyHoldsIsRefused(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-name-another-{self.family.label}-already-holds-is-refused"

    @override
    def describe(self) -> str:
        return (
            f"이미 어떤 {self.family.kind}이 쓰고 있는 이름으로 만들려 하면, "
            "이름이 겹친다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-who-is-not-the-superadmin-may-not-create-a-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 아닌 사용자가 {self.family.kind}을 만들려 하면, "
            "권한을 얼마나 받았는지와 무관하게 역할로 막힌다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.family.everything(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AMonitorMayNotCreate(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-monitor-may-not-create-a-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"모니터 역할 사용자가 {self.family.kind}을 만들려 하면 역할로 막힌다. "
            "역할 문은 모니터에게 읽기만 열어 준다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.MONITOR)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.family.everything(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any], Configured
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"turning-enforcement-off-still-does-not-let-a-user-create-a-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"엔티티 권한 집행을 꺼도 {self.family.kind} 만들기는 여전히 막힌다. "
            "이 문은 권한 그래프가 아니라 역할이 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.family.everything(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    *(TheWholeNodeComesBack(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(ANameAnotherPolicyHoldsIsRefused(family) for family in FAMILIES),
    *(APlainUserMayNotCreate(family) for family in FAMILIES),
    *(AMonitorMayNotCreate(family) for family in FAMILIES),
    *(EnforcementOffChangesNothing(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
