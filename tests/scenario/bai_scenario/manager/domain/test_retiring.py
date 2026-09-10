"""도메인 물리기, 되살리기, 지우기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.domain import (
    ADomainAndACaller,
    ATargetAndSomeone,
    TheCallIsRefused,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import (
    DeleteDomainInput,
    PurgeDomainInput,
    RestoreDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DeleteDomainPayload,
    PurgeDomainPayload,
    RestoreDomainPayload,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
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

type Retired = DeleteDomainPayload | RestoreDomainPayload | PurgeDomainPayload
type DomainStep = Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Retired]


@dataclass(frozen=True)
class Retiring(When[ADomainAndACaller, DomainAdapter, Retired]):
    """도메인을 물린다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "admin_delete"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.domain.name}을 물림"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Retired:
        with ActingAs(laid.caller):
            return await adapter.admin_delete(
                DeleteDomainInput(name=self.named or laid.domain.name)
            )


@dataclass(frozen=True)
class RetiringThenRestoring(When[ADomainAndACaller, DomainAdapter, Retired]):
    """물린 다음 되살린다. 되살리려면 먼저 물려 있어야 한다."""

    @override
    def operation(self) -> str:
        return "admin_restore"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.domain.name}을 물렸다가 되살림"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Retired:
        with ActingAs(laid.caller):
            await adapter.admin_delete(DeleteDomainInput(name=laid.domain.name))
            return await adapter.admin_restore(RestoreDomainInput(name=laid.domain.name))


@dataclass(frozen=True)
class Purging(When[ADomainAndACaller, DomainAdapter, Retired]):
    """완전히 지운다."""

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.domain.name}을 완전히 지움"

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Retired:
        with ActingAs(laid.caller):
            return await adapter.admin_purge(PurgeDomainInput(name=laid.domain.name))


@dataclass(frozen=True)
class ItSaysItWasDone(Then[ADomainAndACaller, Retired]):
    """했다는 답이 온다. 답이 실은 것은 그 한 가지뿐이다."""

    called: str

    @override
    def says(self) -> str:
        return "했다는 답이 온다"

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[Retired]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same(self.called, getattr(payload, self.called), True)]


@dataclass(frozen=True)
class TheSuperadminRetiresADomain(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Retired]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-retires-a-domain"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 도메인을 물리면, 물렸다는 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="to-delete")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Retired]:
        return Retiring()

    @override
    def then(self) -> Then[ADomainAndACaller, Retired]:
        return ItSaysItWasDone("deleted")


@dataclass(frozen=True)
class RestoringSaysItRestored(Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Retired]):
    @override
    def summary(self) -> str:
        return "restoring-answers-that-it-restored"

    @override
    def describe(self) -> str:
        return "물렸던 도메인을 되살리면, 되살렸다는 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="to-restore")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Retired]:
        return RetiringThenRestoring()

    @override
    def then(self) -> Then[ADomainAndACaller, Retired]:
        return ItSaysItWasDone("restored")


@dataclass(frozen=True)
class PurgingADomainNothingRefersTo(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Retired]
):
    @override
    def summary(self) -> str:
        return "purging-a-domain-nothing-else-refers-to-succeeds"

    @override
    def describe(self) -> str:
        return "아무것도 딸려 있지 않은 도메인은 완전히 지울 수 있다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="to-purge")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Retired]:
        return Purging()

    @override
    def then(self) -> Then[ADomainAndACaller, Retired]:
        return ItSaysItWasDone("purged")


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Retired]
):
    @override
    def summary(self) -> str:
        return "retiring-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "아무 도메인도 갖지 않은 이름을 물리려 하면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Retired]:
        return Retiring(named="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, Retired]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRetire(
    Scenario[SeedingSession, ADomainAndACaller, DomainAdapter, Retired]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-retire-a-domain"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자는 도메인을 물릴 수 없다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(name_hint="untouchable")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Retired]:
        return Retiring()

    @override
    def then(self) -> Then[ADomainAndACaller, Retired]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[DomainStep] = [
    TheSuperadminRetiresADomain(),
    RestoringSaysItRestored(),
    PurgingADomainNothingRefersTo(),
    ANameNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotRetire(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
