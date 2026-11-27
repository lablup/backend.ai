"""사용자와 폴더의 쌍 검색 — 마운트 레벨로 걸러내기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.vfolder.request import (
    ScopedSearchUserVFolderMountsInput,
    UserVFolderMountFilter,
    UserVFolderMountOrder,
    VFolderFilter,
)
from ai.backend.common.dto.manager.v2.vfolder.response import SearchUserVFolderMountsPayload
from ai.backend.common.dto.manager.v2.vfolder.types import (
    OrderDirection,
    UserVFolderMountScope,
    VFolderMountPermissionFilter,
    VFolderOrderField,
    VFolderPermissionField,
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
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder import AReaderAndFoldersToMount, SomeoneWithFoldersToMount
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type UserVFolderMountStep = Scenario[
    TestSeedingSession, AReaderAndFoldersToMount, VFolderAdapter, SearchUserVFolderMountsPayload
]


@dataclass(frozen=True)
class SearchingFoldersTheUserMountsReadWrite(
    When[AReaderAndFoldersToMount, VFolderAdapter, SearchUserVFolderMountsPayload]
):
    """자기가 rw로 마운트하는 폴더를 이름 조각으로 걸러 이름 오름차순으로, 크기만큼만 훑는다."""

    fragment: str
    limit: int

    @override
    def operation(self) -> str:
        return "scoped_search_user_vfolder_mounts"

    @override
    def describe(self, laid: AReaderAndFoldersToMount) -> str:
        return Says(
            f"{laid.caller.username}이 자기 범위와 다른 사용자의 개인 프로젝트에서 자기가 rw로 "
            f"마운트하고 이름에 {self.fragment}가 든 vfolder 를 이름 오름차순으로 "
            f"{self.limit}개까지 조회합니다",
            english=(
                f"{laid.caller.username} searches their own scope and another user's personal "
                f"project for vfolders they mount as rw whose name holds {self.fragment}, ordered "
                f"by name ascending, up to {self.limit}"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AReaderAndFoldersToMount
    ) -> SearchUserVFolderMountsPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search_user_vfolder_mounts(
                ScopedSearchUserVFolderMountsInput(
                    scope=UserVFolderMountScope(
                        user=[UUIDScope(value=laid.caller.id)],
                        project=[UUIDScope(value=laid.other_project_id)],
                    ),
                    filter=UserVFolderMountFilter(
                        mount_permission=VFolderMountPermissionFilter(
                            equals=VFolderPermissionField.READ_WRITE
                        ),
                        vfolder=VFolderFilter(name=StringFilter(contains=self.fragment)),
                    ),
                    order=[
                        UserVFolderMountOrder(
                            field=VFolderOrderField.NAME, direction=OrderDirection.ASC
                        )
                    ],
                    limit=self.limit,
                )
            )


@dataclass(frozen=True)
class TheUserAndTheFoldersTheyMountReadWrite(
    Then[AReaderAndFoldersToMount, SearchUserVFolderMountsPayload]
):
    """rw로 마운트하는 자기 폴더 둘과의 쌍만 이름 순서로 실린 한 페이지가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "자기가 rw로 마운트하는 vfolder 둘과의 쌍만 이름 순서로 실린 한 페이지가 응답으로 옵니다",
            english=(
                "one page holding only the pairs with the two vfolders they mount as rw, in name "
                "order, comes back"
            ),
        )

    @override
    def look(
        self, laid: AReaderAndFoldersToMount, answered: Answered[SearchUserVFolderMountsPayload]
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
            verdicts.extend([
                Held(
                    f"items[{at}].id",
                    node.id,
                    SameAs[str](
                        f"{laid.caller.id}:{folder.id}",
                        Says("사용자 id 와 vfolder id", english="the user id and the vfolder id"),
                    ),
                ),
                Held(
                    f"items[{at}].user_id",
                    node.user_id,
                    SameAs[UUID](laid.caller.id, Says("조회한 사용자", english="the caller")),
                ),
                Held(
                    f"items[{at}].vfolder_id",
                    node.vfolder_id,
                    SameAs[UUID](
                        folder.id,
                        Says("미리 저장한 vfolder", english="the vfolder seeded in advance"),
                    ),
                ),
                Same(f"items[{at}].mount_permission", node.mount_permission.value, "rw"),
            ])
        return verdicts


@dataclass(frozen=True)
class AUserSearchesTheFoldersTheyMountReadWrite(
    Scenario[
        TestSeedingSession, AReaderAndFoldersToMount, VFolderAdapter, SearchUserVFolderMountsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-searches-the-folders-they-mount-read-write"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프와 다른 사용자의 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기가 "
            "rw로 마운트하는 vfolder 를 이름 조각으로 걸러 이름 오름차순으로 한 페이지를 조회하면, "
            "남에게는 ro로 마운트되는 자기 vfolder 둘과의 쌍만 이름 순서로 실린 한 페이지가 응답으로 "
            "옵니다",
            english=(
                "when a user granted vfolder read in their own scope and another user's personal "
                "project searches the vfolders they mount as rw by a name fragment, ordered by "
                "name ascending and limited to one page, one page holding only the pairs with "
                "their own two vfolders, mounted for others as ro, in name order comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AReaderAndFoldersToMount]:
        return SomeoneWithFoldersToMount(granted=True, fragment="match")

    @override
    def when(
        self,
    ) -> When[AReaderAndFoldersToMount, VFolderAdapter, SearchUserVFolderMountsPayload]:
        return SearchingFoldersTheUserMountsReadWrite(fragment="match", limit=2)

    @override
    def then(self) -> Then[AReaderAndFoldersToMount, SearchUserVFolderMountsPayload]:
        return TheUserAndTheFoldersTheyMountReadWrite()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheFoldersTheyMount(
    Scenario[
        TestSeedingSession, AReaderAndFoldersToMount, VFolderAdapter, SearchUserVFolderMountsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-the-folders-they-mount"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 범위와 다른 사용자의 개인 프로젝트에서 자기가 rw로 "
            "마운트하는 vfolder 를 조회하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to search their own scope and another user's "
                "personal project for vfolders they mount as rw, it is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AReaderAndFoldersToMount]:
        return SomeoneWithFoldersToMount(granted=False, fragment="match")

    @override
    def when(
        self,
    ) -> When[AReaderAndFoldersToMount, VFolderAdapter, SearchUserVFolderMountsPayload]:
        return SearchingFoldersTheUserMountsReadWrite(fragment="match", limit=2)

    @override
    def then(self) -> Then[AReaderAndFoldersToMount, SearchUserVFolderMountsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[UserVFolderMountStep] = [
    AUserSearchesTheFoldersTheyMountReadWrite(),
    AUserGrantedNothingMayNotSearchTheFoldersTheyMount(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_user_vfolder_mounts(
    scenario: UserVFolderMountStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
