"""유휴 검사기 purge — 한 번에 하나."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker.request import PurgeIdleCheckerInput
from ai.backend.common.dto.manager.v2.idle_checker.response import PurgeIdleCheckerPayload
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
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
from bai_scenario.components.idle_checker import CheckersAndACaller, SomeCheckersAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RetiringStep = Scenario[
    TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, PurgeIdleCheckerPayload
]


@dataclass(frozen=True)
class PurgingTheLaidChecker(When[CheckersAndACaller, IdleCheckerAdapter, PurgeIdleCheckerPayload]):
    """미리 저장한 검사기 하나를 purge 한다."""

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 검사기 {laid.laid[0].name}을 purge 합니다",
            english=f"{laid.caller.username} purges the checker {laid.laid[0].name}",
        )

    @override
    async def call(
        self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller
    ) -> PurgeIdleCheckerPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_purge(PurgeIdleCheckerInput(id=laid.laid[0].id))


@dataclass(frozen=True)
class ThePurgedCheckerAnswers(Then[CheckersAndACaller, PurgeIdleCheckerPayload]):
    """요청에 넣은 검사기의 id 그대로 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "요청에 넣은 검사기의 id 로 반환됩니다",
            english="the purge is answered with the id of the checker put in the request",
        )

    @override
    def look(
        self, laid: CheckersAndACaller, answered: Answered[PurgeIdleCheckerPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[UUID](
                "id",
                payload.id,
                SameAs(
                    laid.laid[0].id,
                    Says("요청에 넣은 검사기", english="the checker put in the request"),
                ),
            ),
            Held[UUID](
                "entity_id",
                payload.entity_id,
                SameAs(
                    laid.laid[0].id,
                    Says("요청에 넣은 검사기", english="the checker put in the request"),
                ),
            ),
        ]


@dataclass(frozen=True)
class TheSuperadminPurgesAChecker(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, PurgeIdleCheckerPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-an-idle-checker"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 검사기 하나를 purge 하면, 요청에 넣은 검사기의 id 로 반환됩니다",
            english=(
                "when the superadmin purges one idle checker, the purge is answered with the id "
                "of the checker put in the request"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, PurgeIdleCheckerPayload]:
        return PurgingTheLaidChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, PurgeIdleCheckerPayload]:
        return ThePurgedCheckerAnswers()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurgeAChecker(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, PurgeIdleCheckerPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-an-idle-checker"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 검사기 하나를 purge 하려 하면 권한이 없다는 이유로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to purge one idle checker, it is rejected for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone()

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, PurgeIdleCheckerPayload]:
        return PurgingTheLaidChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, PurgeIdleCheckerPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RetiringStep] = [
    TheSuperadminPurgesAChecker(),
    AUserGrantedNothingMayNotPurgeAChecker(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: IdleCheckerAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
