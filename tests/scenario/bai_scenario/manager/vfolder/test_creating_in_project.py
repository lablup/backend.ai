"""프로젝트 아래 폴더 만들기 — 프로젝트를 경로로 받는 자리."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder.answers import (
    TheFolderBelongsToTheProject,
)
from bai_scenario.components.vfolder.callers import (
    SomeoneGrantedNothingOnAProject,
    SomeoneGrantedOnAProject,
)
from bai_scenario.components.vfolder.stage import (
    STORAGE_HOST,
    AProjectAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInScopeInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import VFolderNode
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Scenario,
    Then,
    When,
)

ENFORCEMENT = "manager.rbac.enforcement_enabled"

type CreatingStep = Scenario[SeedingSession, Any, VFolderAdapter, VFolderNode]


@dataclass(frozen=True)
class MakingAFolderUnderTheProject(When[AProjectAndACaller, VFolderAdapter, VFolderNode]):
    """프로젝트를 경로로 받는 자리에서 만든다."""

    named: str

    @override
    def operation(self) -> str:
        return "create_in_project"

    @override
    def describe(self, laid: AProjectAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.project.name} 아래 {self.named}이라는 폴더를 만듦"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AProjectAndACaller) -> VFolderNode:
        with ActingAs(laid.caller):
            payload = await adapter.create_in_project(
                laid.project.id, CreateVFolderInScopeInput(name=self.named, host=STORAGE_HOST)
            )
        return payload.vfolder


@dataclass(frozen=True)
class AProjectGrantMakesAProjectFolder(
    Scenario[SeedingSession, AProjectAndACaller, VFolderAdapter, VFolderNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-project-makes-a-folder-the-project-owns"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에 권한을 받은 사용자가 프로젝트 아래 폴더를 만들면, "
            "그 프로젝트가 주인인 폴더 전체가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return SomeoneGrantedOnAProject()

    @override
    def when(self) -> When[AProjectAndACaller, VFolderAdapter, VFolderNode]:
        return MakingAFolderUnderTheProject(named="team")

    @override
    def then(self) -> Then[AProjectAndACaller, VFolderNode]:
        return TheFolderBelongsToTheProject(started=self.started, named="team")


@dataclass(frozen=True)
class NoProjectGrantMakesNoProjectFolder(
    Scenario[SeedingSession, AProjectAndACaller, VFolderAdapter, VFolderNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-on-the-project-may-not-make-a-folder-there"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에 아무 권한도 받지 않은 사용자가 프로젝트 아래 폴더를 만들려 하면, "
            "그 프로젝트에 걸린 권한이 막아 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return SomeoneGrantedNothingOnAProject()

    @override
    def when(self) -> When[AProjectAndACaller, VFolderAdapter, VFolderNode]:
        return MakingAFolderUnderTheProject(named="denied")

    @override
    def then(self) -> Then[AProjectAndACaller, VFolderNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CreatingStep] = [
    AProjectGrantMakesAProjectFolder(started=datetime.now(UTC)),
    NoProjectGrantMakesNoProjectFolder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating_in_project(
    scenario: CreatingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
