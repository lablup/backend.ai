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
from ai.backend.manager.data.vfolder.types import VFolderData, VFolderOperationStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
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
        return Says(
            f"{laid.caller.username}이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 "
            "복제 가능으로 변경합니다",
            english=(
                f"{laid.caller.username} makes their two vfolders and someone else's vfolder "
                "cloneable in one call"
            ),
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
        return Says(
            f"{laid.caller.username}이 자기 vfolder 둘과 다른 사용자의 vfolder 하나를 한 번에 "
            "soft delete 합니다",
            english=(
                f"{laid.caller.username} soft deletes their two vfolders and someone else's "
                "vfolder in one call"
            ),
        )

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
        return Says(
            f"{laid.caller.username}이 자기 vfolder 둘을 한 번에 soft delete 했다가 한 번에 "
            "restore 합니다. restore 의 응답을 반환합니다",
            english=(
                f"{laid.caller.username} soft deletes their two vfolders in one call and then "
                "restores them in one call. It answers the restore"
            ),
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
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        folder.id,
                        Says("대상 vfolder 의 id", english="the id of the target vfolder"),
                    ),
                ),
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
        state_en = "cloneable" if self.cloneable else f"in the {self.status} state"
        if not self.others_denied:
            return Says(
                f"자기 vfolder 둘이 {state} 오고, 실패한 것은 없습니다",
                english=f"both of their vfolders come back {state_en} and nothing failed",
            )
        return Says(
            f"자기 vfolder 둘이 {state} 오고, 다른 사용자의 vfolder 는 권한이 없다는 이유로 "
            "실패 목록에 옵니다",
            english=(
                f"both of their vfolders come back {state_en} and the other user's vfolder "
                "comes back in the failed list for lack of permission"
            ),
        )

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
        return Says(
            "처리된 vfolder 없이, 셋 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "no vfolder is processed and all three come back in the failed list for lack "
                "of permission"
            ),
        )

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
        return Says(
            "자기 개인 프로젝트에서 vfolder 수정 권한을 받은 사용자가 자기 vfolder 둘과 다른 "
            "사용자의 vfolder 하나를 한 번에 수정하면, 자기 vfolder 둘은 수정되어 응답으로 오고 "
            "다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다",
            english=(
                "when a user granted vfolder update in their personal project updates their two "
                "vfolders and someone else's vfolder in one call, their two vfolders come back "
                "updated and the other user's vfolder comes back in the failed list for lack of "
                "permission"
            ),
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
        return Says(
            "아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 수정하려 하면, 수정된 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to update several vfolders in one call, none "
                "is updated and all come back in the failed list for lack of permission"
            ),
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
        return Says(
            "자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 자기 vfolder 둘과 "
            "다른 사용자의 vfolder 하나를 한 번에 soft delete 하면, 자기 vfolder 둘은 삭제 "
            "대기로 오고 다른 사용자의 vfolder 는 권한 부족으로 실패 목록에 옵니다",
            english=(
                "when a user granted vfolder soft delete in their personal project soft deletes "
                "their two vfolders and someone else's vfolder in one call, their two vfolders "
                "come back delete-pending and the other user's vfolder comes back in the failed "
                "list for lack of permission"
            ),
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
        return Says(
            "아무 권한도 받지 않은 사용자가 vfolder 여럿을 한 번에 soft delete 하려 하면, soft "
            "delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to soft delete several vfolders in one call, "
                "none is soft deleted and all come back in the failed list for lack of permission"
            ),
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
        return Says(
            "vfolder soft delete 권한을 받은 사용자가 soft delete 한 자기 vfolder 둘을 한 번에 "
            "restore 하면, 둘 다 사용할 수 있는 상태로 옵니다",
            english=(
                "when a user granted vfolder soft delete restores their two soft-deleted "
                "vfolders in one call, both come back ready for use"
            ),
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


@dataclass(frozen=True)
class RestoringBothWithOneStillPurging(When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]):
    """휴지통에 있는 폴더와 삭제가 진행 중인 폴더를 한 번에 되살린다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: TwoOwnFoldersAndAnothers) -> str:
        return Says(
            f"{laid.caller.username}이 휴지통에 있는 자기 vfolder 와 삭제가 진행 중인 자기 "
            "vfolder 를 한 번에 restore 합니다",
            english=(
                f"{laid.caller.username} restores their trashed vfolder and their vfolder whose "
                "deletion is still in progress in one call"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: TwoOwnFoldersAndAnothers) -> Processed:
        ids: list[UUID] = [laid.own[0].id, laid.own[1].id]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_restore(PartialBulkRestoreVFoldersInput(ids=ids))


@dataclass(frozen=True)
class OnlyTheTrashedFolderComesBack(Then[TwoOwnFoldersAndAnothers, Processed]):
    """휴지통에 있던 폴더만 되살아나고, 삭제 중인 폴더는 실패 목록에 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "휴지통에 있던 폴더만 사용할 수 있는 상태로 오고, 삭제가 진행 중인 폴더는 실패 "
            "목록에 옵니다",
            english=(
                "only the trashed folder comes back ready for use, and the folder whose "
                "deletion is in progress comes back in the failed list"
            ),
        )

    @override
    def look(self, laid: TwoOwnFoldersAndAnothers, answered: Answered[Processed]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), 1)]
        if payload.successes:
            verdicts.extend(
                VFolderNodeLook(self.started).verdicts(
                    payload.successes[0], laid.own[0], at="successes[0]."
                )
            )
        verdicts.append(Same("failed count", len(payload.failed), 1))
        if payload.failed:
            failure = payload.failed[0]
            verdicts.extend([
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        laid.own[1].id,
                        Says(
                            "삭제가 진행 중인 vfolder",
                            english="the vfolder whose deletion is in progress",
                        ),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("being purged")),
            ])
        return verdicts


