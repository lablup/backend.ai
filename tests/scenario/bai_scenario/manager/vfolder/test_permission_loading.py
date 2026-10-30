"""폴더 여럿에서 호출자가 가진 권한과 마운트 수준을 id로 한 번에 읽기 — 자리마다 무엇이 오는가."""

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
    AReaderAndTwoFolders,
    SomeoneWithAFolderOfTheirOwn,
    SomeoneWithTheirFolderAndAnothers,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PermissionsAnswer = list[list[PermissionBitDTO] | Exception]
type MountPermissionsAnswer = list[VFolderPermissionField | Exception | None]
type LoadStep = Scenario[TestSeedingSession, Any, VFolderAdapter, Any]


@dataclass(frozen=True)
class LoadingThePermissionsOfBothFolders(
    When[AReaderAndTwoFolders, VFolderAdapter, PermissionsAnswer]
):
    """자기 폴더, 남의 폴더 순으로 권한을 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_permissions"

    @override
    def describe(self, laid: AReaderAndTwoFolders) -> str:
        return (
            f"{laid.caller.username}이 {laid.readable.name}, {laid.unreadable.name} 순으로 "
            "권한을 일괄 읽음"
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AReaderAndTwoFolders) -> PermissionsAnswer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions([
                VFolderUUID(laid.readable.id),
                VFolderUUID(laid.unreadable.id),
            ])


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
class LoadingTheMountPermissionsOfBothFolders(
    When[AReaderAndTwoFolders, VFolderAdapter, MountPermissionsAnswer]
):
    """자기 폴더, 남의 폴더 순으로 마운트 수준을 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_mount_permissions"

    @override
    def describe(self, laid: AReaderAndTwoFolders) -> str:
        return (
            f"{laid.caller.username}이 {laid.readable.name}, {laid.unreadable.name} 순으로 "
            "마운트 수준을 일괄 읽음"
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AReaderAndTwoFolders
    ) -> MountPermissionsAnswer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_mount_permissions([
                VFolderUUID(laid.readable.id),
                VFolderUUID(laid.unreadable.id),
            ])


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
class ReadAlone(Then[AFolderAndItsReader, PermissionsAnswer]):
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
class ReadWriteAlone(Then[AFolderAndItsReader, MountPermissionsAnswer]):
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
class ReadThenARefusal(Then[AReaderAndTwoFolders, PermissionsAnswer]):
    """자기 폴더는 읽기 권한으로, 남의 폴더는 거부로 온다."""

    @override
    def says(self) -> str:
        return "입력 순서대로 자기 폴더는 읽기 권한, 남의 폴더는 권한 부족 거부가 온다"

    @override
    def look(
        self, laid: AReaderAndTwoFolders, answered: Answered[PermissionsAnswer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) != 2:
            return seen
        first, second = loaded
        seen.append(Same("[0]", first, [PermissionBitDTO.READ]))
        seen.append(Refused(NotEnoughPermission, second if isinstance(second, Exception) else None))
        return seen


@dataclass(frozen=True)
class ReadWriteThenARefusal(Then[AReaderAndTwoFolders, MountPermissionsAnswer]):
    """자기 폴더는 읽기 쓰기로, 남의 폴더는 거부로 온다."""

    @override
    def says(self) -> str:
        return "입력 순서대로 자기 폴더는 읽기 쓰기, 남의 폴더는 권한 부족 거부가 온다"

    @override
    def look(
        self, laid: AReaderAndTwoFolders, answered: Answered[MountPermissionsAnswer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) != 2:
            return seen
        first, second = loaded
        seen.append(Same("[0]", first, VFolderPermissionField.READ_WRITE))
        seen.append(Refused(NotEnoughPermission, second if isinstance(second, Exception) else None))
        return seen


@dataclass(frozen=True)
class ARefusalAlone(Then[AFolderAndItsReader, list[Any]]):
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
        return ReadAlone()


@dataclass(frozen=True)
class AFolderReaderLoadsTheirFoldersPermissionsAndIsRefusedAnothers(
    Scenario[TestSeedingSession, AReaderAndTwoFolders, VFolderAdapter, PermissionsAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-loads-their-folders-permissions-and-is-refused-anothers"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더와 공유받지 않은 남의 "
            "폴더의 권한을 한 번에 읽으면, 입력 순서대로 자기 폴더는 읽기 권한, 남의 폴더는 "
            "권한 부족 거부가 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AReaderAndTwoFolders]:
        return SomeoneWithTheirFolderAndAnothers()

    @override
    def when(self) -> When[AReaderAndTwoFolders, VFolderAdapter, PermissionsAnswer]:
        return LoadingThePermissionsOfBothFolders()

    @override
    def then(self) -> Then[AReaderAndTwoFolders, PermissionsAnswer]:
        return ReadThenARefusal()


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
        return ARefusalAlone()


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
        return ReadWriteAlone()


@dataclass(frozen=True)
class AFolderReaderMountsTheirFolderReadWriteAndIsRefusedAnothers(
    Scenario[TestSeedingSession, AReaderAndTwoFolders, VFolderAdapter, MountPermissionsAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-mounts-their-folder-read-write-and-is-refused-anothers"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더와 공유받지 않은 남의 "
            "폴더의 마운트 수준을 한 번에 읽으면, 입력 순서대로 자기 폴더는 읽기 쓰기, 남의 폴더는 "
            "권한 부족 거부가 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AReaderAndTwoFolders]:
        return SomeoneWithTheirFolderAndAnothers()

    @override
    def when(self) -> When[AReaderAndTwoFolders, VFolderAdapter, MountPermissionsAnswer]:
        return LoadingTheMountPermissionsOfBothFolders()

    @override
    def then(self) -> Then[AReaderAndTwoFolders, MountPermissionsAnswer]:
        return ReadWriteThenARefusal()


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
        return ARefusalAlone()


SCENARIOS: list[LoadStep] = [
    AFolderReaderLoadsTheirFoldersPermissions(),
    AFolderReaderLoadsTheirFoldersPermissionsAndIsRefusedAnothers(),
    AUserGrantedNothingGetsARefusalForTheirFoldersPermissions(),
    AFolderReaderMountsTheirFolderReadWrite(),
    AFolderReaderMountsTheirFolderReadWriteAndIsRefusedAnothers(),
    AUserGrantedNothingGetsARefusalForTheirFoldersMountPermission(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_permission_loading(
    scenario: LoadStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
