"""허용 항목 지우기 — 누가 지울 수 있고, 딸린 조각이 막지 않는다.

조각은 데이터베이스가 함께 지운다. 이 어댑터에는 soft delete가 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_allow_list import AnEntryAndACaller, AnEntryAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    PurgeAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    PurgeAppConfigAllowListPayload,
)
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)

type Purged = PurgeAppConfigAllowListPayload
type PurgingStep = Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]


@dataclass(frozen=True)
class Purging(When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]):
    """항목 하나를 지운다. id를 대지 않으면 심은 항목을 지운다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: AnEntryAndACaller) -> str:
        called = "아무것도 갖지 않은 id" if self.other is not None else f"{laid.name}의 항목"
        return f"{laid.caller.username}이 {called}을 지움"

    @override
    async def call(self, adapter: AppConfigAllowListAdapter, laid: AnEntryAndACaller) -> Purged:
        if self.other is not None:
            wanted = self.other
        elif laid.entry is not None:
            wanted = laid.entry.id
        else:
            raise LookupError("this row lays no entry to purge")
        with ActingAs(laid.caller):
            return await adapter.admin_purge(PurgeAppConfigAllowListInput(id=wanted))


@dataclass(frozen=True)
class ThePurgedOneIsNamed(Then[AnEntryAndACaller, Purged]):
    """지운 항목이 무엇인지 id로 답한다."""

    @override
    def says(self) -> str:
        return "지운 허용 항목의 id를 답한다"

    @override
    def look(self, laid: AnEntryAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None or laid.entry is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Held("id", payload.id, SameAs[UUID](laid.entry.id, "심은 허용 항목"))]


@dataclass(frozen=True)
class TheGrantedUserPurgesIt(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-on-the-entry-purges-it"

    @override
    def describe(self) -> str:
        return (
            "조각이 딸리지 않은 항목에 지우기 권한을 받은 사용자가 지우면, 지운 id를 실은 답이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER, granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AnEntryAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class AFragmentDoesNotBlockIt(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "an-entry-holding-a-fragment-is-still-purged"

    @override
    def describe(self) -> str:
        return "조각이 딸린 항목을 지우기 권한을 받은 사용자가 지우면, 조각이 막지 않고 지운 id를 실은 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(granted=(Permission.HARD_DELETE,), with_fragment=True)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AnEntryAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-an-entry"

    @override
    def describe(self) -> str:
        return "같은 항목이 있고 아무 권한도 받지 않은 사용자가 지우면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AnEntryAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]:
        return Purging(other=uuid4())

    @override
    def then(self) -> Then[AnEntryAndACaller, Purged]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[PurgingStep] = [
    TheGrantedUserPurgesIt(),
    AFragmentDoesNotBlockIt(),
    AUserGrantedNothingMayNotPurge(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
