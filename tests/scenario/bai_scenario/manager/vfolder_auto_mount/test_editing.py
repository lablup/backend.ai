"""자동 마운트의 마운트 위치와 권한 바꾸기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    UpdateVFolderAutoMountInput,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import VFolderAutoMountNode
from ai.backend.common.types import MountPermission
from ai.backend.manager.api.adapters.vfolder_auto_mount.adapter import VFolderAutoMountAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder_auto_mount import (
    AProjectFolderAndAutoMounts,
    AProjectFolderAndSomeone,
    TheAutoMountNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED_AT = "/home/work/edited"

type EditingStep = Scenario[
    TestSeedingSession, AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode
]


@dataclass(frozen=True)
class ChangingTheAutoMount(
    When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]
):
    """마운트 위치와 권한을 바꾼다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AProjectFolderAndAutoMounts) -> str:
        return Says(
            f"{laid.caller.username}이 자동 마운트의 위치를 {EDITED_AT} 로, 권한을 읽기/쓰기로 "
            "바꿉니다",
            english=(
                f"{laid.caller.username} moves the auto-mount to {EDITED_AT} and changes its "
                "permission to read-write"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAutoMountAdapter, laid: AProjectFolderAndAutoMounts
    ) -> VFolderAutoMountNode:
        if laid.mount is None:
            raise LookupError("the auto-mount was not seeded")
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateVFolderAutoMountInput(
                    id=laid.mount.id,
                    mount_destination=EDITED_AT,
                    mount_permission=MountPermission.READ_WRITE,
                )
            )
        return payload.vfolder_auto_mount


@dataclass(frozen=True)
class AGrantedUserChangesTheAutoMount(
    Scenario[
        TestSeedingSession,
        AProjectFolderAndAutoMounts,
        VFolderAutoMountAdapter,
        VFolderAutoMountNode,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-auto-mount-update-changes-its-destination"

    @override
    def describe(self) -> str:
        return Says(
            "자동 마운트 수정 권한을 받은 사용자가 그 자동 마운트의 위치와 권한을 바꾸면, 바뀐 "
            "자동 마운트가 응답으로 옵니다",
            english=(
                "when a user granted auto-mount update changes its destination and permission, "
                "the changed auto-mount comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(permissions=(Permission.UPDATE,), mounted=True)

    @override
    def when(
        self,
    ) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]:
        return ChangingTheAutoMount()

    @override
    def then(self) -> Then[AProjectFolderAndAutoMounts, VFolderAutoMountNode]:
        return TheAutoMountNode(started=self.started, destination=EDITED_AT, permission="rw")


@dataclass(frozen=True)
class AUserGrantedNothingMayNotChangeTheAutoMount(
    Scenario[
        TestSeedingSession,
        AProjectFolderAndAutoMounts,
        VFolderAutoMountAdapter,
        VFolderAutoMountNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-change-an-auto-mount"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자동 마운트를 바꾸려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to change an auto-mount, it is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(mounted=True)

    @override
    def when(
        self,
    ) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]:
        return ChangingTheAutoMount()

    @override
    def then(self) -> Then[AProjectFolderAndAutoMounts, VFolderAutoMountNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[EditingStep] = [
    AGrantedUserChangesTheAutoMount(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotChangeTheAutoMount(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: VFolderAutoMountAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
