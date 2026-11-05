"""시스템 세션 환경변수 완전히 지우기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    PurgeSystemSessionEnvironPayload,
)
from ai.backend.manager.api.adapters.system_session_environ.adapter import (
    SystemSessionEnvironAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
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
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AnEnvironAndACaller) -> str:
        target_ko = "존재하지 않는 id" if self.unknown else laid.environ.key
        target_en = "an id nothing answers to" if self.unknown else laid.environ.key
        return Says(
            f"{laid.caller.username}이 {target_ko}를 완전히 지웁니다",
            english=f"{laid.caller.username} purges {target_en}",
        )

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: AnEnvironAndACaller
    ) -> PurgeSystemSessionEnvironPayload:
        environ_id = (
            SystemSessionEnvironID(uuid4())
            if self.unknown
            else SystemSessionEnvironID(laid.environ.id)
        )
        with ActingAs(laid.caller):
            return await adapter.purge(environ_id)


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
class TheSuperadminPurges(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        PurgeSystemSessionEnvironPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 시스템 세션 환경변수를 완전히 지우면 지운 행의 id 가 반환됩니다",
            english=(
                "when the superadmin purges a system session environ, the id of the purged row "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return AnEnvironAndSomeone(role=UserRole.SUPERADMIN)

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


@dataclass(frozen=True)
class PurgingAnUnknownIdIsNotFound(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        PurgeSystemSessionEnvironPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "purging-an-environ-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 를 완전히 지우려 하면 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when the superadmin purges an id nothing answers to, it is rejected because the "
                "target cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return AnEnvironAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, PurgeSystemSessionEnvironPayload]:
        return Purging(unknown=True)

    @override
    def then(
        self,
    ) -> Then[AnEnvironAndACaller, PurgeSystemSessionEnvironPayload]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurges(),
    AUserGrantedNothingMayNotPurge(),
    PurgingAnUnknownIdIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep,
    adapter: SystemSessionEnvironAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
