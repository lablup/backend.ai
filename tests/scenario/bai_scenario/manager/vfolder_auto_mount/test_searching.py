"""프로젝트 범위에서 자동 마운트 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    ScopedSearchVFolderAutoMountsInput,
    VFolderAutoMountFilter,
    VFolderAutoMountOrder,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import (
    SearchVFolderAutoMountsPayload,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.types import (
    VFolderAutoMountOrderField,
    VFolderAutoMountScope,
)
from ai.backend.manager.api.adapters.vfolder_auto_mount.adapter import VFolderAutoMountAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.vfolder_auto_mount import (
    AProjectAndAutoMountsToSearch,
    AProjectFolderAndAutoMounts,
    AProjectFolderAndSomeone,
    AProjectWithAutoMountsToSearch,
    TheMatchingAutoMountsInOrder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchingStep = Scenario[
    TestSeedingSession,
    Any,
    VFolderAutoMountAdapter,
    SearchVFolderAutoMountsPayload,
]


@dataclass(frozen=True)
class ListingTheProjectAutoMounts(
    When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, SearchVFolderAutoMountsPayload]
):
    """그 프로젝트 범위의 자동 마운트를 훑는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AProjectFolderAndAutoMounts) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트 범위의 자동 마운트를 "
            "조회합니다",
            english=(
                f"{laid.caller.username} lists the auto-mounts of the {laid.project.name} project"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAutoMountAdapter, laid: AProjectFolderAndAutoMounts
    ) -> SearchVFolderAutoMountsPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchVFolderAutoMountsInput(
                    scope=VFolderAutoMountScope(project=[UUIDScope(value=laid.project.id)])
                )
            )


@dataclass(frozen=True)
class ListingByDestinationInOrder(
    When[AProjectAndAutoMountsToSearch, VFolderAutoMountAdapter, SearchVFolderAutoMountsPayload]
):
    """주소 조각으로 걸러 주소 오름차순으로, 크기만큼만 훑는다."""

    fragment: str
    limit: int

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AProjectAndAutoMountsToSearch) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트 범위의 자동 마운트를 주소에 "
            f"{self.fragment}가 든 것만 주소 오름차순으로 {self.limit}개까지 조회합니다",
            english=(
                f"{laid.caller.username} lists up to {self.limit} auto-mounts of the "
                f"{laid.project.name} project whose destination holds {self.fragment}, ordered "
                "by destination"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAutoMountAdapter, laid: AProjectAndAutoMountsToSearch
    ) -> SearchVFolderAutoMountsPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchVFolderAutoMountsInput(
                    scope=VFolderAutoMountScope(project=[UUIDScope(value=laid.project.id)]),
                    filter=VFolderAutoMountFilter(
                        mount_destination=StringFilter(contains=self.fragment)
                    ),
                    order=[
                        VFolderAutoMountOrder(
                            field=VFolderAutoMountOrderField.MOUNT_DESTINATION,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=self.limit,
                )
            )


@dataclass(frozen=True)
class AGrantedUserListsTheProjectAutoMounts(
    Scenario[
        TestSeedingSession,
        AProjectAndAutoMountsToSearch,
        VFolderAutoMountAdapter,
        SearchVFolderAutoMountsPayload,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-auto-mount-read-lists-the-project-auto-mounts"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트 범위에서 자동 마운트 읽기 권한을 받은 사용자가 주소 조각으로 걸러 주소 "
            "오름차순으로 한 페이지를 조회하면, 걸러진 자동 마운트 둘만 주소 순서로 실린 한 "
            "페이지가 응답으로 옵니다",
            english=(
                "when a user granted auto-mount read in a project searches by a destination "
                "fragment, ordered by destination and limited to one page, one page holding only "
                "the two matching auto-mounts in destination order comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAndAutoMountsToSearch]:
        return AProjectWithAutoMountsToSearch(fragment="match")

    @override
    def when(
        self,
    ) -> When[
        AProjectAndAutoMountsToSearch, VFolderAutoMountAdapter, SearchVFolderAutoMountsPayload
    ]:
        return ListingByDestinationInOrder(fragment="match", limit=2)

    @override
    def then(
        self,
    ) -> Then[AProjectAndAutoMountsToSearch, SearchVFolderAutoMountsPayload]:
        return TheMatchingAutoMountsInOrder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotListTheProjectAutoMounts(
    Scenario[
        TestSeedingSession,
        AProjectFolderAndAutoMounts,
        VFolderAutoMountAdapter,
        SearchVFolderAutoMountsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-list-project-auto-mounts"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프로젝트의 자동 마운트를 조회하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to list the auto-mounts of a project, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(mounted=True)

    @override
    def when(
        self,
    ) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, SearchVFolderAutoMountsPayload]:
        return ListingTheProjectAutoMounts()

    @override
    def then(
        self,
    ) -> Then[AProjectFolderAndAutoMounts, SearchVFolderAutoMountsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedReadButNoAutoMountListsNone(
    Scenario[
        TestSeedingSession,
        AProjectFolderAndAutoMounts,
        VFolderAutoMountAdapter,
        SearchVFolderAutoMountsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-project-with-no-auto-mount-answers-an-empty-page"

    @override
    def describe(self) -> str:
        return Says(
            "자동 마운트가 하나도 등록되지 않은 프로젝트의 자동 마운트를 조회하면, 응답은 "
            "비어 있습니다",
            english=(
                "when a user lists the auto-mounts of a project that has none, the answer is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectFolderAndAutoMounts]:
        return AProjectFolderAndSomeone(permissions=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[AProjectFolderAndAutoMounts, VFolderAutoMountAdapter, SearchVFolderAutoMountsPayload]:
        return ListingTheProjectAutoMounts()

    @override
    def then(
        self,
    ) -> Then[AProjectFolderAndAutoMounts, SearchVFolderAutoMountsPayload]:
        return NothingIsFound()


SCENARIOS: list[SearchingStep] = [
    AGrantedUserListsTheProjectAutoMounts(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotListTheProjectAutoMounts(),
    AUserGrantedReadButNoAutoMountListsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: VFolderAutoMountAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
