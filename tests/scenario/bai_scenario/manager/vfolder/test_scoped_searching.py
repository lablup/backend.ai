"""프로젝트 폴더 검색 — 그 프로젝트 것만 오는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder.answers import (
    OnlyTheirsIsFound,
)
from bai_scenario.components.vfolder.callers import (
    AProjectFolderAndANeighboursOwn,
    SomeoneGrantedNothingOnAProject,
)
from bai_scenario.components.vfolder.stage import (
    AProjectAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SearchVFoldersPayload,
)
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

type SearchingStep = Scenario[SeedingSession, Any, VFolderAdapter, SearchVFoldersPayload]


@dataclass(frozen=True)
class SearchingTheProject(When[AProjectAndACaller, VFolderAdapter, SearchVFoldersPayload]):
    """한 프로젝트의 폴더를 훑는다."""

    @override
    def operation(self) -> str:
        return "project_search"

    @override
    def describe(self, laid: AProjectAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.project.name}의 폴더를 조회"

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AProjectAndACaller
    ) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.project_search(laid.project.id, SearchVFoldersInput())


@dataclass(frozen=True)
class TheProjectFoldersComeBack(
    Scenario[SeedingSession, AProjectAndACaller, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "searching-a-project-answers-only-what-that-project-owns"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에 읽기 권한을 받은 사용자가 프로젝트 폴더를 조회하면, "
            "같은 도메인에 있는 남의 개인 폴더는 빼고 그 프로젝트 것만 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return AProjectFolderAndANeighboursOwn()

    @override
    def when(self) -> When[AProjectAndACaller, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[AProjectAndACaller, SearchVFoldersPayload]:
        return OnlyTheirsIsFound(counted=1)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheProject(
    Scenario[SeedingSession, AProjectAndACaller, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-on-the-project-may-not-search-it"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에 아무 권한도 받지 않은 사용자가 프로젝트 폴더를 조회하려 하면, "
            "그 프로젝트에 걸린 권한이 막아 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAndACaller]:
        return SomeoneGrantedNothingOnAProject()

    @override
    def when(self) -> When[AProjectAndACaller, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[AProjectAndACaller, SearchVFoldersPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    TheProjectFoldersComeBack(),
    AUserGrantedNothingMayNotSearchTheProject(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: SearchingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
