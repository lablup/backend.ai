"""정책을 이름으로 읽기 — 누가 읽을 수 있고, 이름이 무엇을 숨기는가.

이름을 해석하는 단계가 먼저 돌고, 없는 이름과 권한이 닿지 않는 이름을 같은 이유로
거부한다. 슈퍼관리자에게도 같아서 대상 없음으로 거부되는 줄이 없다.
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
    Family,
    ThePolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

NOBODY = "nobody"
ENFORCEMENT = "manager.rbac.enforcement_enabled"

type ReadingStep = Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]


@dataclass(frozen=True)
class ReadingByName(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]):
    """이름으로 읽는다. 이름을 대지 않으면 심은 정책의 이름을 쓴다."""

    family: Family[Any, Any]
    named: str | None = None

    @override
    def operation(self) -> str:
        return self.family.calls.read

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        return f"{laid.caller.username}이 {self.named or laid.policy.name}으로 조회"

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> Any:
        with ActingAs(laid.caller):
            return await self.family.read(adapter, self.named or laid.policy.name)


@dataclass(frozen=True)
class TheSuperadminReadsItByName(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"the-superadmin-reads-a-{self.family.label}-by-name"

    @override
    def describe(self) -> str:
        return (
            f"{self.family.kind} 하나가 있고 슈퍼관리자가 이름으로 조회하면, "
            "그 정책 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingByName(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-granted-nothing-cannot-resolve-a-{self.family.label}-name"

    @override
    def describe(self) -> str:
        return (
            f"같은 {self.family.kind}이 있고 아무 권한도 받지 않은 사용자가 이름으로 조회하면, "
            "이름을 해석할 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingByName(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class ANameNothingAnswersToIsUnresolvable(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return (
            f"a-{self.family.label}-name-nothing-answers-to-is-unresolvable-even-for-the-superadmin"
        )

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 어느 {self.family.kind}도 갖지 않은 이름으로 조회하면, 대상이 없다는 "
            "것이 아니라 이름을 해석할 수 없다는 이유로 거부된다. 그 이름이 있는지를 "
            "거부가 말하지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingByName(self.family, named=NOBODY)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class EnforcementOffOpensTheRead(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any], Configured
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"turning-enforcement-off-lets-a-user-granted-nothing-read-a-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 {self.family.kind}을 "
            "이름으로 읽을 수 있다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingByName(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started)


SCENARIOS: list[ReadingStep] = [
    *(TheSuperadminReadsItByName(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(AUserGrantedNothingMayNotRead(family) for family in FAMILIES),
    *(ANameNothingAnswersToIsUnresolvable(family) for family in FAMILIES),
    *(EnforcementOffOpensTheRead(family, started=datetime.now(UTC)) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
