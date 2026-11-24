"""폴더 검색 — 전체 훑기, 내 범위 훑기, 걸러내기와 정렬."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.vfolder.request import (
    ScopedSearchVFoldersInput,
    SearchVFoldersInput,
    VFolderFilter,
    VFolderOrder,
)
from ai.backend.common.dto.manager.v2.vfolder.response import SearchVFoldersPayload
from ai.backend.common.dto.manager.v2.vfolder.types import (
    OrderDirection,
    VFolderOrderField,
    VFolderScope,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
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
    AReaderAndFoldersToSearch,
    SomeonesFolderAndTheSuperadmin,
    SomeoneWithAFolderOfTheirOwn,
    SomeoneWithFoldersToSearch,
    VFolderNodeLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type AdminStep = Scenario[
    TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload
]
type ScopeStep = Scenario[
    TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload
]
type PairStep = Scenario[
    TestSeedingSession, AReaderAndFoldersToSearch, VFolderAdapter, SearchVFoldersPayload
]


@dataclass(frozen=True)
class SearchingEveryFolder(When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]):
    """아무 필터 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 필터 없이 모든 vfolder 를 조회합니다",
            english=f"{laid.caller.username} searches every vfolder without a filter",
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndItsReader
    ) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchVFoldersInput())


@dataclass(frozen=True)
class SearchingMyOwnScope(When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]):
    """자기 사용자 범위를 훑는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 자기 범위의 vfolder 를 조회합니다",
            english=f"{laid.caller.username} searches the vfolders of their own scope",
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndItsReader
    ) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchVFoldersInput(
                    scope=VFolderScope(user=[UUIDScope(value=laid.caller.id)])
                )
            )


@dataclass(frozen=True)
class SearchingByFragmentInOrder(
    When[AReaderAndFoldersToSearch, VFolderAdapter, SearchVFoldersPayload]
):
    """이름 조각으로 걸러 이름 오름차순으로, 크기만큼만 훑는다."""

    fragment: str
    limit: int

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AReaderAndFoldersToSearch) -> str:
        return Says(
            f"{laid.caller.username}이 자기 범위에서 이름에 {self.fragment}가 든 vfolder 를 "
            f"이름 오름차순으로 {self.limit}개까지 조회합니다",
            english=(
                f"{laid.caller.username} searches their own scope for vfolders whose name holds "
                f"{self.fragment}, ordered by name ascending, up to {self.limit}"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AReaderAndFoldersToSearch
    ) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchVFoldersInput(
                    scope=VFolderScope(user=[UUIDScope(value=laid.caller.id)]),
                    filter=VFolderFilter(name=StringFilter(contains=self.fragment)),
                    order=[
                        VFolderOrder(field=VFolderOrderField.NAME, direction=OrderDirection.ASC)
                    ],
                    limit=self.limit,
                )
            )


@dataclass(frozen=True)
class TheSeededFolderAlone(Then[AFolderAndItsReader, SearchVFoldersPayload]):
    """심은 폴더 하나만 실린 페이지가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 vfolder 하나만 실린 페이지가 응답으로 옵니다",
            english="the page holding only the vfolder seeded in advance comes back",
        )

    @override
    def look(
        self, laid: AFolderAndItsReader, answered: Answered[SearchVFoldersPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 1),
        ]
        if page.items:
            verdicts.extend(
                VFolderNodeLook(self.started).verdicts(page.items[0], laid.folder, at="items[0].")
            )
        return verdicts


@dataclass(frozen=True)
class TheseFolders(Condition[Collection[UUID]]):
    """답에 든 폴더가 정해진 폴더들과 같다. id 는 실행마다 달라 무엇인지로 말한다."""

    wanted: frozenset[UUID]
    named: Says

    @override
    def says(self) -> str:
        return self.named

    @override
    def holds(self, got: Collection[UUID]) -> bool:
        return len(got) == len(self.wanted) and frozenset(got) == self.wanted


