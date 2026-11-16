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
    Says,
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PurgeAppConfigDefinitionPayload
type PurgingStep = Scenario[
    TestSeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged
]


@dataclass(frozen=True)
class Purging(When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]):
    """설정 정의 하나를 영구 삭제한다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: ADefinitionAndACaller) -> str:
        if self.other is not None:
            return Says(
                f"{laid.caller.username} 이 존재하지 않는 ID 를 영구 삭제합니다",
                english=f"{laid.caller.username} purges a missing id",
            )
        return Says(
            f"{laid.caller.username} 이 {laid.definition.config_name} 을 영구 삭제합니다",
            english=f"{laid.caller.username} purges {laid.definition.config_name}",
        )

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: ADefinitionAndACaller
    ) -> Purged:
        wanted = self.other if self.other is not None else laid.definition.id
        with ActingAs(laid.caller):
            return await adapter.purge(PurgeAppConfigDefinitionInput(id=wanted))


@dataclass(frozen=True)
class ThePurgedOneIsNamed(Then[ADefinitionAndACaller, Purged]):
    """영구 삭제한 설정 정의의 ID를 응답한다."""

    @override
    def says(self) -> str:
        return Says(
            "영구 삭제한 설정 정의의 ID 를 응답합니다",
            english="it answers with the id of the purged config definition",
        )

    @override
    def look(self, laid: ADefinitionAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held(
                "ID",
                payload.id,
                SameAs[UUID](
                    laid.definition.id,
                    Says(
                        "미리 저장한 설정 정의",
                        english="the config definition made in advance",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class TheSuperadminPurgesIt(
    Scenario[TestSeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-definition"

    @override
    def describe(self) -> str:
        return Says(
            "종속 행이 없는 설정 정의를 superadmin 이 영구 삭제하면, 삭제한 ID 가 반환됩니다",
            english=(
                "when the superadmin purges a config definition with no dependent rows, "
                "the purged id comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ADefinitionAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class EntriesAndFragmentsDoNotBlockIt(
    Scenario[TestSeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-definition-holding-an-entry-and-a-fragment-is-still-purged"

    @override
    def describe(self) -> str:
        return Says(
            "허용 목록 항목과 설정 조각이 딸린 설정 정의를 superadmin 이 영구 삭제하면, "
            "종속 행이 삭제를 막지 않고 정의의 ID 가 반환됩니다",
            english=(
                "when the superadmin purges a config definition holding an allow-list entry "
                "and a config fragment, the dependent rows do not block the purge and the id "
                "of the definition comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone(role=UserRole.SUPERADMIN, with_fragment=True)

    @override
    def when(self) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ADefinitionAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-purge-a-definition"

    @override
    def describe(self) -> str:
        return Says(
            "같은 설정 정의가 있고 권한이 없는 일반 사용자가 영구 삭제하면, "
            "엔티티 영구 삭제 권한이 없어 거부됩니다",
            english=(
                "when a regular user with no permission purges the same config definition, "
                "it is rejected because the user has no entity purge permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADefinitionAndACaller]:
        return ADefinitionAndSomeone()

    @override
    def when(self) -> When[ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ADefinitionAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[TestSeedingSession, ADefinitionAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 ID 를 영구 삭제하면, 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin purges a missing id, it is rejected because no such "
                "target exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADefinitionAndACaller]:
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
