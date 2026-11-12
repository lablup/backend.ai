"""자기 폴더를 만들고 조회하기, 그리고 누가 할 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInput,
    ScopedSearchVFoldersInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SearchVFoldersPayload,
    VFolderNode,
)
from ai.backend.common.dto.manager.v2.vfolder.types import VFolderScope
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
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
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.vfolder import (
    STORAGE_HOST,
    AFolderMakerAndTheirDomain,
    SomeoneWhoMayMakeFolders,
    SomeoneWithNoGrant,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MADE = "work"

type Answer = VFolderNode | SearchVFoldersPayload
type FolderStep = Scenario[TestSeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]


@dataclass(frozen=True)
class MakingAFolder(When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]):
    """자기 폴더를 하나 만든다."""

    named: str = MADE

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        return Says(
            f"{laid.caller.username}이 {self.named} 이라는 이름으로 vfolder 를 생성합니다",
            english=f"{laid.caller.username} creates a vfolder named {self.named}",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderMakerAndTheirDomain) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.create(CreateVFolderInput(name=self.named))
        return payload.vfolder


@dataclass(frozen=True)
class ListingMyFolders(When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]):
    """자기 폴더를 훑는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        return Says(
            f"{laid.caller.username}이 자기 vfolder 를 조회합니다",
            english=f"{laid.caller.username} lists their own vfolders",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderMakerAndTheirDomain) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchVFoldersInput(
                    scope=VFolderScope(user=[UUIDScope(value=laid.caller.id)])
                )
            )


@dataclass(frozen=True)
class TheFolderBelongsToTheMaker(Then[AFolderMakerAndTheirDomain, Answer]):
    """만든 폴더가 통째로 오고, 그 소유는 만든 사람에게 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "만든 vfolder 전체가 응답으로 오고, 그 소유는 만든 사람에게 있습니다",
            english=(
                "the whole vfolder just created comes back and its ownership belongs to the creator"
            ),
        )

    @override
    def look(self, laid: AFolderMakerAndTheirDomain, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, VFolderNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("host", node.host, STORAGE_HOST),
            Same("metadata.name", node.metadata.name, MADE),
            Same("metadata.cloneable", node.metadata.cloneable, False),
            Same("metadata.last_used", node.metadata.last_used, None),
            Same("access_control.ownership_type", node.access_control.ownership_type, "user"),
            Held(
                "ownership.user_id",
                node.ownership.user_id,
                SameAs[UUID | None](laid.caller.id, Says("만든 사람", english="the creator")),
            ),
            Skipped(
                "ownership.project_id",
                Says(
                    "개인 vfolder 는 그 사용자의 개인 프로젝트에 붙습니다. 그 id 는 사용자를 "
                    "생성할 때 생깁니다",
                    english=(
                        "a personal vfolder belongs to the user's personal project. That id is "
                        "made when the user is created"
                    ),
                ),
            ),
            Held(
                "ownership.creator_id",
                node.ownership.creator_id,
                SameAs[UUID | None](laid.caller.id, Says("만든 사람", english="the creator")),
            ),
            Same("ownership.creator_email", node.ownership.creator_email, laid.caller.email),
            Same("unmanaged_path", node.unmanaged_path, None),
            Skipped(
                "id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Skipped(
                "status",
                Says(
                    "vfolder 가 생성되는 동안 오가는 값입니다",
                    english="a value that moves while the vfolder is being created",
                ),
            ),
            Skipped(
                "metadata.usage_mode",
                Says("타입이 이미 값을 고정합니다", english="the type already fixes the value"),
            ),
            Skipped(
                "metadata.quota_scope_id",
                Says("저장소가 정합니다", english="the storage decides it"),
            ),
            Skipped(
                "access_control.permission",
                Says(
                    "만든 사람에게는 확인할 것이 없습니다",
                    english="there is nothing to check for the creator",
                ),
            ),
            Skipped(
                "quota",
                Says(
                    "저장소가 응답하는 값이라 여기서 말할 수 없습니다",
                    english="the storage answers it, so it cannot be stated here",
                ),
            ),
            Held("metadata.created_at", node.metadata.created_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class AGrantedUserMakesAFolderOfTheirOwn(
    Scenario[TestSeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-create-makes-one-of-their-own"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프에서 vfolder 생성 권한을 받은 사용자가 vfolder 를 생성하면, 그 vfolder 의 "
            "소유는 그 사용자에게 있습니다",
            english=(
                "when a user granted vfolder create in their own scope creates a vfolder, its "
                "ownership belongs to that user"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneWhoMayMakeFolders()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return MakingAFolder()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return TheFolderBelongsToTheMaker(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotMakeAFolder(
    Scenario[TestSeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-make-a-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 vfolder 를 생성하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to create a vfolder, it is rejected for lack "
                "of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneWithNoGrant()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return MakingAFolder(named="denied")

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserWhoMadeNoFolderListsNone(
    Scenario[TestSeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-has-made-no-folder-lists-none"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 를 하나도 생성하지 않은 사용자가 자기 vfolder 를 조회하면, 응답은 비어 있습니다",
            english=(
                "when a user who has created no vfolder lists their own vfolders, the answer "
                "is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneWhoMayMakeFolders()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return ListingMyFolders()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return NothingIsFound()


SCENARIOS: list[FolderStep] = [
    AGrantedUserMakesAFolderOfTheirOwn(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotMakeAFolder(),
    AUserWhoMadeNoFolderListsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_vfolder(
    scenario: FolderStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
