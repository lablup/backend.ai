"""도메인 이름으로 도메인 id 를 찾기 — 있는 이름과 없는 이름."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain

NO_SUCH_DOMAIN = "no-such-domain"


@dataclass(frozen=True)
class ADomainAndACaller:
    """id 를 찾을 도메인과, 찾을 사람."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class SomeoneInADomain(Given[Any, ADomainAndACaller]):
    """도메인 하나와 그 도메인에 속한 사용자 한 명."""

    @override
    def describe(self) -> str:
        return Says(
            "도메인 하나와, 그 도메인에 속한 사용자 한 명",
            english="one domain and one user in it",
        )

    @override
    async def lay(self, seeding: Any) -> ADomainAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        return ADomainAndACaller(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class ResolvingAName(When[ADomainAndACaller, UserAdapter, DomainID]):
    """이름을 도메인 id 로 바꾼다. 이름을 대지 않으면 미리 만든 도메인의 이름을 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "resolve_domain_id"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        name = self.named or laid.domain.name
        return Says(
            f"{laid.caller.username}이 {name}의 id 를 찾습니다",
            english=f"{laid.caller.username} resolves the id of {name}",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ADomainAndACaller) -> DomainID:
        with ActingAs(laid.caller):
            return await adapter.resolve_domain_id(self.named or laid.domain.name)


@dataclass(frozen=True)
class TheDomainsIdComesBack(Then[ADomainAndACaller, DomainID]):
    """그 이름을 가진 도메인의 id 가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "그 도메인의 id 가 응답으로 옵니다",
            english="the id of that domain comes back",
        )

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[DomainID]) -> list[Verdict]:
        found = answered.response
        if found is None:
            return [Same("raised", type(answered.raised).__name__, None)]
        return [
            Held(
                "id",
                found,
                SameAs(
                    laid.domain.id,
                    Says(
                        "미리 저장한 도메인의 id", english="the id of the domain seeded in advance"
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, ADomainAndACaller, UserAdapter, DomainID]
):
    @override
    def summary(self) -> str:
        return "resolving-a-domain-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "아무 도메인도 갖지 않은 이름으로 id 를 찾으면, 대상이 없다는 것으로 거부됩니다",
            english="resolving a name no domain answers to is rejected as not found",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return SomeoneInADomain()

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, DomainID]:
        return ResolvingAName(named=NO_SUCH_DOMAIN)

    @override
    def then(self) -> Then[ADomainAndACaller, DomainID]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserResolvesTheDomainName(
    Scenario[TestSeedingSession, ADomainAndACaller, UserAdapter, DomainID]
):
    @override
    def summary(self) -> str:
        return "a-user-resolves-the-id-of-a-domain-by-its-name"

    @override
    def describe(self) -> str:
        return Says(
            "도메인에 속한 사용자가 그 도메인의 이름으로 id 를 찾으면, 그 도메인의 id 가 응답으로 "
            "옵니다",
            english=("when a user in a domain resolves its name, the id of that domain comes back"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return SomeoneInADomain()

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, DomainID]:
        return ResolvingAName()

    @override
    def then(self) -> Then[ADomainAndACaller, DomainID]:
        return TheDomainsIdComesBack()


SCENARIOS: list[Scenario[TestSeedingSession, ADomainAndACaller, UserAdapter, DomainID]] = [
    AUserResolvesTheDomainName(),
    ANameNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_resolving_domain(
    scenario: Scenario[TestSeedingSession, ADomainAndACaller, UserAdapter, DomainID],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
