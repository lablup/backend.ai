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
    AProjectThatClosesTheHost,
    SomeoneGrantedNothingOnAProject,
    SomeoneGrantedOnAProject,
    SomeoneNamingTheirPersonalProject,
)
from bai_scenario.components.vfolder.stage import (
    STORAGE_HOST,
    APersonalProjectAndItsOwner,
    AProjectAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInScopeInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    VFolderNode,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import InsufficientStoragePermission
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
class MakingAFolderUnderTheirPersonalProject(
    When[APersonalProjectAndItsOwner, VFolderAdapter, VFolderNode]
):
    """자기 개인 프로젝트를 대상으로 지목해 만든다."""

    named: str

    @override
    def operation(self) -> str:
        return "create_in_project"

    @override
    def describe(self, laid: APersonalProjectAndItsOwner) -> str:
        return f"{laid.caller.username}이 자기 개인 프로젝트 아래 {self.named}이라는 폴더를 만듦"

    @override
    async def call(self, adapter: VFolderAdapter, laid: APersonalProjectAndItsOwner) -> VFolderNode:
        with ActingAs(laid.caller):
            payload = await adapter.create_in_project(
                laid.project_id, CreateVFolderInScopeInput(name=self.named, host=STORAGE_HOST)
            )
        return payload.vfolder


@dataclass(frozen=True)
class APersonalProjectMayNotBeNamed(
    Scenario[SeedingSession, APersonalProjectAndItsOwner, VFolderAdapter, VFolderNode]
):
    @override
    def summary(self) -> str:
        return "naming-a-personal-project-is-stopped-by-the-storage-host-first"

    @override
    def describe(self) -> str:
        return (
            "사용자를 만들 때 딸려 만들어진 개인 프로젝트를 대상으로 지목해 폴더를 만들려 하면, "
            "그 프로젝트가 어떤 스토리지 호스트도 허용하지 않으므로 저장소 쪽이 먼저 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, APersonalProjectAndItsOwner]:
        return SomeoneNamingTheirPersonalProject()

    @override
    def when(self) -> When[APersonalProjectAndItsOwner, VFolderAdapter, VFolderNode]:
        return MakingAFolderUnderTheirPersonalProject(named="mine")

    @override
    def then(self) -> Then[APersonalProjectAndItsOwner, VFolderNode]:
        return TheCallIsRefused(InsufficientStoragePermission)


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
class TheProjectClosesTheHost(
    Scenario[SeedingSession, AProjectAndACaller, VFolderAdapter, VFolderNode]
):
    @override
    def summary(self) -> str:
        return "a-project-that-closes-the-host-stops-the-create"

    @override
    def describe(self) -> str:
        return (
            "프로젝트가 그 호스트에서 만들기를 막아두면, 부르는 사람의 키페어 정책이 그 "
            "호스트를 모두 허락하더라도 프로젝트 폴더를 만들 수 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return AProjectThatClosesTheHost()

    @override
    def when(self) -> When[AProjectAndACaller, VFolderAdapter, VFolderNode]:
        return MakingAFolderUnderTheProject(named="denied-by-host")

    @override
    def then(self) -> Then[AProjectAndACaller, VFolderNode]:
        return TheCallIsRefused(InsufficientStoragePermission)


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
    TheProjectClosesTheHost(),
    APersonalProjectMayNotBeNamed(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating_in_project(
    scenario: CreatingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
