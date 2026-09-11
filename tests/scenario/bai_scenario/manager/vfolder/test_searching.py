"""내 폴더 검색 — 자기 것만 오는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.vfolder.answers import (
    NoAnswer,
    OnlyTheirsIsFound,
)
from bai_scenario.components.vfolder.callers import (
    SomeoneGrantedNothing,
    SomeoneGrantedOverThemselves,
    TheirFoldersAndANeighbours,
)
from bai_scenario.components.vfolder.stage import (
    READING,
    AFolderMakerAndTheirDomain,
    FoldersAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SearchVFoldersPayload,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

ENFORCEMENT = "manager.rbac.enforcement_enabled"

type SearchingStep = Scenario[SeedingSession, Any, VFolderAdapter, SearchVFoldersPayload]


@dataclass(frozen=True)
class SearchingTheirOwn(When[Any, VFolderAdapter, SearchVFoldersPayload]):
    """자기 폴더를 훑는다. 페이지 크기를 대지 않으면 공용 도우미의 기본값으로 끊긴다."""

    @override
    def operation(self) -> str:
        return "my_search"

    @override
    def describe(self, laid: Any) -> str:
        return f"{laid.caller.username}이 자기 폴더를 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: Any) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.my_search(SearchVFoldersInput())


@dataclass(frozen=True)
class OnePageOfThem(Then[FoldersAndACaller, Any]):
    """페이지 하나만큼 오고, 다음 페이지가 있다고 답한다."""

    fits: int

    @override
    def says(self) -> str:
        return f"{self.fits}건까지 오고, 다음 페이지가 있다고 답한다"

    @override
    def look(self, laid: FoldersAndACaller, answered: Answered[Any]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, SearchVFoldersPayload):
            return [NoAnswer(answered.raised)]
        return [
            Same("items", len(page.items), self.fits),
            Same("total_count", page.total_count, len(laid.seen)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheirOwnFoldersComeBack(
    Scenario[SeedingSession, FoldersAndACaller, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "searching-my-own-folders-answers-only-mine"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에 읽기 권한을 받은 사용자가 자기 폴더를 조회하면, "
            "같은 도메인에 있는 남의 폴더는 빼고 자기 것만 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, FoldersAndACaller]:
        return TheirFoldersAndANeighbours(own=2, others=1)

    @override
    def when(self) -> When[FoldersAndACaller, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingTheirOwn()

    @override
    def then(self) -> Then[FoldersAndACaller, SearchVFoldersPayload]:
        return OnlyTheirsIsFound(counted=2)


@dataclass(frozen=True)
class AUserWhoMadeNoFolderFindsNone(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-has-made-no-folder-finds-none"

    @override
    def describe(self) -> str:
        return "폴더를 하나도 만들지 않은 사용자가 자기 폴더를 조회하면, 답은 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedOverThemselves(permissions=READING)

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingTheirOwn()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, SearchVFoldersPayload]:
        return NothingIsFound()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheirOwn(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-even-their-own-folders"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에 아무 권한도 받지 않은 사용자가 자기 폴더를 조회하려 하면, "
            "범위를 좁히는 것으로 끝나지 않고 그 스코프에 걸린 권한이 막아 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedNothing()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingTheirOwn()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, SearchVFoldersPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class LeavingThePageSizeOutTakesTheDefault(
    Scenario[SeedingSession, FoldersAndACaller, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "leaving-the-page-size-out-answers-one-default-page"

    @override
    def describe(self) -> str:
        return (
            "폴더를 열한 개 가진 사용자가 페이지 크기를 대지 않고 조회하면, "
            "기본 크기만큼만 오고 다음 페이지가 있다고 답한다"
        )

    @override
    def given(self) -> Given[SeedingSession, FoldersAndACaller]:
        return TheirFoldersAndANeighbours(own=11, others=0)

    @override
    def when(self) -> When[FoldersAndACaller, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingTheirOwn()

    @override
    def then(self) -> Then[FoldersAndACaller, SearchVFoldersPayload]:
        return OnePageOfThem(fits=10)


SCENARIOS: list[SearchingStep] = [
    TheirOwnFoldersComeBack(),
    AUserWhoMadeNoFolderFindsNone(),
    AUserGrantedNothingMayNotSearchTheirOwn(),
    LeavingThePageSizeOutTakesTheDefault(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
