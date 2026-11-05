"""자동 마운트 soft delete."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    DeleteVFolderAutoMountInput,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import VFolderAutoMountNode
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

type DeletingStep = Scenario[
    TestSeedingSession, AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode
]


@dataclass(frozen=True)
class DeletingTheAutoMount(
    When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]
):
    """자동 마운트를 삭제된 것으로 표시한다."""

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: AProjectFolderAndAutoMounts) -> str:
        return Says(
            f"{laid.caller.username}이 자동 마운트를 soft delete 합니다",
            english=f"{laid.caller.username} soft deletes the auto-mount",
        )

    @override
    async def call(
        self, adapter: VFolderAutoMountAdapter, laid: AProjectFolderAndAutoMounts
    ) -> VFolderAutoMountNode:
        if laid.mount is None:
            raise LookupError("the auto-mount was not seeded")
        with ActingAs(laid.caller):
            payload = await adapter.delete(DeleteVFolderAutoMountInput(id=laid.mount.id))
        return payload.vfolder_auto_mount


@dataclass(frozen=True)
class AGrantedUserDeletesTheAutoMount(
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
        return "a-user-granted-auto-mount-delete-soft-deletes-it"

    @override
    def describe(self) -> str:
        return Says(
            "자동 마운트 삭제 권한을 받은 사용자가 그 자동 마운트를 soft delete 하면, 삭제된 "
            "자동 마운트가 응답으로 옵니다",
            english=(
                "when a user granted auto-mount delete soft deletes it, the deleted auto-mount "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(permissions=(Permission.SOFT_DELETE,), mounted=True)

    @override
    def when(
        self,
    ) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]:
        return DeletingTheAutoMount()

    @override
    def then(self) -> Then[AProjectFolderAndAutoMounts, VFolderAutoMountNode]:
        return TheAutoMountNode(started=self.started, deleted=True)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDeleteTheAutoMount(
    Scenario[
        TestSeedingSession,
        AProjectFolderAndAutoMounts,
        VFolderAutoMountAdapter,
        VFolderAutoMountNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-an-auto-mount"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자동 마운트를 soft delete 하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to soft delete an auto-mount, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(mounted=True)

    @override
    def when(
        self,
    ) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, VFolderAutoMountNode]:
        return DeletingTheAutoMount()

    @override
    def then(self) -> Then[AProjectFolderAndAutoMounts, VFolderAutoMountNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[DeletingStep] = [
    AGrantedUserDeletesTheAutoMount(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotDeleteTheAutoMount(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deleting(
    scenario: DeletingStep, adapter: VFolderAutoMountAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
