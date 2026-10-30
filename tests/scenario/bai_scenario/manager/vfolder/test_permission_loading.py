"""폴더에서 호출자가 가진 권한과 마운트 수준을 id로 일괄 읽기 — 대표 성공과 대표 실패."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.vfolder import (
    AFolderAndItsReader,
    SomeoneWithAFolderOfTheirOwn,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PermissionsAnswer = list[list[PermissionBitDTO] | Exception]
type MountPermissionsAnswer = list[VFolderPermissionField | Exception | None]
type LoadStep = Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Any]


@dataclass(frozen=True)
class LoadingThePermissionsOfTheFolder(
    When[AFolderAndItsReader, VFolderAdapter, PermissionsAnswer]
):
    """폴더 id 하나의 권한만 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_permissions"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return f"{laid.caller.username}이 {laid.folder.name} 폴더의 권한을 일괄 읽음"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> PermissionsAnswer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions([VFolderUUID(laid.folder.id)])


@dataclass(frozen=True)
class LoadingTheMountPermissionOfTheFolder(
    When[AFolderAndItsReader, VFolderAdapter, MountPermissionsAnswer]
):
    """폴더 id 하나의 마운트 수준만 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_mount_permissions"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return f"{laid.caller.username}이 {laid.folder.name} 폴더의 마운트 수준을 일괄 읽음"

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndItsReader
    ) -> MountPermissionsAnswer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_mount_permissions([VFolderUUID(laid.folder.id)])


@dataclass(frozen=True)
class ReadPermission(Then[AFolderAndItsReader, PermissionsAnswer]):
    """그 폴더 하나가 읽기 권한으로 온다."""

    @override
    def says(self) -> str:
        return "그 폴더 하나가 읽기 권한으로 온다"

    @override
    def look(
        self, laid: AFolderAndItsReader, answered: Answered[PermissionsAnswer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [Same("loaded", loaded, [[PermissionBitDTO.READ]])]


@dataclass(frozen=True)
class ReadWriteMount(Then[AFolderAndItsReader, MountPermissionsAnswer]):
    """그 폴더 하나가 읽기 쓰기로 온다."""

    @override
    def says(self) -> str:
        return "그 폴더 하나가 읽기 쓰기로 온다"

    @override
    def look(
        self, laid: AFolderAndItsReader, answered: Answered[MountPermissionsAnswer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [Same("loaded", loaded, [VFolderPermissionField.READ_WRITE])]


@dataclass(frozen=True)
class ARefusal(Then[AFolderAndItsReader, list[Any]]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return "그 자리는 권한 부족으로 거부된다"

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[list[Any]]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class AFolderReaderLoadsTheirFoldersPermissions(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, PermissionsAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-loads-their-folders-permissions"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더의 권한을 일괄 읽기로 "
            "읽으면, 읽기 권한이 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, PermissionsAnswer]:
        return LoadingThePermissionsOfTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, PermissionsAnswer]:
        return ReadPermission()


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForTheirFoldersPermissions(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, PermissionsAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-in-place-of-their-folders-permissions"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 자기 폴더의 권한을 일괄 읽기로 읽으면, "
            "호출은 성공하되 그 자리는 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, PermissionsAnswer]:
        return LoadingThePermissionsOfTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, PermissionsAnswer]:
        return ARefusal()


@dataclass(frozen=True)
class AFolderReaderMountsTheirFolderReadWrite(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, MountPermissionsAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-mounts-their-folder-read-write"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더의 마운트 수준을 일괄 "
            "읽기로 읽으면, 읽기 쓰기가 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, MountPermissionsAnswer]:
        return LoadingTheMountPermissionOfTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, MountPermissionsAnswer]:
        return ReadWriteMount()


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForTheirFoldersMountPermission(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, MountPermissionsAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-in-place-of-their-folders-mount-permission"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 자기 폴더의 마운트 수준을 일괄 읽기로 읽으면, "
            "호출은 성공하되 그 자리는 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, MountPermissionsAnswer]:
        return LoadingTheMountPermissionOfTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, MountPermissionsAnswer]:
        return ARefusal()


SCENARIOS: list[LoadStep] = [
    AFolderReaderLoadsTheirFoldersPermissions(),
    AUserGrantedNothingGetsARefusalForTheirFoldersPermissions(),
    AFolderReaderMountsTheirFolderReadWrite(),
    AUserGrantedNothingGetsARefusalForTheirFoldersMountPermission(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_permission_loading(
    scenario: LoadStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
