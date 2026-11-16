"""폴더를 휴지통으로 옮기기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder.response import DeleteVFolderPayload
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
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
from bai_scenario.components.vfolder import (
    AFolderAndPeople,
    SomeoneWithAFolder,
    VFolderNodeLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type DeletingStep = Scenario[
    TestSeedingSession, AFolderAndPeople, VFolderAdapter, DeleteVFolderPayload
]


@dataclass(frozen=True)
class DeletingTheFolder(When[AFolderAndPeople, VFolderAdapter, DeleteVFolderPayload]):
    """자기 폴더를 soft delete 한다."""

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 를 soft delete 합니다",
            english=f"{laid.caller.username} soft deletes the {laid.folder.name} vfolder",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> DeleteVFolderPayload:
        with ActingAs(laid.caller):
            return await adapter.delete(laid.folder.id)


@dataclass(frozen=True)
class TheFolderIsInTheTrash(Then[AFolderAndPeople, DeleteVFolderPayload]):
    """삭제 대기 상태의 폴더가 통째로 온다. id 는 시나리오가 부른 폴더의 id 다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "삭제 대기 상태의 vfolder 전체가 응답으로 옵니다",
            english="the whole vfolder in the delete-pending state comes back",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[DeleteVFolderPayload]
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
        look = VFolderNodeLook(self.started, status="delete-pending")
        verdicts.extend(look.verdicts(payload.vfolder, laid.folder, at="vfolder."))
        return verdicts


@dataclass(frozen=True)
class AGrantedOwnerDeletesTheFolder(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, DeleteVFolderPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-soft-deletes-their-folder"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 vfolder soft delete 권한을 받은 사용자가 자기 vfolder 를 "
            "soft delete 하면, 그 vfolder 가 삭제 대기 상태로 응답으로 옵니다",
            english=(
                "when a user granted vfolder soft delete in their personal project soft deletes "
                "their own vfolder, that vfolder comes back delete-pending"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.SOFT_DELETE,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, DeleteVFolderPayload]:
        return DeletingTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, DeleteVFolderPayload]:
        return TheFolderIsInTheTrash(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDeleteTheFolder(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, DeleteVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-soft-delete-their-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 vfolder 를 soft delete 하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to soft delete their own vfolder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder()

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, DeleteVFolderPayload]:
        return DeletingTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, DeleteVFolderPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[DeletingStep] = [
    AGrantedOwnerDeletesTheFolder(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotDeleteTheFolder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deleting(
    scenario: DeletingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