@dataclass(frozen=True)
class TheMatchingFoldersInOrder(Then[AReaderAndFoldersToSearch, SearchVFoldersPayload]):
    """걸러진 자기 폴더 둘만 이름 순서로 실린 한 페이지가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "걸러진 자기 vfolder 둘만 이름 순서로 실린 한 페이지가 응답으로 옵니다",
            english=("one page holding only their two matching vfolders in name order comes back"),
        )

    @override
    def look(
        self, laid: AReaderAndFoldersToSearch, answered: Answered[SearchVFoldersPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, 2),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 2),
        ]
        if len(page.items) != 2:
            return verdicts
        for at, (node, folder) in enumerate(
            zip(page.items, (laid.first, laid.second), strict=True)
        ):
            verdicts.extend(
                VFolderNodeLook(self.started).verdicts(node, folder, at=f"items[{at}].")
            )
        verdicts.append(
            Held(
                "items ids",
                [node.id for node in page.items],
                TheseFolders(
                    frozenset({laid.first.id, laid.second.id}),
                    Says("걸러진 자기 vfolder 둘", english="their two matching vfolders"),
                ),
            )
        )
        return verdicts


@dataclass(frozen=True)
class ASuperadminSearchesEveryFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-superadmin-searches-every-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 역할도 받지 않은 superadmin 이 모든 vfolder 를 조회하면, 심은 vfolder 가 "
            "응답으로 옵니다",
            english=(
                "when a superadmin holding no role searches every vfolder, the vfolder seeded in "
                "advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeonesFolderAndTheSuperadmin()

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingEveryFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, SearchVFoldersPayload]:
        return TheSeededFolderAlone(started=self.started)


@dataclass(frozen=True)
class ARegularUserMayNotSearchEveryFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-regular-user-may-not-search-every-folder"

    @override
    def describe(self) -> str:
        return Says(
            "일반 사용자가 모든 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a regular user tries to search every vfolder, it is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingEveryFolder()

    @override
    def then(self) -> Then[AFolderAndItsReader, SearchVFoldersPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheirScope(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-their-own-scope"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 범위의 vfolder 를 조회하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to search the vfolders of their own scope, "
                "it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingMyOwnScope()

    @override
    def then(self) -> Then[AFolderAndItsReader, SearchVFoldersPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ASearchNarrowsOrdersAndPages(
    Scenario[TestSeedingSession, AReaderAndFoldersToSearch, VFolderAdapter, SearchVFoldersPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-search-narrows-to-the-matching-folder-in-order-and-page"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프에서 vfolder 읽기 권한을 받은 사용자가 이름 조각으로 걸러 이름 오름차순으로 "
            "한 페이지를 조회하면, 걸러진 자기 vfolder 둘만 이름 순서로 실린 한 페이지가 응답으로 "
            "옵니다",
            english=(
                "when a user granted vfolder read in their own scope searches by a name fragment, "
                "ordered by name ascending and limited to one page, one page holding only their "
                "two matching vfolders in name order comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AReaderAndFoldersToSearch]:
        return SomeoneWithFoldersToSearch(fragment="match")

    @override
    def when(self) -> When[AReaderAndFoldersToSearch, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingByFragmentInOrder(fragment="match", limit=2)

    @override
    def then(self) -> Then[AReaderAndFoldersToSearch, SearchVFoldersPayload]:
        return TheMatchingFoldersInOrder(started=self.started)


ADMIN: list[AdminStep] = [
    ASuperadminSearchesEveryFolder(started=datetime.now(UTC)),
    ARegularUserMayNotSearchEveryFolder(),
]

SCOPE: list[ScopeStep] = [
    AUserGrantedNothingMayNotSearchTheirScope(),
]

PAIRS: list[PairStep] = [
    ASearchNarrowsOrdersAndPages(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", ADMIN, ids=lambda s: s.summary())
async def test_admin_searching(
    scenario: AdminStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", SCOPE, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: ScopeStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", PAIRS, ids=lambda s: s.summary())
async def test_pair_searching(
    scenario: PairStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
