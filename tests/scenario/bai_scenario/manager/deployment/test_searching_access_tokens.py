"""배포가 걸린 접근 토큰 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.request import SearchAccessTokensInput
from ai.backend.common.dto.manager.v2.deployment.response import SearchAccessTokensPayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.deployment.types import AccessTokenOperationScope
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
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

type Answer = SearchAccessTokensPayload
type TokenStep = Scenario[
    TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class SearchingTheTokensOfTheDeployment(
    When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    """심은 배포 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "search_access_tokens"

    @override
    def describe(self, laid: TokensOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 배포가 걸린 접근 토큰을 훑습니다",
            english=f"{laid.caller.username} searches the access tokens the deployment holds",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: TokensOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search_access_tokens(
                AccessTokenOperationScope(deployment_id=laid.deployment.id),
                SearchAccessTokensInput(),
            )


@dataclass(frozen=True)
class TheTokenPageComesBack(Then[TokensOfADeploymentAndACaller, Answer]):
    """배포가 걸린 토큰이 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "배포가 걸린 토큰이 양과 함께 옵니다",
            english="the tokens the deployment holds come back with their count",
        )

    @override
    def look(
        self, laid: TokensOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, len(laid.tokens)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        for i, (node, token) in enumerate(zip(page.items, laid.tokens, strict=False)):
            verdicts += TheTokenNode(self.started).verdicts(node, token, f"items[{i}].")
        return verdicts


@dataclass(frozen=True)
class AUserGrantedDeploymentReadSearchesTheTokens(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-searches-the-tokens"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포가 걸린 접근 토큰을 훑으면, 그 토큰들이 옵니다",
            english=(
                "when a user granted deployment read searches the access tokens the "
                "deployment holds, those tokens come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment(granted=(Permission.READ,))

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheTokensOfTheDeployment()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return TheTokenPageComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingSearchesNoToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-searches-no-token"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 접근 토큰을 훑으려 하면, 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to search the access tokens the "
                "deployment holds, the search is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment()

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheTokensOfTheDeployment()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[TokenStep] = [
    AUserGrantedDeploymentReadSearchesTheTokens(started=STARTED),
    AUserGrantedNothingSearchesNoToken(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_access_tokens(
    scenario: TokenStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
