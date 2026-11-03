"""도메인 soft delete, restore, purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import PurgeDomainInput
from ai.backend.common.dto.manager.v2.domain.response import (
    DeleteDomainPayload,
    PurgeDomainPayload,
    RestoreDomainPayload,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import DomainHasGroups, DomainHasUsers
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import (
    ADomainAndACaller,
    ATargetAndSomeone,
    TargetHolds,
    TheCallIsRefused,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = DeleteDomainPayload | RestoreDomainPayload | PurgeDomainPayload
type DomainStep = Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]


@dataclass(frozen=True)
class SoftDeleting(When[ADomainAndACaller, DomainAdapter, Deleted]):
    """도메인을 soft delete 한다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        name = self.named or laid.domain.name
        return Says(
            f"{laid.caller.username}이 {name}을 soft delete 합니다",
            english=f"{laid.caller.username} soft deletes {name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.delete(await adapter.lookup_name(self.named or laid.domain.name))


@dataclass(frozen=True)
class SoftDeletingThenRestoring(When[ADomainAndACaller, DomainAdapter, Deleted]):
    """soft delete 한 다음 restore 한다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}을 soft delete 한 뒤 restore 합니다",
            english=(
                f"{laid.caller.username} soft deletes {laid.domain.name} and then restores it"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            await adapter.delete(await adapter.lookup_name(laid.domain.name))
            return await adapter.restore(await adapter.lookup_name(laid.domain.name))


@dataclass(frozen=True)
class SoftDeletingTwice(When[ADomainAndACaller, DomainAdapter, Deleted]):
    """soft delete 를 두 번 부른다. 두 번째 답을 준다."""

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}을 두 번 soft delete 합니다",
            english=f"{laid.caller.username} soft deletes {laid.domain.name} twice",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            await adapter.delete(await adapter.lookup_name(laid.domain.name))
            return await adapter.delete(await adapter.lookup_name(laid.domain.name))


@dataclass(frozen=True)
class Restoring(When[ADomainAndACaller, DomainAdapter, Deleted]):
    """미리 만든 그대로의 도메인을 restore 한다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}을 restore 합니다",
            english=f"{laid.caller.username} restores {laid.domain.name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.restore(await adapter.lookup_name(laid.domain.name))


