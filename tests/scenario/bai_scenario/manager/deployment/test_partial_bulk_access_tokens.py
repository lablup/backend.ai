"""접근 토큰 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.deployment.request import PartialBulkPurgeAccessTokensInput
from ai.backend.common.dto.manager.v2.deployment.response import AccessTokenNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.access_token import (
    EveryTokenComesBack,
    NoTokenIsProcessed,
    TokensOfADeployment,
    TokensOfADeploymentAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = PartialBulkPayload[AccessTokenNode]
type TokenStep = Scenario[
    TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class PurgingEveryToken(When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """토큰들을 한 번에 purge 한다. ``missing``이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge_access_tokens"

    @override
    def describe(self, laid: TokensOfADeploymentAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 토큰 {len(laid.tokens)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: TokensOfADeploymentAndACaller) -> Answer:
        ids: list[UUID] = [token.id for token in laid.tokens]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge_access_tokens(
                PartialBulkPurgeAccessTokensInput(ids=ids)
            )


@dataclass(frozen=True)
class PurgingAnswersForTheMissingToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-tokens-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "배포 영구 삭제 권한을 받은 사용자가 토큰 둘과 없는 id 하나를 한 번에 purge 하면, "
            "둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return PurgingEveryToken(missing=self.missing)

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return EveryTokenComesBack(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNoToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-tokens"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 토큰 여럿을 한 번에 purge 하려 하면, purge 된 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment()

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return PurgingEveryToken()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return NoTokenIsProcessed(reason="Insufficient permission")


SCENARIOS: list[TokenStep] = [
    PurgingAnswersForTheMissingToken(),
    AUserGrantedNothingPurgesNoToken(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_access_tokens(
    scenario: TokenStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
