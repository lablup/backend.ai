"""모델 카드를 프리셋으로 배포."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.model_card.request import DeployModelCardInput
from ai.backend.common.dto.manager.v2.model_card.response import DeployModelCardPayload
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.model_card_deploy import (
    ACardToDeploy,
    ACardToDeployAndSomeone,
    TheCardIsDeployed,
    TheDeployIsRefused,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type DeployStep = Scenario[
    TestSeedingSession, ACardToDeploy, ModelCardAdapter, DeployModelCardPayload
]


@dataclass(frozen=True)
class DeployingTheCard(When[ACardToDeploy, ModelCardAdapter, DeployModelCardPayload]):
    """미리 만든 카드를 그 프로젝트와 자원 그룹에, 미리 만든 프리셋으로 배포한다."""

    @override
    def operation(self) -> str:
        return "deploy"

    @override
    def describe(self, laid: ACardToDeploy) -> str:
        return Says(
            f"{laid.caller.username}이 카드 {laid.card.name}을 프리셋 {laid.preset.name}으로 "
            f"자원 그룹 {laid.resource_group.name}에 배포합니다",
            english=(
                f"{laid.caller.username} deploys card {laid.card.name} with preset "
                f"{laid.preset.name} in resource group {laid.resource_group.name}"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ACardToDeploy) -> DeployModelCardPayload:
        with ActingAs(laid.caller):
            return await adapter.deploy(
                laid.card.id,
                DeployModelCardInput(
                    project_id=laid.project.id,
                    revision_preset_id=laid.preset.id,
                    resource_group=laid.resource_group.name,
                ),
            )


@dataclass(frozen=True)
class AUserGrantedCreateDeploysACard(
    Scenario[TestSeedingSession, ACardToDeploy, ModelCardAdapter, DeployModelCardPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-create-deploys-a-model-card"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 카드와 그 vfolder 를 읽을 수 있고 배포 생성 권한을 받은 사용자가 카드를 "
            "프리셋으로 배포하면 카드 이름을 딴 배포가 만들어집니다",
            english=(
                "when a user who can read the card and its vfolder and is granted deployment "
                "create in the project deploys the card with a preset, a deployment named "
                "after the card is created"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACardToDeploy]:
        return ACardToDeployAndSomeone(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[ACardToDeploy, ModelCardAdapter, DeployModelCardPayload]:
        return DeployingTheCard()

    @override
    def then(self) -> Then[ACardToDeploy, DeployModelCardPayload]:
        return TheCardIsDeployed()


@dataclass(frozen=True)
class AUserWithoutDeploymentCreateMayNotDeploy(
    Scenario[TestSeedingSession, ACardToDeploy, ModelCardAdapter, DeployModelCardPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-without-deployment-create-may-not-deploy-a-model-card"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 카드와 그 vfolder 는 읽을 수 있지만 배포 생성 권한은 받지 않은 사용자가 "
            "카드를 배포하려 하면 권한이 없다는 이유로 거부됩니다",
            english=(
                "when a user who can read the card and its vfolder in the project but is not "
                "granted deployment create tries to deploy the card, the call is rejected for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACardToDeploy]:
        return ACardToDeployAndSomeone()

    @override
    def when(self) -> When[ACardToDeploy, ModelCardAdapter, DeployModelCardPayload]:
        return DeployingTheCard()

    @override
    def then(self) -> Then[ACardToDeploy, DeployModelCardPayload]:
        return TheDeployIsRefused()


SCENARIOS: list[DeployStep] = [
    AUserGrantedCreateDeploysACard(started=datetime.now(UTC)),
    AUserWithoutDeploymentCreateMayNotDeploy(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deploying(
    scenario: DeployStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
