"""폴더 여럿 수정, soft delete, restore."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.vfolder.request import (
    PartialBulkDeleteVFoldersInput,
    PartialBulkRestoreVFoldersInput,
    PartialBulkUpdateVFolderItemInput,
    PartialBulkUpdateVFoldersInput,
    UpdateVFolderInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import VFolderNode
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import Mentions
from bai_scenario.components.vfolder import (
    SomeoneWithTwoFoldersAndAnothers,
    TwoOwnFoldersAndAnothers,
    VFolderNodeLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

DENIED = "Insufficient permission"

type Processed = PartialBulkPayload[VFolderNode]
type FolderStep = Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]


@dataclass(frozen=True)
class UpdatingAll(When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]):
    """자기 폴더 둘과 남의 폴더 하나를 한 번에 복제 가능으로 바꾼다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: TwoOwnFoldersAndAnothers) -> str:
        return (
            f"{laid.caller.username}이 자기 폴더 둘과 남의 폴더 하나를 한 번에 복제 가능으로 바꿈"
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: TwoOwnFoldersAndAnothers) -> Processed:
        items = [
            PartialBulkUpdateVFolderItemInput(
                id=folder.id, input=UpdateVFolderInput(cloneable=True)
            )
            for folder in (*laid.own, laid.others)
        ]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(PartialBulkUpdateVFoldersInput(items=items))


@dataclass(frozen=True)
class SoftDeletingAll(When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]):
    """자기 폴더 둘과 남의 폴더 하나를 한 번에 soft delete 한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_delete"

    @override
    def describe(self, laid: TwoOwnFoldersAndAnothers) -> str:
        return f"{laid.caller.username}이 자기 폴더 둘과 남의 폴더 하나를 한 번에 soft delete 함"

    @override
    async def call(self, adapter: VFolderAdapter, laid: TwoOwnFoldersAndAnothers) -> Processed:
        ids: list[UUID] = [folder.id for folder in (*laid.own, laid.others)]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_delete(PartialBulkDeleteVFoldersInput(ids=ids))


@dataclass(frozen=True)
class SoftDeletingThenRestoringOwn(When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]):
    """자기 폴더 둘을 한 번에 soft delete 했다가 한 번에 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: TwoOwnFoldersAndAnothers) -> str:
        return (
            f"{laid.caller.username}이 자기 폴더 둘을 한 번에 soft delete 했다가 한 번에 restore 함"
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: TwoOwnFoldersAndAnothers) -> Processed:
        ids: list[UUID] = [folder.id for folder in laid.own]
        with ActingAs(laid.caller):
            await adapter.partial_bulk_delete(PartialBulkDeleteVFoldersInput(ids=ids))
            return await adapter.partial_bulk_restore(PartialBulkRestoreVFoldersInput(ids=ids))


@dataclass(frozen=True)
class DeniedLook:
    """실패 목록이 이 폴더들을 이 순서로 권한 부족 이유와 함께 싣는다."""

    folders: tuple[VFolderData, ...]

    def verdicts(self, payload: Processed) -> list[Verdict]:
        verdicts: list[Verdict] = [Same("failed count", len(payload.failed), len(self.folders))]
        for i, (failure, folder) in enumerate(zip(payload.failed, self.folders, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(folder.id, "대상 폴더의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(DENIED)),
            ]
        return verdicts


@dataclass(frozen=True)
class OwnAreProcessed(Then[TwoOwnFoldersAndAnothers, Processed]):
    """자기 폴더 둘은 처리된 목록에 오고, `others_denied`면 남의 폴더는 권한 부족으로 실패 목록에 온다."""

    started: datetime
    status: str
    cloneable: bool
    others_denied: bool

    @override
    def says(self) -> str:
        state = "복제 가능으로" if self.cloneable else f"{self.status} 상태로"
        if not self.others_denied:
            return f"자기 폴더 둘이 {state} 오고, 실패한 것은 없다"
        return f"자기 폴더 둘이 {state} 오고, 남의 폴더는 권한이 없다는 이유로 실패 목록에 온다"

    @override
    def look(self, laid: TwoOwnFoldersAndAnothers, answered: Answered[Processed]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        look = VFolderNodeLook(self.started, status=self.status, cloneable=self.cloneable)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), 2)]
        for i, (node, folder) in enumerate(zip(payload.successes, laid.own, strict=False)):
            verdicts += look.verdicts(node, folder, at=f"successes[{i}].")
        if not self.others_denied:
            return [*verdicts, Same("failed", payload.failed, [])]
        return [*verdicts, *DeniedLook((laid.others,)).verdicts(payload)]


