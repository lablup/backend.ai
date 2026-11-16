"""시스템 세션 환경변수 완전히 지우기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    PurgeSystemSessionEnvironPayload,
)
from ai.backend.manager.api.adapters.system_session_environ.adapter import (
    SystemSessionEnvironAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.system_session_environ import (
    AnEnvironAndACaller,
    AnEnvironAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PurgingStep = Scenario[
    TestSeedingSession,
    AnEnvironAndACaller,
    SystemSessionEnvironAdapter,
    PurgeSystemSessionEnvironPayload,
]


@dataclass(frozen=True)
class Purging(
    When[AnEnvironAndACaller, SystemSessionEnvironAdapter, PurgeSystemSessionEnvironPayload]
):
    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AnEnvironAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.environ.key}를 완전히 지웁니다",
            english=f"{laid.caller.username} purges {laid.environ.key}",
        )

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: AnEnvironAndACaller
    ) -> PurgeSystemSessionEnvironPayload:
        with ActingAs(laid.caller):
            return await adapter.purge(SystemSessionEnvironID(laid.environ.id))


@dataclass(frozen=True)
class ThePurgedEnvironId(Then[AnEnvironAndACaller, PurgeSystemSessionEnvironPayload]):
    @override
    def says(self) -> str:
        return Says(
            "완전히 지운 행의 id 가 반환됩니다",
            english="the id of the purged row comes back",
        )

    @override
    def look(
        self, laid: AnEnvironAndACaller, answered: Answered[PurgeSystemSessionEnvironPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held[UUID](
                "entity_id",
                payload.entity_id,
                SameAs[UUID](
                    laid.environ.id,
                    Says("미리 저장한 행", english="the row seeded in advance"),
                ),
            )
        ]


@dataclass(frozen=True)
class AUserGrantedPurgePurges(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        PurgeSystemSessionEnvironPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-purge-purges-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 완전 삭제 권한을 받은 사용자가 시스템 세션 환경변수를 완전히 지우면 지운 행의 "
            "id 가 반환됩니다",
            english=(
                "when a user granted purge permission in public purges a system session environ, "
                "the id of the purged row comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return AnEnvironAndSomeone(granted=(Permission.HARD_DELETE,))

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, PurgeSystemSessionEnvironPayload]:
        return Purging()

    @override
    def then(
        self,
    ) -> Then[AnEnvironAndACaller, PurgeSystemSessionEnvironPayload]:
        return ThePurgedEnvironId()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        PurgeSystemSessionEnvironPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 완전히 지우려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to purge a system session environ, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return AnEnvironAndSomeone()

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, PurgeSystemSessionEnvironPayload]:
        return Purging()

    @override
    def then(
        self,
    ) -> Then[AnEnvironAndACaller, PurgeSystemSessionEnvironPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[PurgingStep] = [
    AUserGrantedPurgePurges(),
    AUserGrantedNothingMayNotPurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep,
    adapter: SystemSessionEnvironAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
