"""VFS storage 수정."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.vfs_storage.request import UpdateVFSStorageInput
from ai.backend.common.dto.manager.v2.vfs_storage.response import VFSStorageNode
from ai.backend.manager.api.adapters.vfs_storage.adapter import VFSStorageAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfs_storage import (
    AStorageAndACaller,
    AStorageAndSomeone,
    TheStorageNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MOVED = "/moved/vfs-storage"

type EditingStep = Scenario[TestSeedingSession, Any, VFSStorageAdapter, VFSStorageNode]


@dataclass(frozen=True)
class EditingTheBasePath(When[AStorageAndACaller, VFSStorageAdapter, VFSStorageNode]):
    """미리 만들어 둔 VFS storage 의 기본 경로를 바꾼다. 응답에 담긴 노드를 꺼내서 준다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AStorageAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else laid.storage.name
        return f"{laid.caller.username}이 {target}의 기본 경로 수정"

    @override
    async def call(self, adapter: VFSStorageAdapter, laid: AStorageAndACaller) -> VFSStorageNode:
        storage_id = VFSStorageID(uuid4()) if self.unknown else laid.storage.id
        with ActingAs(laid.caller):
            payload = await adapter.update(
                storage_id, UpdateVFSStorageInput(id=storage_id, base_path=MOVED)
            )
        return payload.vfs_storage


@dataclass(frozen=True)
class TheSuperadminMovesTheBasePath(
    Scenario[TestSeedingSession, AStorageAndACaller, VFSStorageAdapter, VFSStorageNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-changes-the-base-path-of-a-vfs-storage"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 기본 경로만 바꾸면, 기본 경로는 새 값이 되고 나머지는 그대로 남는다"

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AStorageAndACaller, VFSStorageAdapter, VFSStorageNode]:
        return EditingTheBasePath()

    @override
    def then(self) -> Then[AStorageAndACaller, VFSStorageNode]:
        return TheStorageNode(base_path=MOVED)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, AStorageAndACaller, VFSStorageAdapter, VFSStorageNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AStorageAndACaller, VFSStorageAdapter, VFSStorageNode]:
        return EditingTheBasePath(unknown=True)

    @override
    def then(self) -> Then[AStorageAndACaller, VFSStorageNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, AStorageAndACaller, VFSStorageAdapter, VFSStorageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-vfs-storage"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 VFS storage 를 수정하면 권한 부족으로 거부된다. "
            "VFS storage 는 global 에만 속해 그 권한을 받을 방법이 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone()

    @override
    def when(self) -> When[AStorageAndACaller, VFSStorageAdapter, VFSStorageNode]:
        return EditingTheBasePath()

    @override
    def then(self) -> Then[AStorageAndACaller, VFSStorageNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[EditingStep] = [
    TheSuperadminMovesTheBasePath(),
    TheSuperadminEditingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: VFSStorageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
