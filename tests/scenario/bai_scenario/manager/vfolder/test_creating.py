"""프로젝트 소유 폴더 만들기 — 누가 만들 수 있고, 만들어진 폴더가 누구의 것인가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.vfolder.request import CreateVFolderInScopeInput
from ai.backend.common.dto.manager.v2.vfolder.response import VFolderNode
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder import (
    STORAGE_HOST,
    AProjectAndMaker,
    AProjectWhereSomeoneMayMakeFolders,
    TheNewFolderNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MADE = "shared"

type CreatingStep = Scenario[TestSeedingSession, AProjectAndMaker, VFolderAdapter, VFolderNode]


@dataclass(frozen=True)
class CreatingInTheProject(When[AProjectAndMaker, VFolderAdapter, VFolderNode]):
    """그 프로젝트 소유로 폴더 하나를 만든다."""

    @override
    def operation(self) -> str:
        return "create_in_project"

    @override
    def describe(self, laid: AProjectAndMaker) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트 소유로 {MADE} vfolder 를 "
            "생성합니다",
            english=(
                f"{laid.caller.username} creates the {MADE} vfolder owned by the "
                f"{laid.project.name} project"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AProjectAndMaker) -> VFolderNode:
        with ActingAs(laid.caller):
            payload = await adapter.create_in_project(
                laid.project.id, CreateVFolderInScopeInput(name=MADE, host=STORAGE_HOST)
            )
        return payload.vfolder


@dataclass(frozen=True)
class AProjectMemberMakesAProjectFolder(
    Scenario[TestSeedingSession, AProjectAndMaker, VFolderAdapter, VFolderNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-create-in-a-project-makes-a-project-folder"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 vfolder 생성 권한을 받은 사용자가 그 프로젝트 소유로 vfolder 를 "
            "생성하면, 그 폴더는 그 프로젝트에 속합니다",
            english=(
                "when a user granted vfolder create in a project creates a folder owned by "
                "that project, the folder belongs to the project"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAndMaker]:
        return AProjectWhereSomeoneMayMakeFolders(granted=True)

    @override
    def when(self) -> When[AProjectAndMaker, VFolderAdapter, VFolderNode]:
        return CreatingInTheProject()

    @override
    def then(self) -> Then[AProjectAndMaker, VFolderNode]:
        return TheNewFolderNode(started=self.started, named=MADE, ownership_type="group")


@dataclass(frozen=True)
class AUserGrantedNothingMayNotMakeAProjectFolder(
    Scenario[TestSeedingSession, AProjectAndMaker, VFolderAdapter, VFolderNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-make-a-project-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프로젝트 소유 vfolder 를 생성하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to create a project-owned vfolder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAndMaker]:
        return AProjectWhereSomeoneMayMakeFolders(granted=False)

    @override
    def when(self) -> When[AProjectAndMaker, VFolderAdapter, VFolderNode]:
        return CreatingInTheProject()

    @override
    def then(self) -> Then[AProjectAndMaker, VFolderNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CreatingStep] = [
    AProjectMemberMakesAProjectFolder(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotMakeAProjectFolder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
