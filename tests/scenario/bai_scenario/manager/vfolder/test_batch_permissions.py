"""폴더에서 내가 가진 권한과 마운트 레벨을 한 번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.common.dto.manager.v2.vfolder.types import VFolderPermissionField
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.vfolder import AFolderAndItsReader, SomeoneWithAFolderOfTheirOwn
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PermissionAnswer = list[list[PermissionBitDTO] | Exception]
type MountLevelAnswer = list[VFolderPermissionField | Exception | None]
type PermissionStep = Scenario[
    TestSeedingSession, AFolderAndItsReader, VFolderAdapter, PermissionAnswer
]
type MountLevelStep = Scenario[
    TestSeedingSession, AFolderAndItsReader, VFolderAdapter, MountLevelAnswer
]


@dataclass(frozen=True)
class LoadingThePermissions(When[AFolderAndItsReader, VFolderAdapter, PermissionAnswer]):
    @override
    def operation(self) -> str:
        return "batch_load_permissions"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 에서 자기 권한을 일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads the permissions they hold on the "
                f"{laid.folder.name} vfolder in one call"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> PermissionAnswer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions([VFolderUUID(laid.folder.id)])


@dataclass(frozen=True)
class LoadingTheMountLevels(When[AFolderAndItsReader, VFolderAdapter, MountLevelAnswer]):
    @override
    def operation(self) -> str:
        return "batch_load_mount_permissions"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 에서 자기 마운트 레벨을 일괄 "
            "조회합니다",
            english=(
                f"{laid.caller.username} loads the mount level they get on the "
                f"{laid.folder.name} vfolder in one call"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> MountLevelAnswer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_mount_permissions([VFolderUUID(laid.folder.id)])


@dataclass(frozen=True)
class TheReadBitAlone(Then[AFolderAndItsReader, PermissionAnswer]):
    """읽기 권한 하나만 실려 온다."""

    @override
    def says(self) -> str:
        return Says(
            "읽기 권한 하나만 실린 답이 옵니다",
            english="an answer holding only the read permission comes back",
        )

    @override
    def look(
        self, laid: AFolderAndItsReader, answered: Answered[PermissionAnswer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Same("[0]", first, [PermissionBitDTO.READ]),
        ]


@dataclass(frozen=True)
class APermissionRefusalAlone(Then[AFolderAndItsReader, PermissionAnswer]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(
        self, laid: AFolderAndItsReader, answered: Answered[PermissionAnswer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class TheReadWriteLevelAlone(Then[AFolderAndItsReader, MountLevelAnswer]):
    """폴더 소유자가 받는 마운트 레벨은 읽기/쓰기다."""

    @override
    def says(self) -> str:
        return Says(
            "읽기/쓰기 마운트 레벨 하나가 실린 답이 옵니다",
            english="an answer holding the one read-write mount level comes back",
        )

    @override
    def look(
        self, laid: AFolderAndItsReader, answered: Answered[MountLevelAnswer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Same("[0]", first, VFolderPermissionField.READ_WRITE),
        ]


@dataclass(frozen=True)
class AMountLevelRefusalAlone(Then[AFolderAndItsReader, MountLevelAnswer]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(
        self, laid: AFolderAndItsReader, answered: Answered[MountLevelAnswer]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class AGrantedReaderLoadsThePermissions(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, PermissionAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-loads-their-permissions"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 읽기 권한을 받은 사용자가 자기 권한을 일괄 조회하면, 읽기 권한 하나가 "
            "실린 답이 옵니다",
            english=(
                "when a user granted vfolder read loads the permissions they hold, an answer "
                "holding only the read permission comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, PermissionAnswer]:
        return LoadingThePermissions()

    @override
    def then(self) -> Then[AFolderAndItsReader, PermissionAnswer]:
        return TheReadBitAlone()


@dataclass(frozen=True)
class AUserGrantedNothingGetsAPermissionRefusal(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, PermissionAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-rejection-in-place-of-permissions"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 권한을 일괄 조회하면, 호출은 성공하되 그 항목은 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing loads the permissions they hold, the call succeeds "
                "but that entry is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, PermissionAnswer]:
        return LoadingThePermissions()

    @override
    def then(self) -> Then[AFolderAndItsReader, PermissionAnswer]:
        return APermissionRefusalAlone()


@dataclass(frozen=True)
class AnOwnerLoadsTheMountLevel(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, MountLevelAnswer]
):
    @override
    def summary(self) -> str:
        return "the-owner-of-a-personal-folder-loads-the-read-write-mount-level"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 vfolder 를 읽을 수 있는 사용자가 자기 마운트 레벨을 일괄 조회하면, "
            "읽기/쓰기 레벨 하나가 실린 답이 옵니다",
            english=(
                "when the user who can read their own personal vfolder loads the mount level "
                "they get, an answer holding the read-write level comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, MountLevelAnswer]:
        return LoadingTheMountLevels()

    @override
    def then(self) -> Then[AFolderAndItsReader, MountLevelAnswer]:
        return TheReadWriteLevelAlone()


@dataclass(frozen=True)
class AUserGrantedNothingGetsAMountLevelRefusal(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, MountLevelAnswer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-rejection-in-place-of-a-mount-level"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 마운트 레벨을 일괄 조회하면, 호출은 성공하되 그 "
            "항목은 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing loads the mount level they get, the call succeeds "
                "but that entry is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, MountLevelAnswer]:
        return LoadingTheMountLevels()

    @override
    def then(self) -> Then[AFolderAndItsReader, MountLevelAnswer]:
        return AMountLevelRefusalAlone()


PERMISSIONS: list[PermissionStep] = [
    AGrantedReaderLoadsThePermissions(),
    AUserGrantedNothingGetsAPermissionRefusal(),
]

MOUNT_LEVELS: list[MountLevelStep] = [
    AnOwnerLoadsTheMountLevel(),
    AUserGrantedNothingGetsAMountLevelRefusal(),
]


@pytest.mark.parametrize("scenario", PERMISSIONS, ids=lambda s: s.summary())
async def test_permissions(
    scenario: PermissionStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", MOUNT_LEVELS, ids=lambda s: s.summary())
async def test_mount_levels(
    scenario: MountLevelStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
