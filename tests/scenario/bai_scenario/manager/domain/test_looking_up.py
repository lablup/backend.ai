"""이름으로 도메인 id 찾기, 하나와 여럿. 인증만 보고, 권한은 id를 받는 호출이 본다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import ADomainAndACaller, ATargetAndSomeone, TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type DomainStep = Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainID]
type Found = list[DomainID | None]
type BulkStep = Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Found]

UNKNOWN = "no-such-domain"


@dataclass(frozen=True)
class LookingUpTheName(When[ADomainAndACaller, DomainAdapter, DomainID]):
    """이름으로 id를 찾는다. 이름을 대지 않으면 미리 만든 도메인의 이름을 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "lookup_name"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.domain.name}의 id를 찾음"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> DomainID:
        with ActingAs(laid.caller):
            return await adapter.lookup_name(self.named or laid.domain.name)


@dataclass(frozen=True)
class TheDomainsIdComesBack(Then[ADomainAndACaller, DomainID]):
    """그 이름을 가진 도메인의 id가 온다."""

    @override
    def says(self) -> str:
        return "그 도메인의 id가 온다"

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[DomainID]) -> list[Verdict]:
        found = answered.response
        if found is None:
            return [MissingResponse(answered.raised)]
        return [Held("id", found, SameAs(laid.domain.id, "미리 만든 도메인의 id"))]


@dataclass(frozen=True)
class TheSuperadminLooksUpAName(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainID]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-looks-up-a-domain-by-name"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 도메인 이름으로 id를 찾으면, 그 도메인의 id가 온다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainID]:
        return LookingUpTheName()

    @override
    def then(self) -> Then[ADomainAndACaller, DomainID]:
        return TheDomainsIdComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingStillLooksUpAName(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainID]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-still-looks-up-a-domain-by-name"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자도 도메인 이름으로 id를 찾을 수 있다. "
            "이 호출은 인증만 보고, 권한은 그 id를 받는 호출이 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainID]:
        return LookingUpTheName()

    @override
    def then(self) -> Then[ADomainAndACaller, DomainID]:
        return TheDomainsIdComesBack()


@dataclass(frozen=True)
class LookingUpNames(When[ADomainAndACaller, DomainAdapter, Found]):
    """미리 만든 도메인의 이름과 어느 도메인도 갖지 않은 이름으로 id를 여럿 찾는다."""

    @override
    def operation(self) -> str:
        return "bulk_lookup_names"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.domain.name}과 {UNKNOWN}의 id를 여럿 찾음"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Found:
        with ActingAs(laid.caller):
            return await adapter.bulk_lookup_names([laid.domain.name, UNKNOWN])


@dataclass(frozen=True)
class OnlyTheKnownNameHasAnId(Then[ADomainAndACaller, Found]):
    """있는 이름의 자리에 그 도메인의 id가, 없는 이름의 자리에 빈 값이 온다."""

    @override
    def says(self) -> str:
        return "있는 이름에는 그 도메인의 id, 없는 이름에는 빈 값이 온다"

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[Found]) -> list[Verdict]:
        found = answered.response
        if found is None:
            return [MissingResponse(answered.raised)]
        match found:
            case [known, unknown]:
                return [
                    Held[DomainID | None](
                        "[0]", known, SameAs(laid.domain.id, "미리 만든 도메인의 id")
                    ),
                    Same("[1]", unknown, None),
                ]
            case _:
                return [Same("len", len(found), 2)]


@dataclass(frozen=True)
class TheSuperadminLooksUpNames(Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Found]):
    @override
    def summary(self) -> str:
        return "the-superadmin-looks-up-domains-by-name"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 있는 이름과 없는 이름으로 id를 여럿 찾으면, "
            "있는 이름에는 그 도메인의 id, 없는 이름에는 빈 값이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Found]:
        return LookingUpNames()

    @override
    def then(self) -> Then[ADomainAndACaller, Found]:
        return OnlyTheKnownNameHasAnId()


@dataclass(frozen=True)
class AUserGrantedNothingGetsTheSameIds(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Found]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-the-same-ids-by-name"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 찾아도 슈퍼관리자와 같은 답이 온다. "
            "이 호출은 인증만 보므로 이름이 있는지는 누구에게나 드러난다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Found]:
        return LookingUpNames()

    @override
    def then(self) -> Then[ADomainAndACaller, Found]:
        return OnlyTheKnownNameHasAnId()


@dataclass(frozen=True)
class LookingUpNamesWithoutLogin(When[ADomainAndACaller, DomainAdapter, Found]):
    """로그인 문맥 없이 미리 만든 도메인의 이름으로 id를 여럿 찾는다."""

    @override
    def operation(self) -> str:
        return "bulk_lookup_names"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"로그인 문맥 없이 {laid.domain.name}의 id를 여럿 찾음"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Found:
        return await adapter.bulk_lookup_names([laid.domain.name])


@dataclass(frozen=True)
class ACallWithoutLoginIsRefused(Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Found]):
    @override
    def summary(self) -> str:
        return "looking-up-domains-by-name-without-login-is-refused"

    @override
    def describe(self) -> str:
        return "로그인 문맥 없이 이름으로 id를 여럿 찾으면, 사용자를 찾을 수 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Found]:
        return LookingUpNamesWithoutLogin()

    @override
    def then(self) -> Then[ADomainAndACaller, Found]:
        return TheCallIsRefused(UserNotFound)


BULK_SCENARIOS: list[BulkStep] = [
    TheSuperadminLooksUpNames(),
    AUserGrantedNothingGetsTheSameIds(),
    ACallWithoutLoginIsRefused(),
]


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainID]
):
    @override
    def summary(self) -> str:
        return "looking-up-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "아무 도메인도 갖지 않은 이름으로 id를 찾으면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainID]:
        return LookingUpTheName(named=UNKNOWN)

    @override
    def then(self) -> Then[ADomainAndACaller, DomainID]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[DomainStep] = [
    TheSuperadminLooksUpAName(),
    AUserGrantedNothingStillLooksUpAName(),
    ANameNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_looking_up(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", BULK_SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_looking_up(
    scenario: BulkStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
