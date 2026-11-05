"""폴더 검색 — 전체 훑기, 내 범위 훑기, 걸러내기와 정렬."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

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
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
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
    ATwoFoldersAndPeople,
    SomeonesFolderAndTheSuperadmin,
    SomeoneWithAFolderOfTheirOwn,
    SomeoneWithTwoOwnFolders,
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
    TestSeedingSession, ATwoFoldersAndPeople, VFolderAdapter, SearchVFoldersPayload
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
class SearchingByName(When[ATwoFoldersAndPeople, VFolderAdapter, SearchVFoldersPayload]):
    """이름에 ``wanted``가 든 폴더만 훑는다."""

    wanted: str

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ATwoFoldersAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 자기 범위에서 이름에 {self.wanted}가 든 vfolder 를 "
            "조회합니다",
            english=(
                f"{laid.caller.username} searches their own scope for vfolders whose name "
                f"contains {self.wanted}"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: ATwoFoldersAndPeople
    ) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchVFoldersInput(
                    scope=VFolderScope(user=[UUIDScope(value=laid.caller.id)]),
                    filter=VFolderFilter(name=StringFilter(contains=self.wanted)),
                )
            )


@dataclass(frozen=True)
class OrderingByName(When[ATwoFoldersAndPeople, VFolderAdapter, SearchVFoldersPayload]):
    """이름으로 정렬해 훑는다."""

    direction: OrderDirection

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ATwoFoldersAndPeople) -> str:
        order_ko = "오름차순" if self.direction is OrderDirection.ASC else "내림차순"
        order_en = "ascending" if self.direction is OrderDirection.ASC else "descending"
        return Says(
            f"{laid.caller.username}이 자기 범위의 vfolder 를 이름 {order_ko}으로 정렬해 조회합니다",
            english=(f"{laid.caller.username} searches their own scope ordered by name {order_en}"),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: ATwoFoldersAndPeople
    ) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchVFoldersInput(
                    scope=VFolderScope(user=[UUIDScope(value=laid.caller.id)]),
                    order=[VFolderOrder(field=VFolderOrderField.NAME, direction=self.direction)],
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
class TheMatchingFolderAlone(Then[ATwoFoldersAndPeople, SearchVFoldersPayload]):
    """걸러낸 결과에 첫 폴더 하나만 실려 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "걸러낸 첫 vfolder 하나만 실린 페이지가 응답으로 옵니다",
            english="the page holding only the matching first vfolder comes back",
        )

    @override
    def look(
        self, laid: ATwoFoldersAndPeople, answered: Answered[SearchVFoldersPayload]
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
                VFolderNodeLook(self.started).verdicts(page.items[0], laid.first, at="items[0].")
            )
        return verdicts


@dataclass(frozen=True)
class BothFoldersInOrder(Then[ATwoFoldersAndPeople, SearchVFoldersPayload]):
    """두 폴더가 첫째, 둘째 순서로 실린 페이지가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "두 vfolder 가 첫째, 둘째 순서로 실린 페이지가 응답으로 옵니다",
            english=("the page holding the two vfolders with the first one first comes back"),
        )

    @override
    def look(
        self, laid: ATwoFoldersAndPeople, answered: Answered[SearchVFoldersPayload]
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
class ANameFilterLeavesOneFolder(
    Scenario[TestSeedingSession, ATwoFoldersAndPeople, VFolderAdapter, SearchVFoldersPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-name-filter-leaves-the-matching-folder"

    @override
    def describe(self) -> str:
        return Says(
            "이름에 어떤 글자가 든 폴더만 걸러 조회하면, 그 글자가 든 폴더 하나만 실린 페이지가 "
            "응답으로 옵니다",
            english=(
                "when a user searches their own scope filtered by a name fragment, the page "
                "holding only the matching folder comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATwoFoldersAndPeople]:
        return SomeoneWithTwoOwnFolders(permissions=(Permission.READ,))

    @override
    def when(self) -> When[ATwoFoldersAndPeople, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingByName(wanted="first")

    @override
    def then(self) -> Then[ATwoFoldersAndPeople, SearchVFoldersPayload]:
        return TheMatchingFolderAlone(started=self.started)


@dataclass(frozen=True)
class ANameOrderPutsTheFirstFolderFirst(
    Scenario[TestSeedingSession, ATwoFoldersAndPeople, VFolderAdapter, SearchVFoldersPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "ordering-by-name-ascending-puts-the-first-folder-first"

    @override
    def describe(self) -> str:
        return Says(
            "이름 오름차순으로 정렬해 조회하면, 이름이 앞서는 폴더가 먼저 실린 페이지가 "
            "응답으로 옵니다",
            english=(
                "when a user searches their own scope ordered by name ascending, the page "
                "holding the earlier name first comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ATwoFoldersAndPeople]:
        return SomeoneWithTwoOwnFolders(permissions=(Permission.READ,))

    @override
    def when(self) -> When[ATwoFoldersAndPeople, VFolderAdapter, SearchVFoldersPayload]:
        return OrderingByName(direction=OrderDirection.ASC)

    @override
    def then(self) -> Then[ATwoFoldersAndPeople, SearchVFoldersPayload]:
        return BothFoldersInOrder(started=self.started)


ADMIN: list[AdminStep] = [
    ASuperadminSearchesEveryFolder(started=datetime.now(UTC)),
    ARegularUserMayNotSearchEveryFolder(),
]

SCOPE: list[ScopeStep] = [
    AUserGrantedNothingMayNotSearchTheirScope(),
]

PAIRS: list[PairStep] = [
    ANameFilterLeavesOneFolder(started=datetime.now(UTC)),
    ANameOrderPutsTheFirstFolderFirst(started=datetime.now(UTC)),
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
