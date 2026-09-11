"""허용 목록 항목 삭제 — 슈퍼관리자만 삭제할 수 있고, 딸린 설정 조각이 막지 않는다.

설정 조각은 데이터베이스가 함께 삭제한다. 이 어댑터에는 soft delete가 없다.
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
    """항목 하나를 삭제한다. id를 지정하지 않으면 미리 만들어 둔 항목을 삭제한다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: AnEntryAndACaller) -> str:
        called = "존재하지 않는 id" if self.other is not None else f"{laid.name}의 항목"
        return f"{laid.caller.username}이 {called} 삭제"

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
    """삭제한 항목이 무엇인지 id로 응답한다."""

    @override
    def says(self) -> str:
        return "삭제한 허용 목록 항목의 id를 응답한다"

    @override
    def look(self, laid: AnEntryAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None or laid.entry is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held("id", payload.id, SameAs[UUID](laid.entry.id, "미리 만들어 둔 허용 목록 항목"))
        ]


@dataclass(frozen=True)
class TheSuperadminPurgesIt(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-an-entry"

    @override
    def describe(self) -> str:
        return (
            "설정 조각이 딸리지 않은 항목을 슈퍼관리자가 삭제하면, 삭제한 id를 담은 응답이 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER, role=UserRole.SUPERADMIN)

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
        return "설정 조각이 딸린 항목을 슈퍼관리자가 삭제하면, 조각이 막지 않고 삭제한 id를 담은 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(role=UserRole.SUPERADMIN, with_fragment=True)

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
        return "a-user-who-is-not-the-superadmin-may-not-purge-an-entry"

    @override
    def describe(self) -> str:
        return "같은 항목이 있고 슈퍼관리자가 아닌 사용자가 삭제하면, 권한 부족으로 거부된다"

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
        return "슈퍼관리자가 존재하지 않는 id를 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다"

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
    TheSuperadminPurgesIt(),
    AFragmentDoesNotBlockIt(),
    AUserGrantedNothingMayNotPurge(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
