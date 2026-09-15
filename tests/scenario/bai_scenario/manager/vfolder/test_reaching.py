"""누구의 폴더에 닿는가: 자기 폴더, 프로젝트 폴더, 공유받은 폴더."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.vfolder import (
    STORAGE_HOST,
    AFolderAndItsReader,
    AFolderOfferedToSomeone,
    AProjectFolderAndSomeone,
    SomeoneWithAFolderOfTheirOwn,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SearchVFoldersPayload,
    VFolderNode,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)

type Answer = VFolderNode | SearchVFoldersPayload
type ReachStep = Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]


@dataclass(frozen=True)
class ReadingTheFolder(When[AFolderAndItsReader, VFolderAdapter, Answer]):
    """폴더 하나를 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return f"{laid.caller.username}이 {laid.folder.name} 폴더를 읽음"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.get(laid.folder.id)


@dataclass(frozen=True)
class ListingTheProjectFolders(When[AFolderAndItsReader, VFolderAdapter, Answer]):
    """폴더가 놓인 프로젝트의 폴더를 훑는다."""

    @override
    def operation(self) -> str:
        return "project_search"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return f"{laid.caller.username}이 {laid.folder.name} 폴더가 놓인 프로젝트의 폴더를 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> Answer:
        project = laid.folder.group
        if project is None:
            raise LookupError("the folder was laid in no project")
        with ActingAs(laid.caller):
            return await adapter.project_search(project, SearchVFoldersInput())


@dataclass(frozen=True)
class TheFolderIsReached(Then[AFolderAndItsReader, Answer]):
    """심은 폴더가 통째로 온다. 훑었다면 그 폴더 하나만 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 폴더 전체가 온다"

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[Answer]) -> list[Verdict]:
        answer = answered.response
        if isinstance(answer, VFolderNode):
            return self._node("", answer, laid.folder)
        if isinstance(answer, SearchVFoldersPayload):
            page: list[Verdict] = [
                Same("total_count", answer.total_count, 1),
                Same("has_next_page", answer.has_next_page, False),
                Same("has_previous_page", answer.has_previous_page, False),
                Same("items.length", len(answer.items), 1),
            ]
            if answer.items:
                page.extend(self._node("items[0].", answer.items[0], laid.folder))
            return page
        raised = type(answered.raised).__name__ if answered.raised is not None else None
        return [Same("answer", raised, "VFolderNode")]

    def _node(self, at: str, node: VFolderNode, folder: VFolderData) -> list[Verdict]:
        return [
            Held(f"{at}id", node.id, SameAs[UUID](folder.id, "심은 폴더")),
            Same(f"{at}host", node.host, STORAGE_HOST),
            Same(f"{at}status", node.status, "ready"),
            Same(f"{at}metadata.name", node.metadata.name, folder.name),
            Same(f"{at}metadata.cloneable", node.metadata.cloneable, False),
            Same(f"{at}metadata.last_used", node.metadata.last_used, None),
            Same(
                f"{at}access_control.ownership_type",
                node.access_control.ownership_type,
                folder.ownership_type.value,
            ),
            Held(
                f"{at}ownership.user_id",
                node.ownership.user_id,
                SameAs[UUID | None](folder.user, "폴더 주인"),
            ),
            Held(
                f"{at}ownership.project_id",
                node.ownership.project_id,
                SameAs[UUID | None](folder.group, "폴더가 놓인 프로젝트"),
            ),
            Held(
                f"{at}ownership.creator_id",
                node.ownership.creator_id,
                SameAs[UUID | None](folder.creator_id, "만든 사람"),
            ),
            Same(f"{at}ownership.creator_email", node.ownership.creator_email, folder.creator),
            Same(f"{at}unmanaged_path", node.unmanaged_path, None),
            Skipped(f"{at}metadata.usage_mode", "타입이 이미 값을 못박는다"),
            Skipped(f"{at}metadata.quota_scope_id", "주인의 id로 만들어져 실행마다 다르다"),
            Skipped(f"{at}access_control.permission", "마운트 권한이라 이 표가 묻는 것이 아니다"),
            Skipped(f"{at}quota", "저장소가 답하는 값이라 여기서 말할 수 없다"),
            Held(
                f"{at}metadata.created_at", node.metadata.created_at, WrittenByThisRun(self.started)
            ),
        ]


@dataclass(frozen=True)
class AUserReadsTheirOwnFolder(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-reads-their-own-folder"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더를 읽으면, "
            "그 폴더가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderIsReached(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheirOwnFolder(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-own-folder"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 자기 폴더를 읽으려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AProjectRoleListsTheProjectFolder(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-in-a-project-lists-its-folder"

    @override
    def describe(self) -> str:
        return (
            "프로젝트에서 폴더 읽기 권한을 받은 사용자가 그 프로젝트의 폴더를 조회하면, "
            "그 프로젝트의 폴더가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return AProjectFolderAndSomeone(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ListingTheProjectFolders()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderIsReached(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotListAProjectsFolders(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-list-a-projects-folders"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 프로젝트의 폴더를 조회하려 하면 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return AProjectFolderAndSomeone(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ListingTheProjectFolders()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnAcceptedShareReachesSomeoneElsesFolder(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-accepted-share-reads-someone-elses-folder"

    @override
    def describe(self) -> str:
        return "남의 폴더를 읽기로 공유받아 받아들인 사용자가 그 폴더를 읽으면, 그 폴더가 온다"

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderIsReached(started=self.started)


@dataclass(frozen=True)
class AnUnansweredOfferDoesNotReachTheFolder(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-unanswered-offer-may-not-read-someone-elses-folder"

    @override
    def describe(self) -> str:
        return (
            "남의 폴더를 공유 제안만 받고 받아들이지 않은 사용자가 그 폴더를 읽으려 하면 "
            "권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[ReachStep] = [
    AUserReadsTheirOwnFolder(started=STARTED),
    AUserGrantedNothingMayNotReadTheirOwnFolder(),
    AProjectRoleListsTheProjectFolder(started=STARTED),
    AUserGrantedNothingMayNotListAProjectsFolders(),
    AnAcceptedShareReachesSomeoneElsesFolder(started=STARTED),
    AnUnansweredOfferDoesNotReachTheFolder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reaching(
    scenario: ReachStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
