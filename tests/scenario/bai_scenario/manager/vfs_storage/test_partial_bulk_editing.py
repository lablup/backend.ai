"""VFS storage 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    PartialBulkUpdateVFSStoragesInput,
    UpdateVFSStorageInput,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import VFSStorageNode
from ai.backend.manager.api.adapters.vfs_storage.adapter import VFSStorageAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.vfs_storage import (
    EveryStorageIsProcessed,
    ManyStoragesAndACaller,
    ManyStoragesAndSomeone,
    NothingIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MOVED = "/moved/vfs-storage"

type Edited = PartialBulkPayload[VFSStorageNode]
type EditingStep = Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryBasePath(When[ManyStoragesAndACaller, VFSStorageAdapter, Edited]):
    """미리 만들어 둔 VFS storage 들의 기본 경로를 한 번에 바꾼다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyStoragesAndACaller) -> str:
        return f"{laid.caller.username}이 VFS storage {len(laid.laid)}개의 기본 경로를 한 번에 수정"

    @override
    async def call(self, adapter: VFSStorageAdapter, laid: ManyStoragesAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateVFSStoragesInput(
                    items=[UpdateVFSStorageInput(id=one.id, base_path=MOVED) for one in laid.laid]
                )
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralStorages(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-vfs-storages-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 VFS storage 여럿의 기본 경로를 한 번에 바꾸면, 모두 새 기본 경로로 오고 "
            "실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyStoragesAndACaller, VFSStorageAdapter, Edited]:
        return EditingEveryBasePath()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Edited]:
        return EveryStorageIsProcessed(base_path=MOVED)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-vfs-storages"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 고치려 하면, 고쳐진 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone()

    @override
    def when(self) -> When[ManyStoragesAndACaller, VFSStorageAdapter, Edited]:
        return EditingEveryBasePath()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralStorages(),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: VFSStorageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
