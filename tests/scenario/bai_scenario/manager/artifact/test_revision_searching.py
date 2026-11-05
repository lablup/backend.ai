"""리비전 검색: 전체, 상태로 좁혀서, 아티팩트 하나의 리비전만, 권한 없이."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactRevisionsInput,
    ArtifactRevisionGQLFilterInputDTO,
    ArtifactRevisionStatusFilterDTO,
)
from ai.backend.common.dto.manager.v2.artifact.response import (
    AdminSearchArtifactRevisionsPayload,
)
from ai.backend.common.dto.manager.v2.artifact.types import ArtifactStatus
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.data.artifact.types import ArtifactStatus as DataStatus
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.artifact import (
    ManyArtifactsWithRevisionsAndACaller,
    ManyArtifactsWithRevisionsAndSomeone,
    TheRevisionPage,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchStep = Scenario[
    TestSeedingSession,
    ManyArtifactsWithRevisionsAndACaller,
    ArtifactAdapter,
    AdminSearchArtifactRevisionsPayload,
]


@dataclass(frozen=True)
class SearchingRevisions(
    When[ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, AdminSearchArtifactRevisionsPayload]
):
    status: ArtifactStatus | None = None

    @override
    def operation(self) -> str:
        return "search_revisions_gql"

    @override
    def describe(self, laid: ManyArtifactsWithRevisionsAndACaller) -> str:
        who = laid.caller.username
        if self.status is None:
            return Says(
                f"{who}이 조건 없이 검색합니다",
                english=f"{who} searches with no condition",
            )
        return Says(
            f"{who}이 {self.status.value} 상태로 좁혀 검색합니다",
            english=f"{who} searches narrowed to the {self.status.value} status",
        )

    def revision_filter(self) -> ArtifactRevisionGQLFilterInputDTO | None:
        if self.status is None:
            return None
        return ArtifactRevisionGQLFilterInputDTO(
            status=ArtifactRevisionStatusFilterDTO(in_=[self.status])
        )

    @override
    async def call(
        self,
        adapter: ArtifactAdapter,
        laid: ManyArtifactsWithRevisionsAndACaller,
    ) -> AdminSearchArtifactRevisionsPayload:
        with ActingAs(laid.caller):
            return await adapter.search_revisions_gql(
                AdminSearchArtifactRevisionsInput(filter=self.revision_filter())
            )


@dataclass(frozen=True)
class SearchingOneArtifactsRevisions(
    When[ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, AdminSearchArtifactRevisionsPayload]
):
    """미리 저장한 아티팩트 중 하나가 가진 리비전만 검색한다."""

    @override
    def operation(self) -> str:
        return "search_revisions_of_artifact_gql"

    @override
    def describe(self, laid: ManyArtifactsWithRevisionsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.laid[0].artifact.name}이 가진 리비전을 검색합니다",
            english=(
                f"{laid.caller.username} searches the revisions {laid.laid[0].artifact.name} holds"
            ),
        )

    @override
    async def call(
        self,
        adapter: ArtifactAdapter,
        laid: ManyArtifactsWithRevisionsAndACaller,
    ) -> AdminSearchArtifactRevisionsPayload:
        with ActingAs(laid.caller):
            return await adapter.search_revisions_of_artifact_gql(
                laid.laid[0].artifact.id, AdminSearchArtifactRevisionsInput()
            )


@dataclass(frozen=True)
class SearchingRevisionsWithoutAConditionReturnsEvery(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        AdminSearchArtifactRevisionsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "searching-revisions-without-a-condition-returns-every"

    @override
    def describe(self) -> str:
        return Says(
            "읽기만 하는 monitor 가 리비전을 조건 없이 검색하면, 미리 저장한 리비전이 모두 한 "
            "페이지로 옵니다",
            english=(
                "when the read-only monitor searches revisions with no condition, every revision "
                "made in advance comes back on one page"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(role=UserRole.MONITOR)

    @override
    def when(
        self,
    ) -> When[
        ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, AdminSearchArtifactRevisionsPayload
    ]:
        return SearchingRevisions()

    @override
    def then(
        self,
    ) -> Then[ManyArtifactsWithRevisionsAndACaller, AdminSearchArtifactRevisionsPayload]:
        return TheRevisionPage()


@dataclass(frozen=True)
class FilteringByStatusLeavesThatStatus(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        AdminSearchArtifactRevisionsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "filtering-revisions-by-status-leaves-only-that-status"

    @override
    def describe(self) -> str:
        return Says(
            "읽기만 하는 monitor 가 승인 대기 상태로 좁혀 검색하면, 그 상태의 리비전만 남습니다",
            english=(
                "when the read-only monitor searches revisions narrowed to the needs-approval "
                "status, only revisions in that status remain"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(role=UserRole.MONITOR)

    @override
    def when(
        self,
    ) -> When[
        ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, AdminSearchArtifactRevisionsPayload
    ]:
        return SearchingRevisions(status=ArtifactStatus.NEEDS_APPROVAL)

    @override
    def then(
        self,
    ) -> Then[ManyArtifactsWithRevisionsAndACaller, AdminSearchArtifactRevisionsPayload]:
        return TheRevisionPage(only_status=DataStatus.NEEDS_APPROVAL)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchRevisions(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        AdminSearchArtifactRevisionsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-revisions"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 리비전을 검색하려 하면, 전역 역할이 없어 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to search revisions, it is rejected for lack "
                "of permission because they hold no global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(role=UserRole.USER)

    @override
    def when(
        self,
    ) -> When[
        ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, AdminSearchArtifactRevisionsPayload
    ]:
        return SearchingRevisions()

    @override
    def then(
        self,
    ) -> Then[ManyArtifactsWithRevisionsAndACaller, AdminSearchArtifactRevisionsPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class OneArtifactsRevisionsAreReturned(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        AdminSearchArtifactRevisionsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "searching-one-artifacts-revisions-returns-only-the-ones-it-holds"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 읽기 권한을 받은 사용자가 아티팩트 하나의 리비전을 검색하면, "
            "그 아티팩트가 가진 리비전만 한 페이지로 옵니다",
            english=(
                "when a user granted read permission on artifacts in global searches the "
                "revisions of one artifact, only the revisions that artifact holds come back "
                "on one page"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[
        ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, AdminSearchArtifactRevisionsPayload
    ]:
        return SearchingOneArtifactsRevisions()

    @override
    def then(
        self,
    ) -> Then[ManyArtifactsWithRevisionsAndACaller, AdminSearchArtifactRevisionsPayload]:
        return TheRevisionPage(only_artifact_index=0)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchOneArtifactsRevisions(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        AdminSearchArtifactRevisionsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-one-artifacts-revisions"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 아티팩트 하나의 리비전을 검색하려 하면, 그 아티팩트에 "
            "대한 권한이 없어 요청 전체가 거부됩니다",
            english=(
                "when a user granted nothing tries to search the revisions of one artifact, the "
                "whole request is rejected because they hold no permission on that artifact"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(role=UserRole.USER)

    @override
    def when(
        self,
    ) -> When[
        ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, AdminSearchArtifactRevisionsPayload
    ]:
        return SearchingOneArtifactsRevisions()

    @override
    def then(
        self,
    ) -> Then[ManyArtifactsWithRevisionsAndACaller, AdminSearchArtifactRevisionsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchStep] = [
    SearchingRevisionsWithoutAConditionReturnsEvery(),
    FilteringByStatusLeavesThatStatus(),
    AUserGrantedNothingMayNotSearchRevisions(),
    OneArtifactsRevisionsAreReturned(),
    AUserGrantedNothingMayNotSearchOneArtifactsRevisions(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_revision_searching(
    scenario: SearchStep,
    adapter: ArtifactAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
