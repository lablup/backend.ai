"""정책을 이름으로 조회 — 누가 조회할 수 있고, 이름이 무엇을 숨기는가.

이름을 정책으로 풀어내는 단계는 로그인한 누구에게나 열려 있고, 권한은 그 뒤의 조회가
정책 노드에 대해 검사한다. 그래서 존재하지 않는 이름은 누구에게나 대상 없음으로, 권한이
미치지 않는 이름은 권한 부족으로 거부된다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)
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

NOBODY = "nobody"
ENFORCEMENT = "manager.rbac.enforcement_enabled"

type ReadingStep = Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]


@dataclass(frozen=True)
class ReadingByName(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]):
    """이름으로 조회한다. 이름을 지정하지 않으면 미리 만들어 둔 정책의 이름을 쓴다."""

    family: Family[Any, Any]
    named: str | None = None

    @override
    def operation(self) -> str:
        return self.family.calls.read

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        return f"{laid.caller.username}이 {self.named or laid.policy.name} 이름으로 조회"

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
            "그 정책 전체가 반환된다"
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
            f"같은 {self.family.kind}이 있고 아무 권한도 없는 사용자가 이름으로 조회하면, "
            "이름은 풀리지만 그 정책을 읽을 권한이 없어 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingByName(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    role: UserRole

    @override
    def summary(self) -> str:
        return (
            f"reading-a-{self.family.label}-name-nothing-answers-to-is-not-found-"
            f"for-a-{self.role.value}"
        )

    @override
    def describe(self) -> str:
        return (
            f"{self.role.value}이 어느 {self.family.kind}에도 없는 이름으로 조회하면, "
            "권한 문제가 아니라 대상이 없다는 것으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=self.role)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingByName(self.family, named=NOBODY)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(EntityNotFoundError)


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
        return f"권한 검사를 끄면 아무 권한도 없는 사용자도 {self.family.kind}을 이름으로 조회할 수 있다"

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
    *(
        ANameNothingAnswersToIsNotFound(family, role)
        for family in FAMILIES
        for role in (UserRole.SUPERADMIN, UserRole.USER)
    ),
    *(EnforcementOffOpensTheRead(family, started=datetime.now(UTC)) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