@dataclass(frozen=True)
class NothingIsProcessed(Then[TwoOwnFoldersAndAnothers, Processed]):
    """처리된 폴더 없이, 셋 모두 권한 부족으로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return "처리된 폴더 없이 셋 모두 권한이 없다는 이유로 실패 목록에 온다"

    @override
    def look(self, laid: TwoOwnFoldersAndAnothers, answered: Answered[Processed]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("successes", payload.successes, []),
            *DeniedLook((*laid.own, laid.others)).verdicts(payload),
        ]


@dataclass(frozen=True)
class AGrantedOwnerUpdatesTheirsOnly(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-update-updates-their-folders-of-several"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 수정 권한을 받은 사용자가 자기 폴더 둘과 남의 폴더 하나를 "
            "한 번에 수정하면, 자기 폴더 둘은 수정되어 오고 남의 폴더는 권한 부족으로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]:
        return UpdatingAll()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, Processed]:
        return OwnAreProcessed(
            started=self.started, status="ready", cloneable=True, others_denied=True
        )


@dataclass(frozen=True)
class AUserGrantedNothingUpdatesNone(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-updates-none-of-several-folders"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 폴더 여럿을 한 번에 수정하려 하면, 수정된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers()

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]:
        return UpdatingAll()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, Processed]:
        return NothingIsProcessed()


@dataclass(frozen=True)
class AGrantedOwnerSoftDeletesTheirsOnly(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 soft delete 권한을 받은 사용자가 자기 폴더 둘과 남의 폴더 "
            "하나를 한 번에 soft delete 하면, 자기 폴더 둘은 삭제 대기로 오고 남의 폴더는 권한 "
            "부족으로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers(permissions=(Permission.SOFT_DELETE,))

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]:
        return SoftDeletingAll()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, Processed]:
        return OwnAreProcessed(
            started=self.started, status="delete-pending", cloneable=False, others_denied=True
        )


@dataclass(frozen=True)
class AUserGrantedNothingSoftDeletesNone(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-soft-deletes-none-of-several-folders"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 폴더 여럿을 한 번에 soft delete 하려 하면, soft delete "
            "된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers()

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]:
        return SoftDeletingAll()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, Processed]:
        return NothingIsProcessed()


@dataclass(frozen=True)
class RestoringBringsSeveralBack(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-several-folders-brings-them-back"

    @override
    def describe(self) -> str:
        return (
            "폴더 soft delete 권한을 받은 사용자가 soft delete 한 자기 폴더 둘을 한 번에 restore "
            "하면, 둘 다 쓸 수 있는 상태로 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers(permissions=(Permission.SOFT_DELETE,))

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]:
        return SoftDeletingThenRestoringOwn()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, Processed]:
        return OwnAreProcessed(
            started=self.started, status="ready", cloneable=False, others_denied=False
        )


SCENARIOS: list[FolderStep] = [
    AGrantedOwnerUpdatesTheirsOnly(started=datetime.now(UTC)),
    AUserGrantedNothingUpdatesNone(),
    AGrantedOwnerSoftDeletesTheirsOnly(started=datetime.now(UTC)),
    AUserGrantedNothingSoftDeletesNone(),
    RestoringBringsSeveralBack(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk(
    scenario: FolderStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
