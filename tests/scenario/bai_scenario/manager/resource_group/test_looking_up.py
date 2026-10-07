"""이름으로 리소스 그룹 id 찾기. 인증만 보고, 권한은 id를 받는 호출이 본다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_group import AGroupAndACaller, AGroupAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type LookingUpStep = Scenario[
    SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupID
]

UNKNOWN = "no-such-group"


@dataclass(frozen=True)
class LookingUpTheName(When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupID]):
    """이름으로 id를 찾는다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "lookup_name"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        name = UNKNOWN if self.unknown else laid.group.name
        return f"{laid.caller.username}이 {name}의 id를 찾음"

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller) -> ResourceGroupID:
        with ActingAs(laid.caller):
            return await adapter.lookup_name(UNKNOWN if self.unknown else laid.group.name)


@dataclass(frozen=True)
class TheGroupsIdComesBack(Then[AGroupAndACaller, ResourceGroupID]):
    """그 이름을 가진 리소스 그룹의 id가 온다."""

    @override
    def says(self) -> str:
        return "그 리소스 그룹의 id가 온다"

    @override
    def look(self, laid: AGroupAndACaller, answered: Answered[ResourceGroupID]) -> list[Verdict]:
        found = answered.response
        if found is None:
            return [MissingResponse(answered.raised)]
        return [Held[UUID]("id", found, SameAs(laid.group.id, "미리 만든 리소스 그룹의 id"))]


@dataclass(frozen=True)
class TheSuperadminLooksUpAName(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupID]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-looks-up-a-resource-group-by-name"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 리소스 그룹 이름으로 id를 찾으면, 그 리소스 그룹의 id가 온다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupID]:
        return LookingUpTheName()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupID]:
        return TheGroupsIdComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingStillLooksUpAName(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupID]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-still-looks-up-a-resource-group-by-name"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자도 리소스 그룹 이름으로 id를 찾을 수 있다. "
            "이 호출은 인증만 보고, 권한은 그 id를 받는 호출이 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupID]:
        return LookingUpTheName()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupID]:
        return TheGroupsIdComesBack()


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupID]
):
    @override
    def summary(self) -> str:
        return "looking-up-a-resource-group-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "아무 리소스 그룹도 갖지 않은 이름으로 id를 찾으면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupID]:
        return LookingUpTheName(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupID]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[LookingUpStep] = [
    TheSuperadminLooksUpAName(),
    AUserGrantedNothingStillLooksUpAName(),
    ANameNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_looking_up(
    scenario: LookingUpStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
