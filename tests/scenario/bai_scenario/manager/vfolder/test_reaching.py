"""누구의 폴더에 닿는가: 자기 폴더, 프로젝트 폴더, 공유받은 폴더."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
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
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder import (
    AFolderAndItsReader,
    AFolderOfferedToSomeone,
    AProjectFolderAndSomeone,
    SomeoneWithAFolderOfTheirOwn,
    VFolderNodeLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = VFolderNode | SearchVFoldersPayload
type ReachStep = Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]


@dataclass(frozen=True)
class ReadingTheFolder(When[AFolderAndItsReader, VFolderAdapter, Answer]):
    """폴더 하나를 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 를 조회합니다",
            english=f"{laid.caller.username} reads the {laid.folder.name} vfolder",
        )

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
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 가 놓인 프로젝트의 vfolder 를 "
            "조회합니다",
            english=(
                f"{laid.caller.username} lists the vfolders of the project the "
                f"{laid.folder.name} vfolder is placed in"
            ),
        )

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
        return Says(
            "미리 저장한 vfolder 전체가 응답으로 옵니다",
            english="the whole vfolder seeded in advance comes back",
        )

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[Answer]) -> list[Verdict]:
        answer = answered.response
        if isinstance(answer, VFolderNode):
            return VFolderNodeLook(self.started).verdicts(answer, laid.folder)
        if isinstance(answer, SearchVFoldersPayload):
            page: list[Verdict] = [
                Same("total_count", answer.total_count, 1),
                Same("has_next_page", answer.has_next_page, False),
                Same("has_previous_page", answer.has_previous_page, False),
                Same("items.length", len(answer.items), 1),
            ]
            if answer.items:
                page.extend(
                    VFolderNodeLook(self.started).verdicts(
                        answer.items[0], laid.folder, at="items[0]."
                    )
                )
            return page
        raised = type(answered.raised).__name__ if answered.raised is not None else None
        return [Same("answer", raised, "VFolderNode")]


@dataclass(frozen=True)
class AUserReadsTheirOwnFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-reads-their-own-folder"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 조회하면, "
            "그 vfolder 가 응답으로 옵니다",
            english=(
                "when a user granted vfolder read in their personal project reads their own "
                "vfolder, that vfolder comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderIsReached(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheirOwnFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-own-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to read their own vfolder, it is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AProjectRoleListsTheProjectFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-in-a-project-lists-its-folder"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 vfolder 읽기 권한을 받은 사용자가 그 프로젝트의 vfolder 를 조회하면, "
            "그 프로젝트의 vfolder 가 응답으로 옵니다",
            english=(
                "when a user granted vfolder read in a project lists the vfolders of that "
                "project, the vfolders of that project come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return AProjectFolderAndSomeone(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ListingTheProjectFolders()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderIsReached(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotListAProjectsFolders(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-list-a-projects-folders"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프로젝트의 vfolder 를 조회하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to list the vfolders of a project, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return AProjectFolderAndSomeone(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ListingTheProjectFolders()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnAcceptedShareReachesSomeoneElsesFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-accepted-share-reads-someone-elses-folder"

    @override
    def describe(self) -> str:
        return Says(
            "다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 조회하면, "
            "그 vfolder 가 응답으로 옵니다",
            english=(
                "when a user who accepted a read share of someone else's vfolder reads it, "
                "that vfolder comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return ReadingTheFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderIsReached(started=self.started)


@dataclass(frozen=True)
class AnUnansweredOfferDoesNotReachTheFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-unanswered-offer-may-not-read-someone-elses-folder"

    @override
    def describe(self) -> str:
        return Says(
            "다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 "
            "조회하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user who was offered someone else's vfolder but did not accept tries "
                "to read it, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
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
