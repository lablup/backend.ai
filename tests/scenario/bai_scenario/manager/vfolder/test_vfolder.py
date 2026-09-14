"""자기 폴더를 만들고 조회하기, 그리고 누가 할 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.vfolder import (
    STORAGE_HOST,
    AFolderMakerAndTheirDomain,
    SomeoneWhoMayMakeFolders,
    SomeoneWithNoGrant,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInput,
    SearchVFoldersInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SearchVFoldersPayload,
    VFolderNode,
)
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
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)

MADE = "work"

type Answer = VFolderNode | SearchVFoldersPayload
type FolderStep = Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]


@dataclass(frozen=True)
class MakingAFolder(When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]):
    """자기 폴더를 하나 만든다."""

    named: str = MADE

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        return f"{laid.caller.username}이 {self.named}이라는 폴더를 만듦"

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
        return "my_search"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        return f"{laid.caller.username}이 자기 폴더를 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderMakerAndTheirDomain) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.my_search(SearchVFoldersInput())


@dataclass(frozen=True)
class TheFolderBelongsToTheMaker(Then[AFolderMakerAndTheirDomain, Answer]):
    """만든 폴더가 통째로 오고, 그 소유는 만든 사람에게 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "만든 폴더 전체가 오고, 소유는 만든 사람에게 있다"

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
                SameAs[UUID | None](laid.caller.id, "만든 사람"),
            ),
            Skipped(
                "ownership.project_id",
                "개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다",
            ),
            Held(
                "ownership.creator_id",
                node.ownership.creator_id,
                SameAs[UUID | None](laid.caller.id, "만든 사람"),
            ),
            Same("ownership.creator_email", node.ownership.creator_email, laid.caller.email),
            Same("unmanaged_path", node.unmanaged_path, None),
            Skipped("id", "데이터베이스가 만든다"),
            Skipped("status", "폴더가 만들어지는 동안 오가는 값이다"),
            Skipped("metadata.usage_mode", "타입이 이미 값을 못박는다"),
            Skipped("metadata.quota_scope_id", "저장소가 정한다"),
            Skipped("access_control.permission", "만든 사람에게는 물어볼 것이 없다"),
            Skipped("quota", "저장소가 답하는 값이라 여기서 말할 수 없다"),
            Held("metadata.created_at", node.metadata.created_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class AGrantedUserMakesAFolderOfTheirOwn(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-create-makes-one-of-their-own"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 폴더 생성 권한을 받은 사용자가 폴더를 만들면, "
            "그 폴더의 소유는 그 사용자에게 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneWhoMayMakeFolders()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return MakingAFolder()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return TheFolderBelongsToTheMaker(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotMakeAFolder(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-make-a-folder"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 폴더를 만들려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneWithNoGrant()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return MakingAFolder(named="denied")

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserWhoMadeNoFolderListsNone(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-has-made-no-folder-lists-none"

    @override
    def describe(self) -> str:
        return "폴더를 하나도 만들지 않은 사용자가 자기 폴더를 조회하면, 답은 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
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
