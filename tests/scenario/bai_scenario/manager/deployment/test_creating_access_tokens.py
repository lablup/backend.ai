"""배포가 걸린 접근 토큰 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.request import CreateAccessTokenInput
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Says,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.access_token import (
    TokensOfADeployment,
    TokensOfADeploymentAndACaller,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EXPIRES_AT = datetime.now(UTC) + timedelta(days=1)

type Answer = object
type TokenStep = Scenario[
    TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class MakingATokenOfTheDeployment(When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 배포의 id 와 만기 시각만 준다."""

    @override
    def operation(self) -> str:
        return "create_access_token"

    @override
    def describe(self, laid: TokensOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 배포의 접근 토큰 하나를 만듭니다",
            english=f"{laid.caller.username} makes one access token of the deployment",
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: TokensOfADeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.create_access_token(
                CreateAccessTokenInput(
                    model_deployment_id=laid.deployment.id,
                    expires_at=EXPIRES_AT,
                )
            )


@dataclass(frozen=True)
class AUserGrantedDeploymentCreateMakesNoToken(
    Scenario[TestSeedingSession, TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-create-makes-no-token"

    @override
    def describe(self) -> str:
        return Says(
            "배포 생성 권한을 받은 사용자가 심은 배포의 접근 토큰을 만들려 하면, 배포의 스케일링 "
            "그룹에 프록시 대상이 없다는 이유로 거부됩니다. 토큰 문자열을 발행하는 주체가 그룹의 "
            "프록시 대상이므로, 대상이 없으면 만들 수 없습니다",
            english=(
                "when a user granted deployment create tries to make an access token of the "
                "deployment, the create is rejected because the deployment's scaling group has "
                "no proxy target configured"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TokensOfADeploymentAndACaller]:
        return TokensOfADeployment(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[TokensOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return MakingATokenOfTheDeployment()

    @override
    def then(self) -> Then[TokensOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(InvalidAPIParameters)


SCENARIOS: list[TokenStep] = [
    AUserGrantedDeploymentCreateMakesNoToken(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating_access_tokens(
    scenario: TokenStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
