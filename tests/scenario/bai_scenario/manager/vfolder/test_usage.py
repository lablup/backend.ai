"""폴더 사용량 조회 — 저장소에 물어 온 값이 그대로 온다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder.types import VFolderUsageInfo
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import NothingComesBack, TheCallIsRefused
from bai_scenario.components.vfolder import (
    AFolderAndPeople,
    SomeoneWithAFolder,
    SomeoneWithAnUnmanagedFolder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type UsageStep = Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, Any]


@dataclass(frozen=True)
class ReadingTheUsage(When[AFolderAndPeople, VFolderAdapter, VFolderUsageInfo]):
    """폴더 사용량을 저장소에서 읽는다."""

    @override
    def operation(self) -> str:
        return "get_folder_usage"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 의 사용량을 조회합니다",
            english=f"{laid.caller.username} reads the usage of the {laid.folder.name} vfolder",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> VFolderUsageInfo:
        with ActingAs(laid.caller):
            usage = await adapter.get_folder_usage(laid.folder.id)
        if usage is None:
            raise LookupError("the storage answered no usage for a managed folder")
        return usage


@dataclass(frozen=True)
class TheUsageOfAnEmptyFolder(Then[AFolderAndPeople, VFolderUsageInfo]):
    """저장소가 답한 사용량이 통째로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "저장소가 답한 사용량 전체가 응답으로 옵니다",
            english="the whole usage the storage answered comes back",
        )

    @override
    def look(self, laid: AFolderAndPeople, answered: Answered[VFolderUsageInfo]) -> list[Verdict]:
        usage = answered.response
        if usage is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("num_files", usage.num_files, 0),
            Same("used_bytes.expr", usage.used_bytes.expr, "0"),
            Same("used_bytes.display", usage.used_bytes.display, "0"),
        ]


@dataclass(frozen=True)
class ReadingTheUnmanagedFolderUsage(
    When[AFolderAndPeople, VFolderAdapter, VFolderUsageInfo | None]
):
    """관리하지 않는 경로를 가리키는 폴더의 사용량을 읽는다."""

    @override
    def operation(self) -> str:
        return "get_folder_usage"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 의 사용량을 조회합니다",
            english=f"{laid.caller.username} reads the usage of the {laid.folder.name} vfolder",
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndPeople
    ) -> VFolderUsageInfo | None:
        with ActingAs(laid.caller):
            return await adapter.get_folder_usage(laid.folder.id)


@dataclass(frozen=True)
class NoUsageForAnUnmanagedFolder(Then[AFolderAndPeople, VFolderUsageInfo | None]):
    """저장소에 물어볼 곳이 없으므로 사용량 없이 끝난다."""

    @override
    def says(self) -> str:
        return Says(
            "관리하지 않는 폴더라 사용량 없이 응답이 끝납니다",
            english="the call answers no usage, as the folder is not managed",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[VFolderUsageInfo | None]
    ) -> list[Verdict]:
        return [NothingComesBack(answered.raised, answered.response)]


@dataclass(frozen=True)
class AGrantedReaderReadsTheUsage(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, VFolderUsageInfo]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-reads-the-folder-usage"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 의 사용량을 "
            "조회하면, 저장소가 답한 사용량이 응답으로 옵니다",
            english=(
                "when a user granted vfolder read in their personal project reads their "
                "folder's usage, the usage the storage answered comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.READ,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, VFolderUsageInfo]:
        return ReadingTheUsage()

    @override
    def then(self) -> Then[AFolderAndPeople, VFolderUsageInfo]:
        return TheUsageOfAnEmptyFolder()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheUsage(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, VFolderUsageInfo]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-folder-usage"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 vfolder 의 사용량을 조회하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to read a folder's usage, it is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder()

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, VFolderUsageInfo]:
        return ReadingTheUsage()

    @override
    def then(self) -> Then[AFolderAndPeople, VFolderUsageInfo]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedReaderReadsAnUnmanagedFoldersUsage(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, VFolderUsageInfo | None]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-reads-no-usage-for-an-unmanaged-folder"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 관리하지 않는 경로를 가리키는 "
            "vfolder 의 사용량을 조회하면, 사용량 없이 응답이 끝납니다",
            english=(
                "when a user granted vfolder read reads the usage of a folder pointing at a path "
                "the manager does not own, the call answers no usage"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAnUnmanagedFolder(permissions=(Permission.READ,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, VFolderUsageInfo | None]:
        return ReadingTheUnmanagedFolderUsage()

    @override
    def then(self) -> Then[AFolderAndPeople, VFolderUsageInfo | None]:
        return NoUsageForAnUnmanagedFolder()


SCENARIOS: list[UsageStep] = [
    AGrantedReaderReadsTheUsage(),
    AUserGrantedNothingMayNotReadTheUsage(),
    AGrantedReaderReadsAnUnmanagedFoldersUsage(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_usage(
    scenario: UsageStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
