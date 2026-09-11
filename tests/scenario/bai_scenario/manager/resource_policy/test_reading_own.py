"""자기 정책 조회 — 호출자 자신의 스코프에 부여된 권한으로 보호된다.

요청 본문이 없고 호출자 자신이 곧 입력이다. 사용자 정책은 사용자 행이 직접 가리킨다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    OWN_FAMILIES,
    APolicyAndACaller,
    OwnFamily,
    SomeoneHeldToTheirPolicy,
    ThePolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

ENFORCEMENT = "manager.rbac.enforcement_enabled"

type OwnStep = Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]


@dataclass(frozen=True)
class ReadingMine(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]):
    """호출자 자신의 정책을 조회한다. 요청 본문은 없다."""

    family: OwnFamily[Any, Any]

    @override
    def operation(self) -> str:
        return self.family.mine

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        return f"{laid.caller.username}이 자기 {self.family.kind}을 조회"

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> Any:
        with ActingAs(laid.caller):
            return await self.family.read_mine(adapter)


@dataclass(frozen=True)
class TheGrantedUserReadsTheirOwn(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: OwnFamily[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"a-user-granted-read-in-their-own-scope-reads-their-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"자기 스코프에서 {self.family.kind}을 읽을 권한을 받은 사용자가 자기 정책을 "
            "조회하면, 그 사용자에게 할당된 정책 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return SomeoneHeldToTheirPolicy(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingMine(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheirOwn(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: OwnFamily[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-granted-nothing-may-not-read-their-own-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"아무 권한도 없는 사용자가 자기 {self.family.kind}을 조회하면 권한 부족으로 "
            "거부된다. 자기 정책을 읽는 호출도 범위만 좁히는 것이 아니라 권한을 검사한다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return SomeoneHeldToTheirPolicy(self.family, granted=False)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingMine(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffOpensTheirOwn(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any], Configured
):
    family: OwnFamily[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"권한 검사를 끄면 아무 권한도 없는 사용자도 자기 {self.family.kind}을 "
            "조회할 수 있다. 이 호출은 권한 그래프로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return SomeoneHeldToTheirPolicy(self.family, granted=False)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return ReadingMine(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started)


SCENARIOS: list[OwnStep] = [
    *(TheGrantedUserReadsTheirOwn(family, started=datetime.now(UTC)) for family in OWN_FAMILIES),
    *(AUserGrantedNothingMayNotReadTheirOwn(family) for family in OWN_FAMILIES),
    *(EnforcementOffOpensTheirOwn(family, started=datetime.now(UTC)) for family in OWN_FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_own(
    scenario: OwnStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
