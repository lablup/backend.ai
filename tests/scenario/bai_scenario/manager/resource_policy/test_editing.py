"""정책 고치기 — 무엇이 바뀌고, 비우라는 요청을 어떻게 읽는가.

권한 없는 사용자는 고치기 문에 닿기 전에 이름 해석에서 막히므로, 거부가 읽기와 같은 이유로
온다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    FAMILIES,
    APolicyAndACaller,
    APolicyAndSomeone,
    Edit,
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
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

NOBODY = "nobody"

type EditingStep = Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]


@dataclass(frozen=True)
class Editing(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]):
    """정책 하나를 고친다. 이름을 대지 않으면 심은 정책을 고친다."""

    family: Family[Any, Any]
    edit: Edit
    named: str | None = None

    @override
    def operation(self) -> str:
        return self.family.calls.update

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        return f"{laid.caller.username}이 {self.named or laid.policy.name}을 {self.edit.says} 수정"

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> Any:
        with ActingAs(laid.caller):
            return await self.family.update(
                adapter, self.named or laid.policy.name, self.edit.asked
            )


@dataclass(frozen=True)
class OneLimitChangesAndNothingElse(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"the-superadmin-changes-one-limit-of-a-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"{self.family.kind} 하나가 있고 슈퍼관리자가 한도 하나만 고치면, "
            "그 한도는 새 값이 되고 나머지는 그대로다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.one_limit())

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started, changed=self.family.one_limit().changed)


@dataclass(frozen=True)
class GivingNothingChangesNothing(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"giving-no-value-changes-nothing-of-a-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 {self.family.kind}을 지목만 하고 아무 값도 주지 않으면, "
            "아무것도 바뀌지 않은 노드가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.nothing())

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started)


@dataclass(frozen=True)
class ANonNullableValueStaysWhenCleared(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"clearing-a-non-nullable-value-of-a-{self.family.label}-leaves-it-as-it-was"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 {self.family.kind}의 비울 수 없는 항목을 비우도록 고치면, 그 요청은 "
            "없던 것으로 읽혀 아무것도 바뀌지 않은 노드가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.clearing_a_non_nullable())

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-granted-nothing-may-not-edit-a-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"같은 {self.family.kind}이 있고 아무 권한도 받지 않은 사용자가 고치려 하면, "
            "고치기 문에 닿기 전에 이름을 해석할 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.one_limit())

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
        return f"editing-a-{self.family.label}-name-nothing-answers-to-is-unresolvable"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 어느 {self.family.kind}도 갖지 않은 이름을 고치려 하면, "
            "이름을 해석할 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.one_limit(), named=NOBODY)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(GenericBadRequest)


SCENARIOS: list[EditingStep] = [
    *(OneLimitChangesAndNothingElse(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(GivingNothingChangesNothing(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(ANonNullableValueStaysWhenCleared(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(AUserGrantedNothingMayNotEdit(family) for family in FAMILIES),
    *(ANameNothingAnswersToIsUnresolvable(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
