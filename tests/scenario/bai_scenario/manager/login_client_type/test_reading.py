"""로그인 클라이언트 종류 조회 — id로 조회한다. 인증만 확인한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.dto.manager.v2.login_client_type.response import LoginClientTypeNode
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_client_type import (
    ATypeAndACaller,
    ATypeAndSomeone,
    TheTypeNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[
    TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode
]


@dataclass(frozen=True)
class ReadingById(When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]):
    """id로 조회한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ATypeAndACaller) -> str:
        if self.unknown:
            target_ko = "존재하지 않는 id"
            target_en = "an id nothing answers to"
        else:
            target_ko = laid.client_type.name
            target_en = laid.client_type.name
        return Says(
            f"{laid.caller.username} 이 {target_ko} (으)로 조회합니다",
            english=f"{laid.caller.username} reads a login client type by {target_en}",
        )

    @override
    async def call(
        self, adapter: LoginClientTypeAdapter, laid: ATypeAndACaller
    ) -> LoginClientTypeNode:
        with ActingAs(laid.caller):
            return await adapter.get(uuid4() if self.unknown else laid.client_type.id)


@dataclass(frozen=True)
class AUserGrantedNothingReadsById(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-login-client-type-by-id"

    @override
    def describe(self) -> str:
        return Says(
            (
                "아무 권한도 없는 사용자가 id 로 조회하면 그 로그인 클라이언트 유형 전체가 "
                "반환됩니다. 이 조회는 인증만 확인합니다"
            ),
            english=(
                "when a user granted nothing reads a login client type by id, the whole login "
                "client type comes back. This read checks authentication alone"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheTypeNode(started=self.started)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsRefused(
    Scenario[TestSeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-login-client-type-id-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 id 로 조회하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when it is read by an id nothing answers to, it is rejected because the target "
                "cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[ReadingStep] = [
    AUserGrantedNothingReadsById(started=datetime.now(UTC)),
    AnIdNothingAnswersToIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
