"""도메인 읽기 — 세 단계 모양으로 쓴 것.

`given`이 값을 답하고, `when`은 그 값과 어댑터만 받고, `then`은 심은 것과 답을 함께 본다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

import pytest
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)

WAS_HERE = "이미 있던 도메인"

SKEW = timedelta(seconds=30)
"""두 시계가 어긋나 있어도 봐주는 폭."""


@dataclass(frozen=True)
class ADomainAndACaller:
    """읽기 시나리오가 세워 두는 것: 도메인 하나와, 그것을 부를 사람."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class ADomainAndSomeone(Given[SeedingSession, ADomainAndACaller]):
    """도메인 하나와 그 도메인에 속한 사용자 한 명."""

    role: UserRole

    @override
    def describe(self) -> str:
        return f"도메인 하나와, 그 도메인에 속한 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> ADomainAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="host", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ADomainAndACaller(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class ReadingByName(When[ADomainAndACaller, DomainAdapter, DomainNode]):
    """심은 도메인의 이름으로 읽는다."""

    named: str | None = None

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        asked = self.named or laid.domain.name
        return f"{laid.caller.username}이 {asked}으로 조회"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> DomainNode:
        with ActingAs(laid.caller):
            return await adapter.get(self.named or laid.domain.name)


@dataclass(frozen=True)
class WrittenByThisRun(Condition[datetime | None]):
    """이 실행이 쓴 시각. 값 자체는 실행마다 달라 레포트에 넣지 않는다."""

    started: datetime

    @override
    def says(self) -> str:
        return "이 실행이 쓴 시각"

    @override
    def holds(self, got: datetime | None) -> bool:
        if got is None or got.tzinfo is None:
            return False
        return self.started - SKEW <= got <= datetime.now(UTC) + SKEW


@dataclass(frozen=True)
class TheDomainComesBack(Then[ADomainAndACaller, DomainNode]):
    """심은 그 도메인이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 도메인 전체가 온다"

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[DomainNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Same("name", node.basic_info.name, laid.domain.name),
            Same("description", node.basic_info.description, WAS_HERE),
            Same("integration_name", node.basic_info.integration_name, None),
            Same("allowed_docker_registries", node.registry.allowed_docker_registries, []),
            Same("is_active", node.lifecycle.is_active, True),
            Same("is_default", node.lifecycle.is_default, False),
            Skipped("id", "데이터베이스가 만든다"),
            Held("created_at", node.lifecycle.created_at, written),
            Held("modified_at", node.lifecycle.modified_at, written),
        ]


@dataclass(frozen=True)
class TheCallIsRefused(Then[ADomainAndACaller, DomainNode]):
    """이 이름으로 거부된다."""

    expected: type[BaseException]

    @override
    def says(self) -> str:
        return "거부된다"

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[DomainNode]) -> list[Verdict]:
        return [Refused(self.expected, answered.raised)]


@dataclass(frozen=True)
class TheSuperadminReadsADomainByName(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-domain-by-name"

    @override
    def describe(self) -> str:
        return "도메인 하나가 있고 슈퍼관리자가 이름으로 조회하면, 그 도메인이 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return ReadingByName()

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheDomainComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-domain"

    @override
    def describe(self) -> str:
        return (
            "같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, "
            "이름으로 조회하면 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return ReadingByName()

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 이름으로 조회하면, 권한 문제가 아니라 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return ReadingByName(named="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS = [
    TheSuperadminReadsADomainByName(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    ANameNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode],
    adapter: DomainAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
