"""모델 폴더로 배포 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.vfolder.request import DeployVFolderInput
from ai.backend.common.dto.manager.v2.vfolder.response import DeployVFolderPayload
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import NotAModelVFolder
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder import AModelFolderForDeployment, AModelFolderPlace
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type DeployingStep = Scenario[
    TestSeedingSession, AModelFolderPlace, VFolderAdapter, DeployVFolderPayload
]


@dataclass(frozen=True)
class NamedAfterTheFolder(Condition[str]):
    """폴더 이름으로 시작하는 이름. 뒤에는 실행마다 다른 조각이 붙는다."""

    prefix: str

    @override
    def says(self) -> Says:
        return Says(
            f"'{self.prefix}'로 시작하는 이름",
            english=f"a name starting with '{self.prefix}'",
        )

    @override
    def holds(self, got: str) -> bool:
        return got.startswith(f"{self.prefix}-")


@dataclass(frozen=True)
class DeployingTheFolder(When[AModelFolderPlace, VFolderAdapter, DeployVFolderPayload]):
    """모델 폴더로 배포 하나를 만든다."""

    @override
    def operation(self) -> str:
        return "deploy"

    @override
    def describe(self, laid: AModelFolderPlace) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 로 {laid.project.name} 에 "
            "배포를 만듭니다",
            english=(
                f"{laid.caller.username} creates a deployment in the {laid.project.name} from "
                f"the {laid.folder.name} vfolder"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AModelFolderPlace) -> DeployVFolderPayload:
        with ActingAs(laid.caller):
            return await adapter.deploy(
                laid.folder.id,
                DeployVFolderInput(
                    project_id=laid.project.id,
                    revision_preset_id=laid.preset.id,
                    resource_group=laid.resource_group.name,
                ),
            )


@dataclass(frozen=True)
class TheDeploymentMade(Then[AModelFolderPlace, DeployVFolderPayload]):
    """만들어진 배포의 id 와, 폴더 이름에서 온 이름이 온다."""

    @override
    def says(self) -> str:
        return Says(
            "만들어진 배포의 id 와 폴더 이름에서 온 배포 이름이 응답으로 옵니다",
            english="the id of the deployment made and its name derived from the folder come back",
        )

    @override
    def look(
        self, laid: AModelFolderPlace, answered: Answered[DeployVFolderPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Skipped(
                "deployment_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Held(
                "deployment_name",
                payload.deployment_name,
                NamedAfterTheFolder(laid.folder.name),
            ),
        ]


@dataclass(frozen=True)
class AGrantedUserDeploysTheModelFolder(
    Scenario[TestSeedingSession, AModelFolderPlace, VFolderAdapter, DeployVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-create-deploys-a-model-folder"

    @override
    def describe(self) -> str:
        return Says(
            "그 프로젝트에서 배포 생성 권한을 받은 사용자가 읽을 수 있는 모델 vfolder 로 배포를 "
            "만들면, 만들어진 배포의 id 와 이름이 응답으로 옵니다",
            english=(
                "when a user granted deployment create in a project deploys a model vfolder "
                "they can read, the id and name of the deployment made come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AModelFolderPlace]:
        return AModelFolderForDeployment()

    @override
    def when(self) -> When[AModelFolderPlace, VFolderAdapter, DeployVFolderPayload]:
        return DeployingTheFolder()

    @override
    def then(self) -> Then[AModelFolderPlace, DeployVFolderPayload]:
        return TheDeploymentMade()


@dataclass(frozen=True)
class AFolderNotForModelsMayNotBeDeployed(
    Scenario[TestSeedingSession, AModelFolderPlace, VFolderAdapter, DeployVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "deploying-a-folder-not-used-as-a-model-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "모델 용도가 아닌 vfolder 로 배포를 만들려 하면 모델 폴더가 아니라는 이유로 거부됩니다",
            english=(
                "when a user tries to deploy a vfolder not used as a model, it is rejected as "
                "not a model folder"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AModelFolderPlace]:
        return AModelFolderForDeployment(usage_mode=VFolderUsageMode.GENERAL)

    @override
    def when(self) -> When[AModelFolderPlace, VFolderAdapter, DeployVFolderPayload]:
        return DeployingTheFolder()

    @override
    def then(self) -> Then[AModelFolderPlace, DeployVFolderPayload]:
        return TheCallIsRefused(NotAModelVFolder)


@dataclass(frozen=True)
class AUserWithoutDeploymentCreateMayNotDeploy(
    Scenario[TestSeedingSession, AModelFolderPlace, VFolderAdapter, DeployVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-without-deployment-create-may-not-deploy-a-model-folder"

    @override
    def describe(self) -> str:
        return Says(
            "폴더 읽기만 받고 배포 생성은 받지 않은 사용자가 모델 vfolder 로 배포를 만들려 하면 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted folder read but not deployment create tries to deploy a model "
                "vfolder, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AModelFolderPlace]:
        return AModelFolderForDeployment(granted=False)

    @override
    def when(self) -> When[AModelFolderPlace, VFolderAdapter, DeployVFolderPayload]:
        return DeployingTheFolder()

    @override
    def then(self) -> Then[AModelFolderPlace, DeployVFolderPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[DeployingStep] = [
    AGrantedUserDeploysTheModelFolder(),
    AFolderNotForModelsMayNotBeDeployed(),
    AUserWithoutDeploymentCreateMayNotDeploy(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deploying(
    scenario: DeployingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
