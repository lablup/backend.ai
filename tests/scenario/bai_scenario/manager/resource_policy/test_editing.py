"""정책 수정 — 무엇이 바뀌고, 값을 비우라는 요청을 어떻게 처리하는가.

권한 없는 사용자는 수정 로직에 이르기 전에 이름 조회 단계에서 막히므로, 거부 이유가 조회와
같다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.repository import CheckConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
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
    Edit,
    Family,
    ThePolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

NOBODY = "nobody"

type EditingStep = Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]


@dataclass(frozen=True)
class Editing(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]):
    """정책 하나를 수정한다. 이름을 지정하지 않으면 미리 만들어 둔 정책을 수정한다."""

    family: Family[Any, Any]
    edit: Edit
    named: str | None = None

    @override
    def operation(self) -> str:
        return self.family.calls.update

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        name = self.named or laid.policy.name
        edit = self.edit.says
        return Says(
            f"{laid.caller.username}이 {name}을 수정합니다 ({edit})",
            english=(
                f"{laid.caller.username} updates {name} ({in_language(edit, Language.ENGLISH)})"
            ),
        )

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> Any:
        with ActingAs(laid.caller):
            return await self.family.update(
                adapter, self.named or laid.policy.name, self.edit.asked
            )


@dataclass(frozen=True)
class OneLimitChangesAndNothingElse(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"the-superadmin-changes-one-limit-of-a-{self.family.label}"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"{kind} 하나가 있고 superadmin 이 한도 하나만 수정하면, 그 한도만 새 값이 되고 "
            "나머지는 그대로 유지됩니다",
            english=(
                f"one {kind_en} exists and the superadmin changes one limit, so only that limit "
                "takes the new value and the rest stays as it was"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.one_limit())

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started, changed=self.family.one_limit().changed)


@dataclass(frozen=True)
class GivingNothingChangesNothing(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"giving-no-value-changes-nothing-of-a-{self.family.label}"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"superadmin 이 {kind}을 지정만 하고 아무 값도 주지 않으면, 아무것도 바뀌지 않은 "
            "노드가 반환됩니다",
            english=(
                f"when the superadmin names a {kind_en} and gives no value, the node comes back "
                "with nothing changed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.nothing())

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started)


@dataclass(frozen=True)
class ANullableValueIsCleared(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    edit: Edit
    started: datetime

    @override
    def summary(self) -> str:
        return f"clearing-a-nullable-value-of-a-{self.family.label}-empties-it"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"비울 수 있는 항목에 값이 설정된 {kind}을 superadmin 이 그 항목을 비우도록 "
            "수정하면, 그 항목이 비어 있는 노드가 반환됩니다",
            english=(
                f"when the superadmin clears the nullable entry of a {kind_en} that holds a "
                "value, the node comes back with that entry empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN, holding_optional=True)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.edit)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started, changed=self.edit.changed)


@dataclass(frozen=True)
class ANonNullableValueStaysWhenCleared(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]
    started: datetime

    @override
    def summary(self) -> str:
        return f"clearing-a-non-nullable-value-of-a-{self.family.label}-leaves-it-as-it-was"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"superadmin 이 {kind}의 비울 수 없는 항목을 비우도록 수정하면, 그 요청은 무시되어 "
            "아무것도 바뀌지 않은 노드가 반환됩니다",
            english=(
                f"when the superadmin clears a non-nullable entry of a {kind_en}, the request is "
                "ignored and the node comes back with nothing changed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.clearing_a_non_nullable())

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return ThePolicyNode(self.family, self.started)


@dataclass(frozen=True)
class APriorityCapMovedOutOfRangeIsRefused(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "moving-the-priority-cap-outside-the-session-range-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 키페어 정책의 우선순위 상한을 세션 우선순위 범위 밖으로 수정하려 "
            "하면 제약 위반으로 거부됩니다",
            english=(
                "when the superadmin tries to move the priority cap of a keypair policy outside "
                "the session priority range, the call is rejected on a constraint violation"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(KEYPAIR, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(KEYPAIR, KEYPAIR.priority_moved_out_of_range())

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(CheckConstraintViolationError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-granted-nothing-may-not-edit-a-{self.family.label}"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"같은 {kind}이 있고 아무 권한도 없는 사용자가 수정하려 하면, 수정 로직에 이르기 "
            "전에 정책을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                f"when the same {kind_en} exists and a user granted nothing tries to edit it, "
                "the call is rejected before the edit logic because the policy cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.one_limit())

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"editing-a-{self.family.label}-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"superadmin 이 어느 {kind}에도 없는 이름을 수정하려 하면, 권한 문제가 아니라 "
            "대상이 없다는 것으로 거부됩니다",
            english=(
                f"when the superadmin tries to edit a name no {kind_en} holds, the call is "
                "rejected as no such target, not on a permission problem"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Any]:
        return Editing(self.family, self.family.one_limit(), named=NOBODY)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Any]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[EditingStep] = [
    *(OneLimitChangesAndNothingElse(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(GivingNothingChangesNothing(family, started=datetime.now(UTC)) for family in FAMILIES),
    *(
        ANullableValueIsCleared(family, family.clearing_a_nullable(), started=datetime.now(UTC))
        for family in OWN_FAMILIES
    ),
    *(ANonNullableValueStaysWhenCleared(family, started=datetime.now(UTC)) for family in FAMILIES),
    APriorityCapMovedOutOfRangeIsRefused(),
    *(AUserGrantedNothingMayNotEdit(family) for family in FAMILIES),
    *(ANameNothingAnswersToIsNotFound(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
