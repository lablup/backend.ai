"""폴더 하나의 이름과 옵션 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.vfolder.request import UpdateVFolderInput
from ai.backend.common.dto.manager.v2.vfolder.response import UpdateVFolderPayload
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import VFolderInvalidParameter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder import (
    SomeoneWithTwoFoldersAndAnothers,
    TwoOwnFoldersAndAnothers,
    VFolderNodeLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

RENAMED = "renamed"

type FolderStep = Scenario[
    TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, UpdateVFolderPayload
]


@dataclass(frozen=True)
class UpdatingTheFirst(When[TwoOwnFoldersAndAnothers, VFolderAdapter, UpdateVFolderPayload]):
    """자기 첫 폴더의 이름을 바꾸고 복제 가능으로 바꾼다. `taken`이면 둘째 폴더의 이름을 쓴다."""

    taken: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: TwoOwnFoldersAndAnothers) -> str:
        name = "둘째 폴더의 이름" if self.taken else RENAMED
        return f"{laid.caller.username}이 자기 첫 폴더를 {name}으로 바꾸고 복제 가능으로 바꿈"

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: TwoOwnFoldersAndAnothers
    ) -> UpdateVFolderPayload:
        name = laid.own[1].name if self.taken else RENAMED
        with ActingAs(laid.caller):
            return await adapter.update(
                laid.own[0].id, UpdateVFolderInput(name=name, cloneable=True)
            )


@dataclass(frozen=True)
class TheFolderIsUpdated(Then[TwoOwnFoldersAndAnothers, UpdateVFolderPayload]):
    """첫 폴더가 새 이름과 복제 가능으로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return f"첫 폴더가 {RENAMED}이라는 이름과 복제 가능으로 온다"

    @override
    def look(
        self, laid: TwoOwnFoldersAndAnothers, answered: Answered[UpdateVFolderPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        look = VFolderNodeLook(self.started, name=RENAMED, cloneable=True)
        return look.verdicts(payload.vfolder, laid.own[0], at="vfolder.")


@dataclass(frozen=True)
class AGrantedOwnerUpdatesTheirFolder(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, UpdateVFolderPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-update-renames-their-folder"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 수정 권한을 받은 사용자가 자기 폴더의 이름과 옵션을 "
            "바꾸면, 바뀐 폴더가 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, UpdateVFolderPayload]:
        return UpdatingTheFirst()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, UpdateVFolderPayload]:
        return TheFolderIsUpdated(started=self.started)


@dataclass(frozen=True)
class ATakenNameIsRefused(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, UpdateVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "renaming-to-a-name-the-owner-already-uses-is-refused"

    @override
    def describe(self) -> str:
        return "자기 다른 폴더가 이미 쓰는 이름으로 바꾸려 하면, 잘못된 값으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, UpdateVFolderPayload]:
        return UpdatingTheFirst(taken=True)

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, UpdateVFolderPayload]:
        return TheCallIsRefused(VFolderInvalidParameter)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotUpdate(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, UpdateVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-update-their-folder"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 자기 폴더를 바꾸려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers()

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, UpdateVFolderPayload]:
        return UpdatingTheFirst()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, UpdateVFolderPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[FolderStep] = [
    AGrantedOwnerUpdatesTheirFolder(started=datetime.now(UTC)),
    ATakenNameIsRefused(),
    AUserGrantedNothingMayNotUpdate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: FolderStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
