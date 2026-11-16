"""배포가 걸린 접근 토큰 id 로 한꺼번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.common.dto.manager.v2.deployment.response import AccessTokenNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
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
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[AccessTokenNode | Exception | None]
type TokenStep = Scenario[
    TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class LoadingTheSeededTokens(When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 토큰들의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_access_tokens_by_ids"

    @override
    def describe(self, laid: TokensOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 토큰 {len(laid.tokens)}개를 id 로 한꺼번에 읽습니다",
            english=f"{laid.caller.username} batch loads {len(laid.tokens)} tokens by id",
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: TokensOfADeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_access_tokens_by_ids([
                DeploymentTokenID(token.id) for token in laid.tokens
            ])


@dataclass(frozen=True)
class TheTokensComeBackInOrder(Then[TokensOfADeploymentAndACaller, Answer]):
    """토큰이 요청에 넣은 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "토큰이 요청에 넣은 순서대로 옵니다",
            english="the tokens come back in the order they were put in the request",
        )

    @override
    def look(
        self, laid: TokensOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        tokens = answered.response
        if tokens is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("loaded count", len(tokens), len(laid.tokens))]
        for i, (node, token) in enumerate(zip(tokens, laid.tokens, strict=False)):
            if isinstance(node, AccessTokenNode):
                verdicts += TheTokenNode(self.started).verdicts(node, token, f"[{i}].")
            else:
                verdicts.append(Same(f"[{i}]", type(node).__name__, "AccessTokenNode"))
        return verdicts


@dataclass(frozen=True)
class EveryEntryIsRefused(Then[TokensOfADeploymentAndACaller, Answer]):
    """토큰 없이, 모든 항목이 같은 이유로 거부된 예외로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "토큰 없이 모든 항목이 거부된 예외로 옵니다",
            english="no token comes back and every entry is the exception the check raised",
        )

    @override
    def look(
        self, laid: TokensOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        tokens = answered.response
        if tokens is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("loaded count", len(tokens), len(laid.tokens))]
        for i, entry in enumerate(tokens):
            verdicts.append(
                Refused(NotEnoughPermission, entry if isinstance(entry, Exception) else None)
                if entry is not None
                else Same(f"[{i}]", type(entry).__name__, "exception")
            )
        return verdicts


@dataclass(frozen=True)
class AUserGrantedDeploymentReadLoadsTheTokensById(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-loads-the-tokens-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포가 걸린 접근 토큰을 id 로 한꺼번에 읽으면, "
            "그 토큰들이 옵니다",
            english=(
                "when a user granted deployment read batch loads the access tokens the "
                "deployment holds by id, those tokens come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment(granted=(Permission.READ,))

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return LoadingTheSeededTokens()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return TheTokensComeBackInOrder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForEachToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-for-each-token"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 접근 토큰을 id 로 한꺼번에 읽으려 하면, "
            "모든 항목이 권한이 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to batch load the access tokens the "
                "deployment holds by id, every entry is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment()

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return LoadingTheSeededTokens()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return EveryEntryIsRefused()


STARTED = datetime.now(UTC)

SCENARIOS: list[TokenStep] = [
    AUserGrantedDeploymentReadLoadsTheTokensById(started=STARTED),
    AUserGrantedNothingGetsARefusalForEachToken(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading_access_tokens(
    scenario: TokenStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
