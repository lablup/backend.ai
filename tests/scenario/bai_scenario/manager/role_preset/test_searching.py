"""프리셋 검색."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.role_preset.request import (
    RolePresetFilter,
    RolePresetOrder,
    SearchRolePresetsInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import SearchRolePresetsPayload
from ai.backend.common.dto.manager.v2.role_preset.types import RolePresetOrderField
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    OnlyThePresetForPublicComesBack,
    PresetsForPublicAndEveryProjectAndACaller,
    PresetsForPublicAndEveryProjectAndSomeone,
    PresetsToFind,
    ProjectPresetsAndADomainOne,
    TheMatchingPresetPage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchStep = Scenario[TestSeedingSession, Any, RolePresetAdapter, SearchRolePresetsPayload]


@dataclass(frozen=True)
class Searching(When[PresetsToFind, RolePresetAdapter, SearchRolePresetsPayload]):
    """프로젝트 스코프 필터, 이름 정렬, 한 페이지 크기로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: PresetsToFind) -> str:
        return Says(
            f"{laid.caller.username}이 프로젝트 스코프 필터, 이름 정렬, 한 페이지 크기로 "
            "조회합니다",
            english=(
                f"{laid.caller.username} searches with the project-scope filter, name order and "
                "a page size of one"
            ),
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: PresetsToFind
    ) -> SearchRolePresetsPayload:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRolePresetsInput(
                    filter=RolePresetFilter(
                        scope_type=StringFilter(equals=str(ProjectEntityType()))
                    ),
                    order=[
                        RolePresetOrder(
                            field=RolePresetOrderField.NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                )
            )


@dataclass(frozen=True)
class SearchingByScopeType(
    When[PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload]
):
    """스코프 타입 필터에 값 하나를 지정해 검색한다."""

    scope_type: str

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: PresetsForPublicAndEveryProjectAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 스코프 타입이 {self.scope_type}인 프리셋을 검색합니다",
            english=(
                f"{laid.caller.username} searches presets whose scope type is {self.scope_type}"
            ),
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: PresetsForPublicAndEveryProjectAndACaller
    ) -> SearchRolePresetsPayload:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRolePresetsInput(
                    filter=RolePresetFilter(scope_type=StringFilter(equals=self.scope_type))
                )
            )


@dataclass(frozen=True)
class TheSuperadminFindsOnePage(
    Scenario[TestSeedingSession, PresetsToFind, RolePresetAdapter, SearchRolePresetsPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-finds-one-page-of-matching-presets"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 프로젝트 스코프 필터, 이름 정렬, 한 페이지 크기로 검색하면, 맞는 "
            "프리셋 가운데 정렬상 첫 하나만 오고 나머지는 오지 않습니다. 이 호출은 global "
            "역할이 막습니다",
            english=(
                "when the superadmin searches with the project-scope filter, name order and a "
                "page size of one, only the first matching preset in the order comes back and "
                "the rest do not. The global role gates this call"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsToFind]:
        return ProjectPresetsAndADomainOne()

    @override
    def when(self) -> When[PresetsToFind, RolePresetAdapter, SearchRolePresetsPayload]:
        return Searching()

    @override
    def then(self) -> Then[PresetsToFind, SearchRolePresetsPayload]:
        return TheMatchingPresetPage()


@dataclass(frozen=True)
class ARegularUserMayNotSearch(
    Scenario[TestSeedingSession, PresetsToFind, RolePresetAdapter, SearchRolePresetsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-presets"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할이 없는 사용자가 프리셋을 검색하려 하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user without the global role tries to search presets, it is rejected for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsToFind]:
        return ProjectPresetsAndADomainOne(role=UserRole.USER)

    @override
    def when(self) -> When[PresetsToFind, RolePresetAdapter, SearchRolePresetsPayload]:
        return Searching()

    @override
    def then(self) -> Then[PresetsToFind, SearchRolePresetsPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AGlobalScopeTypeFindsThePresetForPublic(
    Scenario[
        TestSeedingSession,
        PresetsForPublicAndEveryProjectAndACaller,
        RolePresetAdapter,
        SearchRolePresetsPayload,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-global-scope-type-finds-the-preset-for-public"

    @override
    def describe(self) -> str:
        scope_type = GlobalEntityType()
        public = GlobalEntityName.PUBLIC
        return Says(
            f"superadmin 이 스코프 타입 {scope_type}로 프리셋을 검색하면, {public} 하나에만 "
            "역할을 만드는 프리셋만 반환됩니다",
            english=(
                f"when the superadmin searches presets with the scope type {scope_type}, only "
                f"the preset creating its role in {public} alone comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsForPublicAndEveryProjectAndACaller]:
        return PresetsForPublicAndEveryProjectAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[
        PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload
    ]:
        return SearchingByScopeType(str(GlobalEntityType()))

    @override
    def then(self) -> Then[PresetsForPublicAndEveryProjectAndACaller, SearchRolePresetsPayload]:
        return OnlyThePresetForPublicComesBack(self.started)


SCENARIOS: list[SearchStep] = [
    TheSuperadminFindsOnePage(),
    AGlobalScopeTypeFindsThePresetForPublic(started=datetime.now(UTC)),
    ARegularUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep,
    adapter: RolePresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
