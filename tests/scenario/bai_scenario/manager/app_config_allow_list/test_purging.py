"""허용 목록 항목 영구 삭제 — 권한 검사와 종속 설정 조각의 처리를 확인한다.

설정 조각은 데이터베이스가 함께 삭제한다. 이 어댑터에는 soft delete가 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest

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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_allow_list import AnEntryAndACaller, AnEntryAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PurgeAppConfigAllowListPayload
type PurgingStep = Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]


@dataclass(frozen=True)
class Purging(When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]):
    """항목 하나를 영구 삭제한다. ID를 지정하지 않으면 준비한 항목을 삭제한다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: AnEntryAndACaller) -> str:
        called = "존재하지 않는 ID" if self.other is not None else f"{laid.name}의 항목"
        return f"{laid.caller.username}이 {called} 영구 삭제"

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
    """영구 삭제한 항목의 ID를 반환한다."""

    @override
    def says(self) -> str:
        return "영구 삭제한 허용 목록 항목의 ID가 반환된다"

    @override
    def look(self, laid: AnEntryAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None or laid.entry is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Held("id", payload.id, SameAs[UUID](laid.entry.id, "준비한 ID"))]


@dataclass(frozen=True)
class TheSuperadminPurgesIt(
    Scenario[SeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-an-entry"

    @override
    def describe(self) -> str:
        return "설정 조각이 없는 항목을 슈퍼관리자가 영구 삭제하면, 삭제한 항목의 ID가 반환된다"

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
        return "설정 조각이 있는 항목을 슈퍼관리자가 영구 삭제하면, 설정 조각이 막지 않고 항목의 ID가 반환된다"

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
        return (
            "같은 항목을 권한이 없는 일반 사용자가 영구 삭제하면, 엔티티 삭제 권한이 없어 거부된다"
        )

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
        return (
            "슈퍼관리자가 존재하지 않는 ID를 영구 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다"
        )

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
