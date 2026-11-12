"""프로젝트의 모델 vfolder 를 훑어 모델 카드 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.model_card.response import ScanProjectModelCardsPayload
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.project.types import ProjectData, ProjectType
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.resource import InvalidProjectTypeForModelCard
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
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.vfolder import STORAGE_HOST
from bai_scenario.fakes.storage_proxy import FakeStorageProxyManagerFacingClient, StorageScript
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.vfolder.vfolder import TestSeedProjectVFolder

type Scanned = ScanProjectModelCardsPayload

MODEL_DEFINITION = b"models:\n  - name: llama\n    model_path: /models/llama\n"


@pytest.fixture
def storage() -> FakeStorageProxyManagerFacingClient:
    """모든 vfolder 맨 위에 모델 하나를 적은 모델 정의 파일이 있다."""
    return FakeStorageProxyManagerFacingClient(
        StorageScript(files={"model-definition.yml": MODEL_DEFINITION})
    )


@dataclass(frozen=True)
class AProjectToScan:
    """훑을 프로젝트와 훑으려는 사람."""

    project: ProjectData
    caller: UserData


@dataclass(frozen=True)
class AModelFolderInAProject(Given[Any, AProjectToScan]):
    """모델 vfolder 하나가 놓인 프로젝트와 사용자 한 명. vfolder 에는 모델 정의 파일이 있다."""

    role: UserRole
    project_type: ProjectType = ProjectType.MODEL_STORE

    @override
    def describe(self) -> str:
        return Says(
            f"모델 하나를 적은 모델 정의 파일을 담은 vfolder 하나가 놓인 {self.project_type.value} "
            f"프로젝트와 {self.role.value} 한 명",
            english=(
                f"a {self.project_type.value} project holding one vfolder whose model "
                f"definition file names one model, and one {self.role.value}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AProjectToScan:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(name_hint="model-store", type=self.project_type), domain, policy
        )
        caller = await seeding.within(
            SomeoneOf(domain, role=self.role, vfolder_hosts=[STORAGE_HOST])
        )
        usage_mode = (
            VFolderUsageMode.MODEL
            if self.project_type is ProjectType.MODEL_STORE
            else VFolderUsageMode.GENERAL
        )
        await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST, usage_mode=usage_mode), project, caller
        )
        return AProjectToScan(seeding.made(project), seeding.made(caller))


@dataclass(frozen=True)
class ScanningTheProject(When[AProjectToScan, ModelCardAdapter, Scanned]):
    @override
    def operation(self) -> str:
        return "scan_project"

    @override
    def describe(self, laid: AProjectToScan) -> str:
        return Says(
            f"{laid.caller.username}이 프로젝트 {laid.project.name}의 vfolder 를 훑습니다",
            english=f"{laid.caller.username} scans the vfolders of project {laid.project.name}",
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: AProjectToScan) -> Scanned:
        with ActingAs(laid.caller):
            return await adapter.scan_project(laid.project.id)


@dataclass(frozen=True)
class OneCardIsCreated(Then[AProjectToScan, Scanned]):
    @override
    def says(self) -> str:
        return Says(
            "카드 하나가 새로 만들어지고 고친 카드와 오류는 없습니다",
            english="one card is created, none is updated and nothing went wrong",
        )

    @override
    def look(self, laid: AProjectToScan, answered: Answered[Scanned]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("created_count", payload.created_count, 1),
            Same("updated_count", payload.updated_count, 0),
            Same("errors", payload.errors, []),
        ]


@dataclass(frozen=True)
class TheSuperadminScansAModelStore(
    Scenario[TestSeedingSession, AProjectToScan, ModelCardAdapter, Scanned]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-scans-a-model-store-into-a-card"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 모델 정의 파일을 담은 vfolder 하나가 놓인 model-store 프로젝트를 훑으면 "
            "카드 하나가 새로 만들어집니다. 전역 역할이 이 호출을 막으므로 superadmin 이 부릅니다",
            english=(
                "when the superadmin scans a model-store project holding one vfolder with a "
                "model definition file, one card is created. The global role gates this call, "
                "so the superadmin calls it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectToScan]:
        return AModelFolderInAProject(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AProjectToScan, ModelCardAdapter, Scanned]:
        return ScanningTheProject()

    @override
    def then(self) -> Then[AProjectToScan, Scanned]:
        return OneCardIsCreated()


@dataclass(frozen=True)
class ARegularUserMayNotScan(
    Scenario[TestSeedingSession, AProjectToScan, ModelCardAdapter, Scanned]
):
    @override
    def summary(self) -> str:
        return "a-regular-user-may-not-scan-a-model-store"

    @override
    def describe(self) -> str:
        return Says(
            "일반 사용자가 model-store 프로젝트를 훑으려 하면 전역 역할이 막아 거부됩니다",
            english=(
                "when a regular user tries to scan a model-store project, the global role "
                "rejects the call"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectToScan]:
        return AModelFolderInAProject(role=UserRole.USER)

    @override
    def when(self) -> When[AProjectToScan, ModelCardAdapter, Scanned]:
        return ScanningTheProject()

    @override
    def then(self) -> Then[AProjectToScan, Scanned]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AProjectThatIsNoModelStoreIsRefused(
    Scenario[TestSeedingSession, AProjectToScan, ModelCardAdapter, Scanned]
):
    @override
    def summary(self) -> str:
        return "a-project-that-is-not-a-model-store-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 model-store 가 아닌 프로젝트를 훑으려 하면 프로젝트 유형이 맞지 "
            "않는다는 이유로 거부됩니다",
            english=(
                "when the superadmin tries to scan a project that is not a model-store, the "
                "call is rejected for the wrong project type"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectToScan]:
        return AModelFolderInAProject(role=UserRole.SUPERADMIN, project_type=ProjectType.GENERAL)

    @override
    def when(self) -> When[AProjectToScan, ModelCardAdapter, Scanned]:
        return ScanningTheProject()

    @override
    def then(self) -> Then[AProjectToScan, Scanned]:
        return TheCallIsRefused(InvalidProjectTypeForModelCard)


type ScanStep = Scenario[TestSeedingSession, AProjectToScan, ModelCardAdapter, Scanned]

SCENARIOS: list[ScanStep] = [
    TheSuperadminScansAModelStore(),
    ARegularUserMayNotScan(),
    AProjectThatIsNoModelStoreIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scanning(
    scenario: ScanStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
