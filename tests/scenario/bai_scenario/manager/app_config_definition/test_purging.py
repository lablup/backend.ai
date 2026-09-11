"""정의 지우기 — 슈퍼관리자만 지우고, 딸린 것이 막지 않는다.

허용 항목과 조각은 데이터베이스가 함께 지운다. 이 어댑터에는 soft delete가 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_definition import (
    ADefinitionAndACaller,
    ADefinitionAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

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

type Purged = PurgeAppConfigDefinitionPayload
type PurgingStep = Scenario[
    SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged
]


@dataclass(frozen=True)
class Purging(When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]):
    """정의 하나를 지운다. id를 대지 않으면 심은 정의를 지운다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: ADefinitionAndACaller) -> str:
        called = "아무것도 갖지 않은 id" if self.other is not None else laid.definition.config_name
        return f"{laid.caller.username}이 {called}를 지움"

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ADefinitionAndACaller
    ) -> Purged:
        wanted = self.other if self.other is not None else laid.definition.id
        with ActingAs(laid.caller):
            return await adapter.admin_purge(PurgeAppConfigDefinitionInput(id=wanted))


@dataclass(frozen=True)
class ThePurgedOneIsNamed(Then[ADefinitionAndACaller, Purged]):
    """지운 정의가 무엇인지 id로 답한다."""

    @override
    def says(self) -> str:
        return "지운 정의의 id를 답한다"

    @override
    def look(self, laid: ADefinitionAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Held("id", payload.id, SameAs[UUID](laid.definition.id, "심은 정의"))]


@dataclass(frozen=True)
class TheSuperadminPurgesIt(
    Scenario[SeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-definition"

    @override
    def describe(self) -> str:
        return "아무것도 딸리지 않은 정의를 슈퍼관리자가 지우면, 지운 id를 실은 답이 온다"

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
        return "허용 항목과 조각이 딸린 정의를 슈퍼관리자가 지우면, 딸린 것이 막지 않고 지운 id를 실은 답이 온다"

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
        return "같은 정의가 있고 슈퍼관리자가 아닌 사용자가 지우면, 권한 부족으로 거부된다"

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
        return "슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다"

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
