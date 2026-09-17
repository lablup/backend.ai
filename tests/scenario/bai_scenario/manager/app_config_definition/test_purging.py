"""설정 정의 영구 삭제 — 엔티티 권한과 종속 행 처리를 확인한다.

허용 목록 항목과 설정 조각은 데이터베이스 외래 키에 따라 함께 삭제된다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    PurgeAppConfigDefinitionInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    PurgeAppConfigDefinitionPayload,
)
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
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
from bai_scenario.components.app_config_definition import (
    ADefinitionAndACaller,
    ADefinitionAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PurgeAppConfigDefinitionPayload
type PurgingStep = Scenario[
    SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged
]


@dataclass(frozen=True)
class Purging(When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]):
    """설정 정의 하나를 영구 삭제한다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: ADefinitionAndACaller) -> str:
        called = "존재하지 않는 ID" if self.other is not None else laid.definition.config_name
        return f"{laid.caller.username}이 {called} 영구 삭제"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ADefinitionAndACaller
    ) -> Purged:
        wanted = self.other if self.other is not None else laid.definition.id
        with ActingAs(laid.caller):
            return await adapter.admin_purge(PurgeAppConfigDefinitionInput(id=wanted))


@dataclass(frozen=True)
class ThePurgedOneIsNamed(Then[ADefinitionAndACaller, Purged]):
    """영구 삭제한 설정 정의의 ID를 응답한다."""

    @override
    def says(self) -> str:
        return "영구 삭제한 설정 정의의 ID를 응답한다"

    @override
    def look(self, laid: ADefinitionAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held("ID", payload.id, SameAs[UUID](laid.definition.id, "미리 만들어 둔 설정 정의"))
        ]


@dataclass(frozen=True)
class TheSuperadminPurgesIt(
    Scenario[SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-definition"

    @override
    def describe(self) -> str:
        return "종속 행이 없는 설정 정의를 슈퍼관리자가 영구 삭제하면, 삭제한 ID가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ADefinitionAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class EntriesAndFragmentsDoNotBlockIt(
    Scenario[SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-definition-holding-an-entry-and-a-fragment-is-still-purged"

    @override
    def describe(self) -> str:
        return "허용 목록 항목과 설정 조각이 딸린 설정 정의를 슈퍼관리자가 영구 삭제하면, 종속 행이 삭제를 막지 않고 정의의 ID가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN, with_fragment=True)

    @override
    def when(self) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ADefinitionAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-purge-a-definition"

    @override
    def describe(self) -> str:
        return "같은 설정 정의가 있고 권한이 없는 일반 사용자가 영구 삭제하면, 엔티티 영구 삭제 권한이 없어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone()

    @override
    def when(self) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ADefinitionAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
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
    def given(self) -> Given[SeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]:
        return Purging(other=uuid4())

    @override
    def then(self) -> Then[ADefinitionAndACaller, Purged]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesIt(),
    EntriesAndFragmentsDoNotBlockIt(),
    AUserGrantedNothingMayNotPurge(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
