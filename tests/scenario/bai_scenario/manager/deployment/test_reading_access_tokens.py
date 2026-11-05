"""배포가 걸린 접근 토큰 하나 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.response import GetAccessTokenPayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.access_token import (
    TheTokenNode,
    TokensOfADeployment,
    TokensOfADeploymentAndACaller,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = GetAccessTokenPayload
type TokenStep = Scenario[
    TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class ReadingTheFirstToken(When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 토큰 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "get_access_token"

    @override
    def describe(self, laid: TokensOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 토큰 하나를 읽습니다",
            english=f"{laid.caller.username} reads one of the tokens seeded in advance",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: TokensOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.get_access_token(laid.tokens[0].id)


@dataclass(frozen=True)
class TheTokenReadComesBack(Then[TokensOfADeploymentAndACaller, Answer]):
    """읽은 토큰이 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "읽은 토큰이 옵니다", english="the token read comes back"
        )

    @override
    def look(
        self, laid: TokensOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return TheTokenNode(self.started).verdicts(payload.access_token, laid.tokens[0])


@dataclass(frozen=True)
class AUserGrantedDeploymentReadReadsAToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-reads-a-token"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포가 걸린 접근 토큰 하나를 읽으면, 그 토큰이 옵니다",
            english=(
                "when a user granted deployment read reads one of the access tokens the "
                "deployment holds, that token comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment(granted=(Permission.READ,))

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return ReadingTheFirstToken()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return TheTokenReadComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingReadsNoToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-no-token"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 접근 토큰 하나를 읽으려 하면, 권한이 "
            "없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to read one of the access tokens the "
                "deployment holds, the read is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment()

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return ReadingTheFirstToken()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now()

SCENARIOS: list[TokenStep] = [
    AUserGrantedDeploymentReadReadsAToken(started=STARTED),
    AUserGrantedNothingReadsNoToken(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_access_tokens(
    scenario: TokenStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
