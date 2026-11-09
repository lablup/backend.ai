"""도메인 읽기 — 누가 무엇을 읽을 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.domain import (
    ADomainAndACaller,
    ADomainAndSomeone,
    ATargetAndSomeone,
    TheCallIsRefused,
    TheDomainNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type DomainStep = Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]


@dataclass(frozen=True)
class ReadingByName(When[ADomainAndACaller, DomainAdapter, DomainNode]):
    """이름으로 읽는다. 이름을 대지 않으면 미리 만든 도메인의 이름을 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        name = self.named or laid.domain.name
        return Says(
            f"{laid.caller.username}이 {name}으로 조회합니다",
            english=f"{laid.caller.username} reads a domain by name {name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> DomainNode:
        with ActingAs(laid.caller):
            return await adapter.get(self.named or laid.domain.name)


@dataclass(frozen=True)
class SoftDeletingThenReading(When[ADomainAndACaller, DomainAdapter, DomainNode]):
    """미리 만든 도메인을 soft delete 한 뒤 이름으로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}을 soft delete 한 뒤 이름으로 조회합니다",
            english=(
                f"{laid.caller.username} soft deletes {laid.domain.name} and then reads it by name"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> DomainNode:
        with ActingAs(laid.caller):
            await adapter.delete(await adapter.lookup_name(laid.domain.name))
            return await adapter.get(laid.domain.name)


@dataclass(frozen=True)
class TheSuperadminReadsADomainByName(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-domain-by-name"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 하나가 있고 superadmin 이 이름으로 조회하면, 그 도메인이 응답으로 옵니다",
            english=(
                "with one domain laid, when the superadmin reads it by name, that domain comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return ReadingByName()

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheDomainNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "같은 도메인이 있고 사용자가 아무 권한도 받지 않았을 때, "
            "이름으로 조회하면 권한 부족으로 거부됩니다",
            english=(
                "with the same domain laid, when a user granted nothing reads it by name, "
                "the call is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return ReadingByName()

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 이름으로 조회하면, "
            "권한 문제가 아니라 대상이 없다는 것으로 거부됩니다",
            english=(
                "when the superadmin reads by a name that does not exist, "
                "the call is rejected as not found, not for a permission problem"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return ReadingByName(named="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class ASoftDeletedDomainIsStillRead(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, DomainNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-soft-deleted-domain-by-name"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 도메인을 soft delete 한 뒤 이름으로 조회하면, "
            "비활성 상태를 담은 그 도메인이 응답으로 옵니다",
            english=(
                "when the superadmin soft deletes a domain and then reads it by name, "
                "that domain comes back carrying the inactive state"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="soft-deleted")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, DomainNode]:
        return SoftDeletingThenReading()

    @override
    def then(self) -> Then[ADomainAndACaller, DomainNode]:
        return TheDomainNode(started=self.started, active=False)


SCENARIOS: list[DomainStep] = [
    TheSuperadminReadsADomainByName(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    ANameNothingAnswersToIsNotFound(),
    ASoftDeletedDomainIsStillRead(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
