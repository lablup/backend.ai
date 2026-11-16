"""정책 생성 — 누가 생성할 수 있고, 무엇이 값을 막는가.

생성은 전역 superadmin 역할만 검사한다. 이름 중복과 범위 밖 우선순위 상한은 생성 spec이
아니라 데이터베이스 제약이 막으므로, 그 거부는 저장소의 제약 위반 오류로 온다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.repository import (
    CheckConstraintViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Language,
    Says,
    Scenario,
    Then,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    FAMILIES,
    KEYPAIR,
    OWN_FAMILIES,
    APolicyAndACaller,
    APolicyAndSomeone,
    Ask,
    Family,
    TheNewPolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

FRESH = "fresh-policy"
ENFORCEMENT = "manager.rbac.enforcement_enabled"

type CreatingStep = Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]


@dataclass(frozen=True)
class Creating(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]):
    """정책을 생성한다. 요청을 지정하지 않으면 미리 만들어 둔 정책의 이름으로 모든 값을 지정해 생성한다."""

    family: Family[Any, Any]
    ask: Ask | None = None

    @override
    def operation(self) -> str:
        return self.family.calls.create

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        if self.ask is not None:
            how_ko = self.ask.says
            how_en = in_language(self.ask.says, Language.ENGLISH)
        else:
            how_ko = "이미 있는 이름으로"
            how_en = "with an existing name"
        return Says(
            f"{laid.caller.username}이 {how_ko} {kind}을 생성합니다",
            english=f"{laid.caller.username} creates the {kind_en} {how_en}",
        )

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> Any:
        ask = self.ask if self.ask is not None else self.family.everything(laid.policy.name)
        with ActingAs(laid.caller):
            return await self.family.create(adapter, ask.asked)


@dataclass(frozen=True)
class TheWholeNodeComesBack(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"the-superadmin-creates-a-{self.family.label}-giving-every-value"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"superadmin 이 모든 값을 지정해 {kind}을 생성하면, 지정한 값이 그대로 담긴 노드 "
            "전체가 반환됩니다",
            english=(
                f"when the superadmin creates a {kind_en} giving every value, the whole node "
                "comes back with those values as given"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.family.everything(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheNewPolicyNode(self.family, self.started, self.family.everything(FRESH))


@dataclass(frozen=True)
class LeavingOptionalsOutLeavesThemEmpty(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    ask: Ask
    started: datetime

    @override
    def summary(self) -> str:
        return f"leaving-the-optional-values-out-of-a-{self.family.label}-leaves-them-empty"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"superadmin 이 생략할 수 있는 항목을 모두 생략하고 {kind}을 생성하면, 생략한 필드가 "
            "비어 있는 노드 전체가 반환됩니다",
            english=(
                f"when the superadmin creates a {kind_en} leaving out every optional entry, the "
                "whole node comes back with the omitted fields empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.ask)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheNewPolicyNode(self.family, self.started, self.ask)


@dataclass(frozen=True)
class AnUnlimitedSlotIsMarkedUnlimited(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-unlimited-slot-of-a-keypair-policy-comes-back-marked-unlimited"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 한 자원의 전체 슬롯을 무제한으로 지정해 키페어 정책을 생성하면, 그 "
            "자원은 무제한으로 표시되고 수량은 비어 있습니다",
            english=(
                "when the superadmin creates a keypair policy with every slot of one resource "
                "set to unlimited, that resource comes back marked unlimited with an empty "
                "quantity"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(KEYPAIR, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(KEYPAIR, KEYPAIR.unlimited_slot(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheNewPolicyNode(KEYPAIR, self.started, KEYPAIR.unlimited_slot(FRESH))


@dataclass(frozen=True)
class ANameAnotherPolicyHoldsIsRefused(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-name-another-{self.family.label}-already-holds-is-refused"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"이미 다른 {kind}이 사용 중인 이름으로 생성하려 하면 이름 중복으로 거부됩니다",
            english=(
                f"creating with a name another {kind_en} already holds is rejected as a "
                "duplicate name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class APriorityCapOutOfRangeIsRefused(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-priority-cap-outside-the-session-range-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 우선순위 상한을 세션 우선순위 범위 밖 값으로 지정해 키페어 정책을 "
            "생성하려 하면 제약 위반으로 거부됩니다",
            english=(
                "when the superadmin tries to create a keypair policy with a priority cap "
                "outside the session priority range, the call is rejected on a constraint "
                "violation"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(KEYPAIR, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(KEYPAIR, KEYPAIR.priority_out_of_range(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(CheckConstraintViolationError)


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-who-is-not-the-superadmin-may-not-create-a-{self.family.label}"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"superadmin 이 아닌 사용자가 {kind}을 생성하려 하면 어떤 권한을 받았는지와 무관하게 "
            "역할 부족으로 거부됩니다",
            english=(
                f"when a user who is not the superadmin tries to create a {kind_en}, the call is "
                "rejected for lacking the role regardless of how much permission the user holds"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.family.everything(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AMonitorMayNotCreate(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-monitor-may-not-create-a-{self.family.label}"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"모니터 역할 사용자가 {kind}을 생성하려 하면 역할 부족으로 거부됩니다. superadmin "
            "검사는 모니터에게 읽기만 허용합니다",
            english=(
                f"when a user with the monitor role tries to create a {kind_en}, the call is "
                "rejected for lacking the role. the superadmin check allows the monitor reads only"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.MONITOR)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.family.everything(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothing(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any], Configured
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"turning-enforcement-off-still-does-not-let-a-user-create-a-{self.family.label}"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"권한 검사를 꺼도 {kind} 생성은 여전히 거부됩니다",
            english=(f"turning permission enforcement off still rejects creating a {kind_en}"),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Creating(self.family, self.family.everything(FRESH))

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    *(TheWholeNodeComesBack(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(
        LeavingOptionalsOutLeavesThemEmpty(
            family, family.only_required(FRESH), started=datetime.now(UTC)
        )
        for family in OWN_FAMILIES
    ),
    AnUnlimitedSlotIsMarkedUnlimited(started=datetime.now(UTC)),
    *(ANameAnotherPolicyHoldsIsRefused(family) for family in FAMILIES),
    APriorityCapOutOfRangeIsRefused(),
    *(APlainUserMayNotCreate(family) for family in FAMILIES),
    *(AMonitorMayNotCreate(family) for family in FAMILIES),
    *(EnforcementOffChangesNothing(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
