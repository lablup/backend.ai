"""휴지통에서 폴더 되살리기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder.response import RestoreVFolderPayload
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
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
from bai_scenario.components.vfolder import AFolderAndPeople, SomeoneWithAFolder
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RestoringStep = Scenario[
    TestSeedingSession, AFolderAndPeople, VFolderAdapter, RestoreVFolderPayload
]


@dataclass(frozen=True)
class RestoringTheFolder(When[AFolderAndPeople, VFolderAdapter, RestoreVFolderPayload]):
    """휴지통에 있는 자기 폴더를 되살린다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 를 휴지통에서 되살립니다",
            english=f"{laid.caller.username} restores the {laid.folder.name} vfolder from trash",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> RestoreVFolderPayload:
        with ActingAs(laid.caller):
            return await adapter.restore(laid.folder.id)


@dataclass(frozen=True)
class TheFolderIsRestored(Then[AFolderAndPeople, RestoreVFolderPayload]):
    """되살린 폴더의 id 가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "되살린 vfolder 의 id 가 응답으로 옵니다",
            english="the id of the restored vfolder comes back",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[RestoreVFolderPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held(
                "id",
                payload.id,
                SameAs[UUID](
                    laid.folder.id,
                    Says("되살린 vfolder 의 id", english="the id of the restored vfolder"),
                ),
            )
        ]


@dataclass(frozen=True)
class AGrantedOwnerRestoresTheFolder(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, RestoreVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-restores-their-trashed-folder"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 휴지통에 있는 자기 "
            "vfolder 를 되살리면, 그 vfolder 의 id 가 응답으로 옵니다",
            english=(
                "when a user granted vfolder soft delete restores their trashed vfolder, the id "
                "of that vfolder comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(
            permissions=(Permission.SOFT_DELETE,), status=VFolderOperationStatus.DELETE_PENDING
        )

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, RestoreVFolderPayload]:
        return RestoringTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, RestoreVFolderPayload]:
        return TheFolderIsRestored()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestoreTheFolder(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, RestoreVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-their-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 휴지통에 있는 자기 vfolder 를 되살리려 하면 권한 "
            "부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to restore their trashed vfolder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(status=VFolderOperationStatus.DELETE_PENDING)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, RestoreVFolderPayload]:
        return RestoringTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, RestoreVFolderPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RestoringStep] = [
    AGrantedOwnerRestoresTheFolder(),
    AUserGrantedNothingMayNotRestoreTheFolder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_restoring(
    scenario: RestoringStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
