"""allow_list 영구 삭제 — 권한 검사와 종속 설정 조각의 처리를 확인한다.

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
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_allow_list import AnEntryAndACaller, AnEntryAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PurgeAppConfigAllowListPayload
type PurgingStep = Scenario[
    TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged
]


@dataclass(frozen=True)
class Purging(When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]):
    """allow_list 하나를 영구 삭제한다. ID를 지정하지 않으면 준비한 allow_list를 삭제한다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AnEntryAndACaller) -> str:
        if self.other is not None:
            called_ko, called_en = "존재하지 않는 ID", "a missing ID"
        else:
            called_ko = f"{laid.name}의 allow_list"
            called_en = f"the allow_list of {laid.name}"
        return Says(
            f"{laid.caller.username}이 {called_ko} 영구 삭제합니다",
            english=f"{laid.caller.username} purges {called_en}",
        )

    @override
    async def call(self, adapter: AppConfigAllowListAdapter, laid: AnEntryAndACaller) -> Purged:
        if self.other is not None:
            wanted = self.other
        elif laid.entry is not None:
            wanted = laid.entry.id
        else:
            raise LookupError("this row lays no entry to purge")
        with ActingAs(laid.caller):
            return await adapter.purge(PurgeAppConfigAllowListInput(id=wanted))


@dataclass(frozen=True)
class ThePurgedOneIsNamed(Then[AnEntryAndACaller, Purged]):
    """영구 삭제한 allow_list의 ID를 반환한다."""

    @override
    def says(self) -> str:
        return Says(
            "영구 삭제한 allow_list 의 ID 가 반환됩니다",
            english="the ID of the purged allow_list comes back",
        )

    @override
    def look(self, laid: AnEntryAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None or laid.entry is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held(
                "id",
                payload.id,
                SameAs[UUID](laid.entry.id, Says("준비한 ID", english="the ID seeded in advance")),
            )
        ]


@dataclass(frozen=True)
class TheSuperadminPurgesIt(
    Scenario[TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-an-entry"

    @override
    def describe(self) -> str:
        return Says(
            "설정 조각이 없는 allow_list 를 superadmin 이 영구 삭제하면, "
            "삭제한 allow_list 의 ID 가 반환됩니다",
            english=(
                "when the superadmin purges an allow_list with no config fragment, "
                "the ID of the purged allow_list comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AnEntryAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class AFragmentDoesNotBlockIt(
    Scenario[TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "an-entry-holding-a-fragment-is-still-purged"

    @override
    def describe(self) -> str:
        return Says(
            "설정 조각이 있는 allow_list 를 superadmin 이 영구 삭제하면, 설정 조각이 차단하지 않고 "
            "allow_list 의 ID 가 반환됩니다",
            english=(
                "when the superadmin purges an allow_list that has a config fragment, "
                "the fragment does not block it and the ID of the allow_list comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(role=UserRole.SUPERADMIN, with_fragment=True)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AnEntryAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-purge-an-entry"

    @override
    def describe(self) -> str:
        return Says(
            "같은 allow_list 를 권한이 없는 일반 사용자가 영구 삭제하면, "
            "엔티티 삭제 권한이 없어 거부됩니다",
            english=(
                "when a plain user without permission purges the same allow_list, "
                "the call is rejected because the user has no entity delete permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AnEntryAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 ID 를 영구 삭제하면, "
            "대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin purges a missing ID, "
                "the call is rejected because there is no such target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEntryAndACaller]:
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
