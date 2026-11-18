"""폴더를 영구히 지우기 — 휴지통에 있어야 하고, 권한이 있어야 한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder.request import PurgeVFolderInput
from ai.backend.common.dto.manager.v2.vfolder.response import PurgeVFolderPayload
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import VFolderFilterStatusFailed
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder import (
    AFolderAndPeople,
    SomeoneWithAFolder,
    VFolderNodeLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PurgingStep = Scenario[
    TestSeedingSession, AFolderAndPeople, VFolderAdapter, PurgeVFolderPayload
]


@dataclass(frozen=True)
class PurgingTheFolder(When[AFolderAndPeople, VFolderAdapter, PurgeVFolderPayload]):
    """휴지통에 있는 자기 폴더를 영구히 지운다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 를 영구히 지웁니다",
            english=f"{laid.caller.username} purges the {laid.folder.name} vfolder",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> PurgeVFolderPayload:
        with ActingAs(laid.caller):
            return await adapter.purge(laid.folder.id, PurgeVFolderInput())


@dataclass(frozen=True)
class TheFolderIsBeingPurged(Then[AFolderAndPeople, PurgeVFolderPayload]):
    """삭제 중 상태의 폴더가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "삭제 중 상태의 vfolder 전체가 응답으로 옵니다",
            english="the whole vfolder in the delete-ongoing state comes back",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[PurgeVFolderPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Held(
                "id",
                payload.id,
                SameAs[UUID](
                    laid.folder.id,
                    Says("부른 vfolder 의 id", english="the id of the vfolder called"),
                ),
            )
        ]
        look = VFolderNodeLook(self.started, status="delete-ongoing")
        verdicts.extend(look.verdicts(payload.vfolder, laid.folder, at="vfolder."))
        return verdicts


@dataclass(frozen=True)
class AGrantedOwnerPurgesTheFolder(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, PurgeVFolderPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-purges-a-trashed-folder"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 vfolder 영구 삭제 권한을 받은 사용자가 휴지통에 있는 자기 "
            "vfolder 를 영구히 지우면, 그 vfolder 가 삭제 중 상태로 응답으로 옵니다",
            english=(
                "when a user granted vfolder hard delete purges their trashed vfolder, that "
                "vfolder comes back delete-ongoing"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(
            permissions=(Permission.HARD_DELETE,), status=VFolderOperationStatus.DELETE_PENDING
        )

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, PurgeVFolderPayload]:
        return PurgingTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, PurgeVFolderPayload]:
        return TheFolderIsBeingPurged(started=self.started)


@dataclass(frozen=True)
class AFolderNotInTheTrashMayNotBePurged(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, PurgeVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "purging-a-folder-outside-the-trash-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "휴지통에 있지 않은 vfolder 를 영구히 지우려 하면 상태가 맞지 않는다는 이유로 "
            "거부됩니다",
            english=(
                "when a user tries to purge a vfolder that is not in the trash, it is rejected "
                "as the status does not allow it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, PurgeVFolderPayload]:
        return PurgingTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, PurgeVFolderPayload]:
        return TheCallIsRefused(VFolderFilterStatusFailed)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurgeTheFolder(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, PurgeVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-their-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 휴지통에 있는 자기 vfolder 를 영구히 지우려 하면 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to purge their trashed vfolder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(status=VFolderOperationStatus.DELETE_PENDING)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, PurgeVFolderPayload]:
        return PurgingTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, PurgeVFolderPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[PurgingStep] = [
    AGrantedOwnerPurgesTheFolder(started=datetime.now(UTC)),
    AFolderNotInTheTrashMayNotBePurged(),
    AUserGrantedNothingMayNotPurgeTheFolder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
