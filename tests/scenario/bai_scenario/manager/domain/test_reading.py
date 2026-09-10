"""도메인 읽기 — 누가 무엇을 읽을 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest
from bai_scenario.components.domain import (
    ADomainAndACaller,
    ADomainAndSomeone,
    TheCallIsRefused,
    TheDomainNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type DomainStep = Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]


@dataclass(frozen=True)
class ReadingByName(When[ADomainAndACaller, DomainAdapter, DomainNode]):
    """이름으로 읽는다. 이름을 대지 않으면 심은 도메인의 이름을 쓴다."""

    named: str | None = None

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.domain.name}으로 조회"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> DomainNode:
        with ActingAs(laid.caller):
            return await adapter.get(self.named or laid.domain.name)


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
        return TheDomainNode(started=self.started)


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
        return ADomainAndSomeone()

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
        return (
            "슈퍼관리자가 존재하지 않는 이름으로 조회하면, "
            "권한 문제가 아니라 대상이 없다는 것으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return ReadingByName(named="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[DomainStep] = [
    TheSuperadminReadsADomainByName(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    ANameNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