@dataclass(frozen=True)
class ARestoreLeavesThePurgingFolderOut(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-several-folders-leaves-the-purging-one-out"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 폴더와 삭제가 진행 중인 "
            "폴더를 한 번에 restore 하면, 휴지통에 있던 폴더만 되살아나고 삭제 중인 폴더는 "
            "실패 목록에 옵니다",
            english=(
                "when a user granted vfolder soft delete restores a trashed vfolder and a folder "
                "whose deletion is in progress in one call, only the trashed folder comes back "
                "and the other comes back in the failed list"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers(
            permissions=(Permission.SOFT_DELETE,),
            first_status=VFolderOperationStatus.DELETE_PENDING,
            second_status=VFolderOperationStatus.DELETE_ONGOING,
        )

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]:
        return RestoringBothWithOneStillPurging()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, Processed]:
        return OnlyTheTrashedFolderComesBack(started=self.started)


@dataclass(frozen=True)
class RestoringOwnAndAnothers(When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]):
    """휴지통에 있는 자기 폴더 하나와 남의 폴더 하나를 한 번에 되살린다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: TwoOwnFoldersAndAnothers) -> str:
        return Says(
            f"{laid.caller.username}이 휴지통에 있는 자기 vfolder 하나와 다른 사용자의 vfolder "
            "하나를 한 번에 restore 합니다",
            english=(
                f"{laid.caller.username} restores their trashed vfolder and another user's "
                "vfolder in one call"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: TwoOwnFoldersAndAnothers) -> Processed:
        ids: list[UUID] = [laid.own[0].id, laid.others.id]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_restore(PartialBulkRestoreVFoldersInput(ids=ids))


@dataclass(frozen=True)
class TheRestoredFolderAlone(Then[TwoOwnFoldersAndAnothers, Processed]):
    """휴지통에 있던 자기 폴더만 되살아나고, 남의 폴더는 권한 부족으로 실패 목록에 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "휴지통에 있던 자기 폴더만 사용할 수 있는 상태로 오고, 다른 사용자의 폴더는 권한이 "
            "없다는 이유로 실패 목록에 옵니다",
            english=(
                "only their trashed folder comes back ready for use, and the other user's folder "
                "comes back in the failed list for lack of permission"
            ),
        )

    @override
    def look(self, laid: TwoOwnFoldersAndAnothers, answered: Answered[Processed]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), 1)]
        if payload.successes:
            verdicts.extend(
                VFolderNodeLook(self.started).verdicts(
                    payload.successes[0], laid.own[0], at="successes[0]."
                )
            )
        return [*verdicts, *DeniedLook((laid.others,)).verdicts(payload)]


@dataclass(frozen=True)
class ARestoreLeavesAnothersFolderOut(
    Scenario[TestSeedingSession, TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-several-folders-leaves-anothers-out"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 자기 폴더와 다른 사용자의 "
            "폴더를 한 번에 restore 하면, 자기 폴더만 되살아나고 다른 사용자의 폴더는 권한 부족 "
            "으로 실패 목록에 옵니다",
            english=(
                "when a user granted vfolder soft delete restores their trashed folder and another "
                "user's folder in one call, only their folder comes back and the other user's "
                "folder comes back in the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoOwnFoldersAndAnothers]:
        return SomeoneWithTwoFoldersAndAnothers(
            permissions=(Permission.SOFT_DELETE,),
            first_status=VFolderOperationStatus.DELETE_PENDING,
            second_status=VFolderOperationStatus.DELETE_PENDING,
        )

    @override
    def when(self) -> When[TwoOwnFoldersAndAnothers, VFolderAdapter, Processed]:
        return RestoringOwnAndAnothers()

    @override
    def then(self) -> Then[TwoOwnFoldersAndAnothers, Processed]:
        return TheRestoredFolderAlone(started=self.started)


SCENARIOS: list[FolderStep] = [
    AGrantedOwnerUpdatesTheirsOnly(started=datetime.now(UTC)),
    AUserGrantedNothingUpdatesNone(),
    AGrantedOwnerSoftDeletesTheirsOnly(started=datetime.now(UTC)),
    AUserGrantedNothingSoftDeletesNone(),
    RestoringBringsSeveralBack(started=datetime.now(UTC)),
    ARestoreLeavesThePurgingFolderOut(started=datetime.now(UTC)),
    ARestoreLeavesAnothersFolderOut(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk(
    scenario: FolderStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
