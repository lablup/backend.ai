"""도메인 여럿을 id로 읽기. 자리마다 따로 답한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import (
    ADomainAndACaller,
    ATargetAndSomeone,
    DomainLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Answers = list[DomainNode | Exception | None]
type DomainStep = Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Answers]


@dataclass(frozen=True)
class ReadingByIds(When[ADomainAndACaller, DomainAdapter, Answers]):
    """미리 만든 도메인을 id로 읽는다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.domain.name}의 id로 여럿 읽기"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Answers:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([laid.domain.id])


@dataclass(frozen=True)
class TheOneDomainComesBack(Then[ADomainAndACaller, Answers]):
    """물은 자리 하나에 미리 만든 도메인 전체가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "물은 자리에 미리 만든 도메인 전체가 온다"

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[Answers]) -> list[Verdict]:
        answers = answered.response
        if answers is None:
            return [MissingResponse(answered.raised)]
        match answers:
            case [DomainNode() as node]:
                return DomainLook(self.started).verdicts("[0].", node, laid.domain)
            case _:
                return [Same("answers", [type(one).__name__ for one in answers], ["DomainNode"])]


@dataclass(frozen=True)
class TheOnePlaceIsRefused(Then[ADomainAndACaller, Answers]):
    """물은 자리 하나가 이 이름으로 거부된다. 호출 전체는 답한다."""

    expected: type[BaseException]

    @override
    def says(self) -> str:
        return "물은 자리가 거부된다"

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[Answers]) -> list[Verdict]:
        answers = answered.response
        if answers is None:
            return [MissingResponse(answered.raised)]
        match answers:
            case [Exception() as denial]:
                return [Refused(self.expected, denial)]
            case _:
                return [Same("answers", [type(one).__name__ for one in answers], ["거부"])]


@dataclass(frozen=True)
class TheSuperadminReadsById(Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Answers]):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-domains-by-id"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 id로 도메인 여럿을 읽으면, 그 자리에 도메인이 온다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Answers]:
        return ReadingByIds()

    @override
    def then(self) -> Then[ADomainAndACaller, Answers]:
        return TheOneDomainComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadById(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Answers]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-domains-by-id"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 id로 도메인 여럿을 읽으면, 그 자리가 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Answers]:
        return ReadingByIds()

    @override
    def then(self) -> Then[ADomainAndACaller, Answers]:
        return TheOnePlaceIsRefused(NotEnoughPermission)


SCENARIOS: list[DomainStep] = [
    TheSuperadminReadsById(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotReadById(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_reading(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