@dataclass(frozen=True)
class Purging(When[ADomainAndACaller, DomainAdapter, Deleted]):
    """purge 한다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        name = self.named or laid.domain.name
        return Says(
            f"{laid.caller.username}이 {name}을 purge 합니다",
            english=f"{laid.caller.username} purges {name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ADomainAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.purge(PurgeDomainInput(name=self.named or laid.domain.name))


@dataclass(frozen=True)
class ItSaysItWasDone(Then[ADomainAndACaller, Deleted]):
    """했다는 답이 온다. 답이 실은 것은 그 한 가지뿐이다."""

    called: str

    @override
    def says(self) -> str:
        return Says(
            "했다는 응답이 옵니다",
            english="the answer says it was done",
        )

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[Deleted]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same(self.called, getattr(payload, self.called), True)]


@dataclass(frozen=True)
class TheSuperadminSoftDeletesADomain(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-soft-deletes-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 도메인을 soft delete 하면, soft delete 했다는 응답이 옵니다",
            english="when the superadmin soft deletes a domain, the answer says it was done",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="to-delete")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return SoftDeleting()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return ItSaysItWasDone("deleted")


@dataclass(frozen=True)
class RestoringSaysItRestored(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "restoring-answers-that-it-restored"

    @override
    def describe(self) -> str:
        return Says(
            "soft delete 된 도메인을 restore 하면, restore 했다는 응답이 옵니다",
            english="when a soft-deleted domain is restored, the answer says it was restored",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="to-restore")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return SoftDeletingThenRestoring()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return ItSaysItWasDone("restored")


@dataclass(frozen=True)
class PurgingADomainNothingRefersTo(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "purging-a-domain-nothing-else-refers-to-succeeds"

    @override
    def describe(self) -> str:
        return Says(
            "아무것도 딸려 있지 않은 도메인은 purge 할 수 있습니다",
            english="a domain nothing else refers to can be purged",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="to-purge")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return Purging()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return ItSaysItWasDone("purged")


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "soft-deleting-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "아무 도메인도 갖지 않은 이름을 soft delete 하려 하면 대상이 없다는 것으로 거부됩니다",
            english=("soft-deleting a name no domain answers to is rejected as not found"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return SoftDeleting(named="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSoftDelete(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-soft-delete-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 도메인을 soft delete 할 수 없습니다",
            english="a user granted nothing cannot soft delete a domain",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(name_hint="untouchable")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return SoftDeleting()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class SoftDeletingASoftDeletedDomainAgain(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "soft-deleting-a-domain-already-soft-deleted"

    @override
    def describe(self) -> str:
        return Says(
            "이미 soft delete 된 도메인을 superadmin 이 다시 soft delete 하면, "
            "soft delete 했다는 응답이 옵니다",
            english=(
                "when the superadmin soft deletes an already soft-deleted domain again, "
                "the answer says it was done"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="twice")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return SoftDeletingTwice()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return ItSaysItWasDone("deleted")


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestore(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 도메인을 restore 할 수 없습니다",
            english="a user granted nothing cannot restore a domain",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(name_hint="untouchable")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return Restoring()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RestoringAnActiveDomain(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "restoring-a-domain-that-is-not-soft-deleted"

    @override
    def describe(self) -> str:
        return Says(
            "soft delete 되지 않은 도메인을 superadmin 이 restore 하면, "
            "restore 했다는 응답이 옵니다",
            english=(
                "when the superadmin restores a domain that is not soft-deleted, "
                "the answer says it was restored"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, name_hint="active")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return Restoring()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return ItSaysItWasDone("restored")


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 아무것도 딸리지 않은 도메인이라도 purge 할 수 없습니다",
            english=(
                "a user granted nothing cannot purge a domain even when nothing else refers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(name_hint="untouchable")

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return Purging()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ADomainHoldingAProjectIsNotPurged(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-domain-holding-a-project-is-not-purged"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트가 딸린 도메인은 superadmin 이라도 purge 할 수 없습니다",
            english="a domain holding a project cannot be purged even by the superadmin",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, holds=TargetHolds.PROJECT)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return Purging()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return TheCallIsRefused(DomainHasGroups)


@dataclass(frozen=True)
class ADomainHoldingAUserIsNotPurged(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-domain-holding-a-user-is-not-purged"

    @override
    def describe(self) -> str:
        return Says(
            "사용자가 딸린 도메인은 superadmin 이라도 purge 할 수 없습니다",
            english="a domain holding a user cannot be purged even by the superadmin",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN, holds=TargetHolds.USER)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return Purging()

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return TheCallIsRefused(DomainHasUsers)


@dataclass(frozen=True)
class PurgingANameNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, ADomainAndACaller, DomainAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "purging-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "아무 도메인도 갖지 않은 이름을 purge 하려 하면 대상이 없다는 것으로 거부됩니다",
            english="purging a name no domain answers to is rejected as not found",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ATargetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, DomainAdapter, Deleted]:
        return Purging(named="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[DomainStep] = [
    TheSuperadminSoftDeletesADomain(),
    RestoringSaysItRestored(),
    PurgingADomainNothingRefersTo(),
    ANameNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotSoftDelete(),
    SoftDeletingASoftDeletedDomainAgain(),
    AUserGrantedNothingMayNotRestore(),
    RestoringAnActiveDomain(),
    AUserGrantedNothingMayNotPurge(),
    ADomainHoldingAProjectIsNotPurged(),
    ADomainHoldingAUserIsNotPurged(),
    PurgingANameNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deleting(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
