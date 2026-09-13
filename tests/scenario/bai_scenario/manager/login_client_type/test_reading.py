"""로그인 클라이언트 종류 조회 — id로 조회한다. 인증만 확인한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_client_type import (
    ATypeAndACaller,
    ATypeAndSomeone,
    TheTypeNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.login_client_type.response import LoginClientTypeNode
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode
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
        target = "존재하지 않는 id" if self.unknown else laid.client_type.name
        return f"{laid.caller.username}이 {target}(으)로 조회"

    @override
    async def call(
        self, adapter: LoginClientTypeAdapter, laid: ATypeAndACaller
    ) -> LoginClientTypeNode:
        with ActingAs(laid.caller):
            return await adapter.get(uuid4() if self.unknown else laid.client_type.id)


@dataclass(frozen=True)
class AUserGrantedNothingReadsById(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-login-client-type-by-id"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 id로 조회하면 그 종류 전체가 반환된다. 이 조회는 인증만 확인한다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheTypeNode(started=self.started)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[SeedingSession, ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-login-client-type-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ATypeAndACaller]:
        return ATypeAndSomeone()

    @override
    def when(self) -> When[ATypeAndACaller, LoginClientTypeAdapter, LoginClientTypeNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[ATypeAndACaller, LoginClientTypeNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[ReadingStep] = [
    AUserGrantedNothingReadsById(started=datetime.now(UTC)),
    AnIdNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
