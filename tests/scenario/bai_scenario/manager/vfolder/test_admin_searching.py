"""전체 검색 — 권한이 아니라 역할이 지키는 자리."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder.answers import (
    OnlyTheirsIsFound,
)
from bai_scenario.components.vfolder.callers import (
    FoldersOfTwoOthers,
    SomeoneGrantedNothing,
    SomeoneGrantedOverThemselves,
)
from bai_scenario.components.vfolder.stage import (
    READING,
    AFolderMakerAndTheirDomain,
    FoldersAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SearchVFoldersPayload,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

ENFORCEMENT = "manager.rbac.enforcement_enabled"

type SearchingStep = Scenario[SeedingSession, Any, VFolderAdapter, SearchVFoldersPayload]


@dataclass(frozen=True)
class SearchingEverything(When[Any, VFolderAdapter, SearchVFoldersPayload]):
    """주인을 가리지 않고 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: Any) -> str:
        return f"{laid.caller.username}이 전체를 조회"

    @override
    async def call(self, adapter: VFolderAdapter, laid: Any) -> SearchVFoldersPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchVFoldersInput())


@dataclass(frozen=True)
class TheSuperadminSeesEveryFolder(
    Scenario[SeedingSession, FoldersAndACaller, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searches-across-every-owner"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 전체를 조회하면, 주인이 서로 다른 폴더가 모두 답으로 온다. "
            "이 조회는 권한이 아니라 역할이 지킨다"
        )

    @override
    def given(self) -> Given[SeedingSession, FoldersAndACaller]:
        return FoldersOfTwoOthers(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[FoldersAndACaller, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingEverything()

    @override
    def then(self) -> Then[FoldersAndACaller, SearchVFoldersPayload]:
        return OnlyTheirsIsFound(counted=2)


@dataclass(frozen=True)
class TheMonitorSeesWhatTheSuperadminSees(
    Scenario[SeedingSession, FoldersAndACaller, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "the-monitor-role-searches-across-every-owner-too"

    @override
    def describe(self) -> str:
        return (
            "모니터 역할은 슈퍼관리자가 아니지만 읽는 요청은 지나가므로, "
            "전체 조회가 슈퍼관리자와 같은 답을 준다"
        )

    @override
    def given(self) -> Given[SeedingSession, FoldersAndACaller]:
        return FoldersOfTwoOthers(role=UserRole.MONITOR)

    @override
    def when(self) -> When[FoldersAndACaller, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingEverything()

    @override
    def then(self) -> Then[FoldersAndACaller, SearchVFoldersPayload]:
        return OnlyTheirsIsFound(counted=2)


@dataclass(frozen=True)
class APlainUserMayNotSearchEverything(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, SearchVFoldersPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-everything"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에 읽기 권한을 받았더라도 슈퍼관리자가 아닌 사용자는 "
            "전체를 조회할 수 없다. 권한을 얼마나 받았는지와 무관하게 역할이 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedOverThemselves(permissions=READING)

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingEverything()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, SearchVFoldersPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffChangesNothingHere(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, SearchVFoldersPayload],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-a-user-search-everything"

    @override
    def describe(self) -> str:
        return (
            "권한 집행을 꺼도 슈퍼관리자가 아니면 전체를 조회할 수 없다. "
            "이 요청을 지키는 것이 권한이 아니라 역할이라 스위치와 무관하다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneGrantedNothing()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, SearchVFoldersPayload]:
        return SearchingEverything()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, SearchVFoldersPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSeesEveryFolder(),
    TheMonitorSeesWhatTheSuperadminSees(),
    APlainUserMayNotSearchEverything(),
    EnforcementOffChangesNothingHere(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_admin_searching(
    scenario: SearchingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
