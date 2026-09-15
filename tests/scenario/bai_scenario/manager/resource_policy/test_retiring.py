"""정책 삭제 — soft-delete 없이 행을 바로 지운다.

삭제 spec에는 충돌 검사가 없다. 아직 사용 중인 정책의 삭제를 막는 것은 데이터베이스의 외래
키이므로, 거부가 저장소의 제약 위반 오류로 온다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    FAMILIES,
    AHeldPolicyAndSomeone,
    APolicyAndACaller,
    APolicyAndSomeone,
    Family,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

NOBODY = "nobody"


@dataclass(frozen=True)
class Purged:
    """삭제 뒤의 상태. 응답에 담긴 이름과, 그 이름으로 다시 검색했을 때의 건수."""

    name: str
    left: int


type RetiringStep = Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]


@dataclass(frozen=True)
class Purging(When[APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]):
    """정책을 삭제하고 같은 이름으로 다시 검색한다. 이름을 지정하지 않으면 미리 만들어 둔 정책을 삭제한다."""

    family: Family[Any, Any]
    named: str | None = None

    @override
    def operation(self) -> str:
        return self.family.calls.delete

    @override
    def describe(self, laid: APolicyAndACaller[Any]) -> str:
        return f"{laid.caller.username}이 {self.named or laid.policy.name} 삭제 후 같은 이름으로 다시 검색"

    @override
    async def call(self, adapter: ResourcePolicyAdapter, laid: APolicyAndACaller[Any]) -> Purged:
        wanted = self.named or laid.policy.name
        with ActingAs(laid.caller):
            answered = await self.family.delete(adapter, wanted)
            found = await self.family.search(adapter, named=wanted)
        return Purged(name=answered, left=found.total_count)


@dataclass(frozen=True)
class TheNameIsAnsweredAndGone(Then[APolicyAndACaller[Any], Purged]):
    """삭제한 이름이 응답에 담기고, 그 이름으로는 더 이상 검색되지 않는다."""

    @override
    def says(self) -> str:
        return "삭제한 이름이 반환되고 다시 검색하면 없다"

    @override
    def look(self, laid: APolicyAndACaller[Any], answered: Answered[Purged]) -> list[Verdict]:
        purged = answered.response
        if purged is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("name", purged.name, laid.policy.name),
            Same("found afterwards", purged.left, 0),
        ]


@dataclass(frozen=True)
class TheSuperadminPurgesAnUnusedPolicy(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"the-superadmin-purges-a-{self.family.label}-nobody-holds"

    @override
    def describe(self) -> str:
        return (
            f"아무도 사용하지 않는 {self.family.kind}을 슈퍼관리자가 삭제하면, 삭제한 이름이 "
            "반환되고 이어서 검색하면 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]:
        return Purging(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Purged]:
        return TheNameIsAnsweredAndGone()


@dataclass(frozen=True)
class APolicyStillHeldIsRefused(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"purging-a-{self.family.label}-still-held-is-refused"

    @override
    def describe(self) -> str:
        return (
            f"아직 누군가에게 할당된 {self.family.kind}을 슈퍼관리자가 삭제하려 하면, "
            "아직 참조 중이라는 이유로 거부된다. 막는 것은 삭제 spec이 아니라 외래 키다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return AHeldPolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]:
        return Purging(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Purged]:
        return TheCallIsRefused(ForeignKeyViolationError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-granted-nothing-may-not-purge-a-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"같은 {self.family.kind}이 있고 아무 권한도 없는 사용자가 삭제하려 하면, "
            "삭제 로직에 이르기 전에 정책을 찾을 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]:
        return Purging(self.family)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Purged]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class ANameNothingAnswersToIsUnresolvable(
    Scenario[SeedingSession, APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"purging-a-{self.family.label}-name-nothing-answers-to-is-unresolvable"

    @override
    def describe(self) -> str:
        return (
            f"슈퍼관리자가 어느 {self.family.kind}에도 없는 이름을 삭제하려 하면, "
            "정책을 찾을 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller[Any]]:
        return APolicyAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller[Any], ResourcePolicyAdapter, Purged]:
        return Purging(self.family, named=NOBODY)

    @override
    def then(self) -> Then[APolicyAndACaller[Any], Purged]:
        return TheCallIsRefused(GenericBadRequest)


SCENARIOS: list[RetiringStep] = [
    *(TheSuperadminPurgesAnUnusedPolicy(family) for family in FAMILIES),
    *(APolicyStillHeldIsRefused(family) for family in FAMILIES),
    *(AUserGrantedNothingMayNotPurge(family) for family in FAMILIES),
    *(ANameNothingAnswersToIsUnresolvable(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
