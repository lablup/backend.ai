"""도메인 자원 개요 조회 — 도메인 이름을 풀어낸 뒤, 그 도메인 범위의 세션 조회 권한을 검사하고 집계한다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.response import ActiveResourceOverviewInfoDTO
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_allocation import (
    AKernelAndACaller,
    AKernelAndSomeone,
    Granted,
    NothingIsOccupied,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

UNKNOWN = "no-such-domain"

type Overview = ActiveResourceOverviewInfoDTO
type OverviewStep = Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, Overview]


@dataclass(frozen=True)
class ReadingTheDomainOverview(When[AKernelAndACaller, ResourceSlotAdapter, Overview]):
    """도메인 이름으로 개요를 조회한다. 지정하지 않으면 커널이 속한 도메인의 이름을 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "get_domain_resource_overview"

    @override
    def describe(self, laid: AKernelAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.domain.name} 도메인의 개요 조회"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: AKernelAndACaller) -> Overview:
        with ActingAs(laid.caller):
            return await adapter.get_domain_resource_overview(self.named or laid.domain.name)


@dataclass(frozen=True)
class TheSuperadminReadsADomainOverview(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, Overview]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-domain-overview-that-counts-no-pending-kernel"

    @override
    def describe(self) -> str:
        return (
            "대기 중인 커널만 있는 도메인의 개요를 슈퍼관리자가 조회하면 점유된 슬롯이 없고 세션 수가 0이다. "
            "개요는 자원을 점유했거나 배정받은 커널만 세고, 요구만 한 커널은 세지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, Overview]:
        return ReadingTheDomainOverview()

    @override
    def then(self) -> Then[AKernelAndACaller, Overview]:
        return NothingIsOccupied()


@dataclass(frozen=True)
class AUserReadingSessionsInTheDomainReadsItsOverview(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, Overview]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-sessions-in-the-domain-reads-its-overview"

    @override
    def describe(self) -> str:
        return "도메인 범위에서 세션을 읽을 수 있는 사용자가 그 도메인의 개요를 조회하면 개요가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone(granted=Granted.THE_DOMAIN)

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, Overview]:
        return ReadingTheDomainOverview()

    @override
    def then(self) -> Then[AKernelAndACaller, Overview]:
        return NothingIsOccupied()


@dataclass(frozen=True)
class AUserReadingSessionsInTheProjectMayNotReadTheDomainOverview(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, Overview]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-sessions-in-the-project-may-not-read-the-domain-overview"

    @override
    def describe(self) -> str:
        return (
            "프로젝트 범위에서만 세션을 읽을 수 있는 사용자가 그 프로젝트가 속한 도메인의 개요를 조회하면 "
            "권한 부족으로 거부된다. 도메인 개요는 도메인 범위의 권한을 검사한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone(granted=Granted.THE_PROJECT)

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, Overview]:
        return ReadingTheDomainOverview()

    @override
    def then(self) -> Then[AKernelAndACaller, Overview]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadADomainOverview(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, Overview]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-domain-overview"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 조회하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone()

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, Overview]:
        return ReadingTheDomainOverview()

    @override
    def then(self) -> Then[AKernelAndACaller, Overview]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ADomainNameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, Overview]
):
    @override
    def summary(self) -> str:
        return "reading-the-overview-of-a-domain-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "존재하지 않는 도메인 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, Overview]:
        return ReadingTheDomainOverview(named=UNKNOWN)

    @override
    def then(self) -> Then[AKernelAndACaller, Overview]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneReadADomainOverview(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, Overview], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-read-a-domain-overview"

    @override
    def describe(self) -> str:
        return "권한 검사를 끄면 아무 권한도 없는 사용자도 도메인의 개요를 조회할 수 있다"

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone()

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, Overview]:
        return ReadingTheDomainOverview()

    @override
    def then(self) -> Then[AKernelAndACaller, Overview]:
        return NothingIsOccupied()


SCENARIOS: list[OverviewStep] = [
    TheSuperadminReadsADomainOverview(),
    AUserReadingSessionsInTheDomainReadsItsOverview(),
    AUserReadingSessionsInTheProjectMayNotReadTheDomainOverview(),
    AUserGrantedNothingMayNotReadADomainOverview(),
    ADomainNameNothingAnswersToIsNotFound(),
    EnforcementOffLetsAnyoneReadADomainOverview(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_domain_overview(
    scenario: OverviewStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
