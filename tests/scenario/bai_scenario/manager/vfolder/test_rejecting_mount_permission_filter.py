"""마운트 정책 필터 거부 — 사용자 한 명을 지정하지 않는 검색."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.vfolder.request import (
    ScopedSearchVFoldersInput,
    SearchVFoldersInput,
    VFolderFilter,
)
from ai.backend.common.dto.manager.v2.vfolder.response import SearchVFoldersPayload
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderMountPermissionFilter,
    VFolderPermissionField,
    VFolderScope,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder import (
    AFolderAndItsReader,
    AProjectFolderAndSomeone,
    SomeonesFolderAndTheSuperadmin,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RejectionStep = Scenario[
    TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload
]

_MOUNTED_READ_WRITE = VFolderFilter(
    mount_permission=VFolderMountPermissionFilter(equals=VFolderPermissionField.READ_WRITE)
)


@dataclass(frozen=True)
class SearchingEveryFolderMountedReadWrite(
    When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    """전체에서 rw로 마운트하는 것을 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 모든 vfolder 중 rw로 마운트하는 것을 조회합니다",
            english=f"{laid.caller.username} searches every vfolder for those mounted as rw",
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndItsReader
    ) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchVFoldersInput(filter=_MOUNTED_READ_WRITE))


@dataclass(frozen=True)
class ListingTheProjectFoldersMountedReadWrite(
    When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    """폴더가 놓인 프로젝트에서 rw로 마운트하는 것을 훑는다."""

    @override
    def operation(self) -> str:
        return "project_search"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 가 놓인 프로젝트의 vfolder 중 "
            "rw로 마운트하는 것을 조회합니다",
            english=(
                f"{laid.caller.username} lists the vfolders mounted as rw of the project the "
                f"{laid.folder.name} vfolder is placed in"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndItsReader
    ) -> SearchVFoldersPayload:
        project_id = laid.folder.group
        if project_id is None:
            raise LookupError("the folder was laid in no project")
        with ActingAs(laid.caller):
            return await adapter.project_search(
                project_id, SearchVFoldersInput(filter=_MOUNTED_READ_WRITE)
            )


@dataclass(frozen=True)
class SearchingTheProjectScopeMountedReadWrite(
    When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    """사용자 없이 프로젝트만 지정한 스코프에서 rw로 마운트하는 것을 훑는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 가 놓인 프로젝트만 스코프로 "
            "지정해 rw로 마운트하는 vfolder 를 조회합니다",
            english=(
                f"{laid.caller.username} searches the vfolders mounted as rw with only the project "
                f"the {laid.folder.name} vfolder is placed in as the scope"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndItsReader
    ) -> SearchVFoldersPayload:
        project_id = laid.folder.group
        if project_id is None:
            raise LookupError("the folder was laid in no project")
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchVFoldersInput(
                    scope=VFolderScope(project=[UUIDScope(value=project_id)]),
                    filter=_MOUNTED_READ_WRITE,
                )
            )


@dataclass(frozen=True)
class ASearchOfEveryFolderRejectsTheMountPermissionFilter(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-search-of-every-folder-rejects-the-mount-permission-filter"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 모든 vfolder 중 rw로 마운트하는 것을 조회하려 하면, 기준이 될 사용자가 "
            "없어 거부됩니다",
            english=(
                "when a superadmin tries to search every vfolder for those mounted as rw, it is "
                "rejected because no user is named"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeonesFolderAndTheSuperadmin()

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingEveryFolderMountedReadWrite()

    @override
    def then(self) -> Then[AFolderAndItsReader, SearchVFoldersPayload]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class AProjectSearchRejectsTheMountPermissionFilter(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-project-search-rejects-the-mount-permission-filter"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 vfolder 읽기 권한을 받은 사용자가 그 프로젝트의 vfolder 중 rw로 마운트하는 "
            "것을 조회하려 하면, 기준이 될 사용자가 없어 거부됩니다",
            english=(
                "when a user granted vfolder read in a project tries to list its vfolders mounted "
                "as rw, it is rejected because no user is named"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return AProjectFolderAndSomeone(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]:
        return ListingTheProjectFoldersMountedReadWrite()

    @override
    def then(self) -> Then[AFolderAndItsReader, SearchVFoldersPayload]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class AScopeWithoutAUserRejectsTheMountPermissionFilter(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-scope-without-a-user-rejects-the-mount-permission-filter"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 vfolder 읽기 권한을 받은 사용자가 그 프로젝트만 스코프로 지정해 rw로 "
            "마운트하는 vfolder 를 조회하려 하면, 기준이 될 사용자가 없어 거부됩니다",
            english=(
                "when a user granted vfolder read in a project tries to search vfolders mounted as "
                "rw with only that project as the scope, it is rejected because no user is named"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return AProjectFolderAndSomeone(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingTheProjectScopeMountedReadWrite()

    @override
    def then(self) -> Then[AFolderAndItsReader, SearchVFoldersPayload]:
        return TheCallIsRefused(InvalidAPIParameters)


SCENARIOS: list[RejectionStep] = [
    ASearchOfEveryFolderRejectsTheMountPermissionFilter(),
    AProjectSearchRejectsTheMountPermissionFilter(),
    AScopeWithoutAUserRejectsTheMountPermissionFilter(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_rejecting_mount_permission_filter(
    scenario: RejectionStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
