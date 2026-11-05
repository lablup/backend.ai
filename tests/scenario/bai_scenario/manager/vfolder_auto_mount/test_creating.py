"""자동 마운트 만들기 — 누가 만들 수 있고, 만들어진 것이 무엇을 가리키는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    CreateVFolderAutoMountInput,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import VFolderAutoMountNode
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.types import VFolderAutoMountScopeRef
from ai.backend.common.types import MountPermission
from ai.backend.manager.api.adapters.vfolder_auto_mount.adapter import VFolderAutoMountAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder_auto_mount import (
    MOUNTED_AT,
    AProjectFolderAndAutoMounts,
    AProjectFolderAndSomeone,
    TheAutoMountNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type CreatingStep = Scenario[
    TestSeedingSession, AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode
]


@dataclass(frozen=True)
class CreatingTheAutoMount(
    When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]
):
    """그 프로젝트의 폴더를 자동 마운트로 등록한다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AProjectFolderAndAutoMounts) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트의 {laid.folder.name} "
            f"vfolder 를 {MOUNTED_AT} 에 자동 마운트합니다",
            english=(
                f"{laid.caller.username} auto-mounts the {laid.folder.name} vfolder of the "
                f"{laid.project.name} project at {MOUNTED_AT}"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAutoMountAdapter, laid: AProjectFolderAndAutoMounts
    ) -> VFolderAutoMountNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateVFolderAutoMountInput(
                    scope=VFolderAutoMountScopeRef(
                        scope_type=VFolderAutoMountScopeType.PROJECT,
                        scope_id=laid.project.id,
                    ),
                    vfolder_id=laid.folder.id,
                    mount_destination=MOUNTED_AT,
                    mount_permission=MountPermission.READ_ONLY,
                )
            )
        return payload.vfolder_auto_mount


@dataclass(frozen=True)
class AGrantedUserAutoMountsAProjectFolder(
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
        return "a-user-granted-auto-mount-create-registers-a-project-folder"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 자동 마운트 생성 권한을 받은 사용자가 그 프로젝트의 폴더를 자동 "
            "마운트로 등록하면, 그 폴더를 가리키는 자동 마운트가 응답으로 옵니다",
            english=(
                "when a user granted auto-mount create in a project registers one of its "
                "folders, the auto-mount naming that folder comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(permissions=(Permission.CREATE,))

    @override
    def when(
        self,
    ) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]:
        return CreatingTheAutoMount()

    @override
    def then(self) -> Then[AProjectFolderAndAutoMounts, VFolderAutoMountNode]:
        return TheAutoMountNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAutoMount(
    Scenario[
        TestSeedingSession,
        AProjectFolderAndAutoMounts,
        VFolderAutoMountAdapter,
        VFolderAutoMountNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-register-an-auto-mount"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자동 마운트를 등록하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to register an auto-mount, it is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone()

    @override
    def when(
        self,
    ) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]:
        return CreatingTheAutoMount()

    @override
    def then(self) -> Then[AProjectFolderAndAutoMounts, VFolderAutoMountNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CreatingStep] = [
    AGrantedUserAutoMountsAProjectFolder(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotAutoMount(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: VFolderAutoMountAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
