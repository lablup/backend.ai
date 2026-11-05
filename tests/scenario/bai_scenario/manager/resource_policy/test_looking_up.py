"""이름으로 정책 id 찾기 — 하나씩, 그리고 여럿을 한 번에.

이 호출은 인증만 확인하고, 해석한 id 를 받는 호출이 권한을 본다. 없는 이름은 인증한
호출자에게 그대로 거부된다.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    FAMILIES,
    APolicyAndACaller,
    APolicyAndSomeone,
    Family,
    TheKnownNameHasAnId,
    ThePolicyId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

NOBODY = "nobody"

type LookedUp = UUID
type LookedUpSeveral = Sequence[UUID | None]
type LookingUpStep = Scenario[
    TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Any
]


@dataclass(frozen=True)
class LookingUpTheName(When[APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUp]):
    """이름으로 id 를 찾는다. ``unknown``이면 어느 정책도 갖지 않은 이름을 쓴다."""

    family: Family[Any, Any]
    unknown: bool = False

    @override
    def operation(self) -> str:
        return self.family.calls.lookup

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        name = NOBODY if self.unknown else laid.policy.name
        return Says(
            f"{laid.caller.username}이 {name}의 id 를 찾습니다",
            english=f"{laid.caller.username} looks up the id of {name}",
        )

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> LookedUp:
        name = NOBODY if self.unknown else laid.policy.name
        with ActingAs(laid.caller):
            return await self.family.lookup(adapter, name)


@dataclass(frozen=True)
class LookingUpSeveralNames(When[APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUpSeveral]):
    """미리 만들어 둔 정책의 이름과 어느 정책도 갖지 않은 이름으로 id 를 여럿 찾는다."""

    family: Family[Any, Any]

    @override
    def operation(self) -> str:
        return self.family.calls.bulk_lookup

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.policy.name}과 {NOBODY}의 id 를 여럿 조회합니다",
            english=(
                f"{laid.caller.username} looks up several ids for {laid.policy.name} and {NOBODY}"
            ),
        )

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]
    ) -> LookedUpSeveral:
        with ActingAs(laid.caller):
            return await self.family.bulk_lookup(adapter, [laid.policy.name, NOBODY])


@dataclass(frozen=True)
class LookingUpSeveralNamesWithoutLogin(
    When[APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUpSeveral]
):
    """로그인 문맥 없이 미리 만들어 둔 정책의 이름으로 id 를 여럿 찾는다."""

    family: Family[Any, Any]

    @override
    def operation(self) -> str:
        return self.family.calls.bulk_lookup

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        return Says(
            f"로그인 문맥 없이 {laid.policy.name}의 id 를 여럿 조회합니다",
            english=f"without a login context, looks up several ids for {laid.policy.name}",
        )

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]
    ) -> LookedUpSeveral:
        return await self.family.bulk_lookup(adapter, [laid.policy.name])


@dataclass(frozen=True)
class TheSuperadminLooksUpAName(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUp]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"the-superadmin-looks-up-a-{self.family.label}-by-name"

    @override
    def describe(self) -> str:
        return Says(
            f"superadmin 이 {self.family.kind} 이름으로 id 를 찾으면 그 정책의 id 가 반환됩니다",
            english=(
                f"when the superadmin looks up a {self.family.label} by name, the id of that "
                "policy comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUp]:
        return LookingUpTheName(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], LookedUp]:
        return ThePolicyId()


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUp]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"looking-up-a-{self.family.label}-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            f"superadmin 이 어느 {self.family.kind}에도 없는 이름으로 id 를 찾으면 대상이 없다는 "
            "것으로 거부됩니다",
            english=(
                f"when the superadmin looks up a name no {self.family.label} holds, the call is "
                "rejected as no such target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUp]:
        return LookingUpTheName(self.family, unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], LookedUp]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class TheSuperadminLooksUpSeveralNames(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUpSeveral]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"the-superadmin-looks-up-several-{self.family.label}-names"

    @override
    def describe(self) -> str:
        return Says(
            f"superadmin 이 있는 이름과 없는 이름으로 {self.family.kind} id 를 여럿 조회하면, "
            "있는 이름에는 그 정책의 id, 없는 이름에는 빈 값이 응답으로 옵니다",
            english=(
                f"when the superadmin looks up several ids for a name that exists and one that "
                f"does not, the {self.family.label} id comes back for the name that exists and an "
                "empty value for the name that does not"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUpSeveral]:
        return LookingUpSeveralNames(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], LookedUpSeveral]:
        return TheKnownNameHasAnId()


@dataclass(frozen=True)
class LookingUpSeveralNamesWithoutLoginIsRefused(
    Scenario[TestSeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUpSeveral]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"looking-up-several-{self.family.label}-names-without-login-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "로그인 문맥 없이 이름으로 id 를 여럿 조회하면, 사용자를 찾을 수 없다는 것으로 "
            "거부됩니다",
            english=(
                "looking up several ids by name without a login context is rejected as user not "
                "found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, LookedUpSeveral]:
        return LookingUpSeveralNamesWithoutLogin(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], LookedUpSeveral]:
        return TheCallIsRefused(UserNotFound)


SCENARIOS: list[LookingUpStep] = [
    *(TheSuperadminLooksUpAName(family) for family in FAMILIES),
    *(ANameNothingAnswersToIsNotFound(family) for family in FAMILIES),
    *(TheSuperadminLooksUpSeveralNames(family) for family in FAMILIES),
    *(LookingUpSeveralNamesWithoutLoginIsRefused(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_looking_up(
    scenario: LookingUpStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
