"""폴더를 휴지통에 보내고 되살리기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder.answers import (
    NoAnswer,
)
from bai_scenario.components.vfolder.callers import (
    AProjectFolderTheProjectWouldNotLetGo,
    SomeoneElsesFolder,
    SomeoneElsesTrashedFolderAndABroadGrant,
    SomeoneGrantedOverTheDomainWithAFolder,
)
from bai_scenario.components.vfolder.stage import (
    RETIRING,
    WITHOUT_DELETE,
    AFolderAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.response import (
    BulkDeleteVFoldersPayload,
    DeleteVFolderPayload,
    RestoreVFolderPayload,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import InsufficientStoragePermission, VFolderNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)

type Answer = DeleteVFolderPayload | RestoreVFolderPayload | BulkDeleteVFoldersPayload
type RetiringStep = Scenario[SeedingSession, Any, VFolderAdapter, Answer]


@dataclass(frozen=True)
class SendingItToTheTrash(When[AFolderAndACaller, VFolderAdapter, Answer]):
    """폴더 하나를 휴지통으로 보낸다."""

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: AFolderAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.folder.name}을 지움"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.delete(laid.folder.id)


@dataclass(frozen=True)
class BringingItBack(When[AFolderAndACaller, VFolderAdapter, Answer]):
    """휴지통에 있는 폴더를 되살린다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: AFolderAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.folder.name}을 되살림"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.restore(laid.folder.id)


@dataclass(frozen=True)
class TheFolderIsPointedAt(Then[AFolderAndACaller, Any]):
    """답이 심어둔 폴더를 가리킨다."""

    @override
    def says(self) -> str:
        return "답이 그 폴더를 가리킨다"

    @override
    def look(self, laid: AFolderAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [NoAnswer(answered.raised)]
        return [Held("id", payload.id, SameAs[UUID](laid.folder.id, "심어둔 폴더"))]


@dataclass(frozen=True)
class TheOwnerSendsTheirFolderToTheTrash(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-granted-owner-sends-their-folder-to-the-trash"

    @override
    def describe(self) -> str:
        return (
            "자기 폴더를 지울 권한을 받고 키페어 정책도 그 호스트를 허락한 사용자가 "
            "폴더를 지우면, 지운 폴더를 가리키는 답이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneGrantedOverTheDomainWithAFolder(permissions=RETIRING)

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return SendingItToTheTrash()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheFolderIsPointedAt()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDeleteIt(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-someone-elses-folder"

    @override
    def describe(self) -> str:
        return (
            "남의 폴더에 아무 권한도 받지 않은 사용자가 그것을 지우려 하면, "
            "그 폴더에 걸린 권한이 막아 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneElsesFolder()

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return SendingItToTheTrash()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ThePolicyClosesTheHost(Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-keypair-policy-that-closes-the-host-stops-the-delete"

    @override
    def describe(self) -> str:
        return (
            "폴더를 지울 권한은 받았지만 키페어 정책이 그 호스트에서 지우기를 막아둔 "
            "사용자가 지우려 하면, 권한이 아니라 저장소 쪽이 막아 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneGrantedOverTheDomainWithAFolder(
            permissions=RETIRING, host_permissions=WITHOUT_DELETE
        )

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return SendingItToTheTrash()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheCallIsRefused(InsufficientStoragePermission)


@dataclass(frozen=True)
class TheProjectDoesNotAnswerForDeleting(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "deleting-a-project-folder-asks-the-callers-keypair-policy-not-the-project"

    @override
    def describe(self) -> str:
        return (
            "프로젝트가 그 호스트에서 지우기를 막아두어도, 부르는 사람의 키페어 정책이 "
            "허락하면 그 프로젝트의 폴더가 지워진다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return AProjectFolderTheProjectWouldNotLetGo()

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return SendingItToTheTrash()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheFolderIsPointedAt()


@dataclass(frozen=True)
class WhoeverDeletedItBringsItBack(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "whoever-sent-a-folder-to-the-trash-brings-it-back"

    @override
    def describe(self) -> str:
        return (
            "자기 폴더를 지워 휴지통에 둔 사용자가 같은 권한으로 되살리면, "
            "되살린 폴더를 가리키는 답이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneGrantedOverTheDomainWithAFolder(
            permissions=RETIRING, status=VFolderOperationStatus.DELETE_PENDING
        )

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return BringingItBack()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheFolderIsPointedAt()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestoreIt(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-someone-elses-folder"

    @override
    def describe(self) -> str:
        return (
            "남이 휴지통에 보낸 폴더에 아무 권한도 받지 않은 사용자가 되살리려 하면, "
            "그 폴더에 걸린 권한이 막아 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneElsesFolder(status=VFolderOperationStatus.DELETE_PENDING)

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return BringingItBack()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ABroadGrantStillDoesNotReachSomeoneElses(
    Scenario[SeedingSession, AFolderAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-grant-over-the-whole-domain-still-restores-only-ones-own"

    @override
    def describe(self) -> str:
        return (
            "도메인 전체의 폴더에 지우기 권한을 받은 사용자라도 남이 휴지통에 보낸 폴더를 "
            "되살리려 하면, 권한이 아니라 자기 것이 아니라는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndACaller]:
        return SomeoneElsesTrashedFolderAndABroadGrant()

    @override
    def when(self) -> When[AFolderAndACaller, VFolderAdapter, Answer]:
        return BringingItBack()

    @override
    def then(self) -> Then[AFolderAndACaller, Answer]:
        return TheCallIsRefused(VFolderNotFound)


SCENARIOS: list[RetiringStep] = [
    TheOwnerSendsTheirFolderToTheTrash(),
    AUserGrantedNothingMayNotDeleteIt(),
    ThePolicyClosesTheHost(),
    TheProjectDoesNotAnswerForDeleting(),
    WhoeverDeletedItBringsItBack(),
    AUserGrantedNothingMayNotRestoreIt(),
    ABroadGrantStillDoesNotReachSomeoneElses(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
