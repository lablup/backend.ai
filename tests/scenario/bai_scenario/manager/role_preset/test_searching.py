"""프리셋 검색 — 스코프 id 필터에 따른 결과를 검증한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import NullableUUIDFilter
from ai.backend.common.dto.manager.v2.role_preset.request import (
    RolePresetFilter,
    SearchRolePresetsInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import SearchRolePresetsPayload
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    OnlyThatPresetComesBack,
    PresetsForPublicAndEveryProjectAndACaller,
    PresetsForPublicAndEveryProjectAndSomeone,
    RemainingPreset,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchingStep = Scenario[
    TestSeedingSession,
    PresetsForPublicAndEveryProjectAndACaller,
    RolePresetAdapter,
    SearchRolePresetsPayload,
]


@dataclass(frozen=True)
class SearchingByTheScopeOfOnePreset(
    When[PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload]
):
    """스코프 하나에만 역할을 만드는 프리셋이 지정한 스코프의 id로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: PresetsForPublicAndEveryProjectAndACaller) -> str:
        return (
            f"{laid.caller.username}이 {laid.for_public.name}이 지정한 스코프의 id를 "
            "스코프 id 필터에 지정해 검색"
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: PresetsForPublicAndEveryProjectAndACaller
    ) -> SearchRolePresetsPayload:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRolePresetsInput(
                    filter=RolePresetFilter(
                        scope_id=NullableUUIDFilter(equals=laid.for_public.scope_id)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingWithoutAScopeId(
    When[PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload]
):
    """스코프 id가 비어 있는 프리셋을 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: PresetsForPublicAndEveryProjectAndACaller) -> str:
        return f"{laid.caller.username}이 스코프 id가 비어 있는 프리셋을 검색"

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: PresetsForPublicAndEveryProjectAndACaller
    ) -> SearchRolePresetsPayload:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRolePresetsInput(
                    filter=RolePresetFilter(scope_id=NullableUUIDFilter(is_null=True))
                )
            )


@dataclass(frozen=True)
class SearchingWithAScopeId(
    When[PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload]
):
    """스코프 id가 있는 프리셋을 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: PresetsForPublicAndEveryProjectAndACaller) -> str:
        return f"{laid.caller.username}이 스코프 id가 있는 프리셋을 검색"

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: PresetsForPublicAndEveryProjectAndACaller
    ) -> SearchRolePresetsPayload:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRolePresetsInput(
                    filter=RolePresetFilter(scope_id=NullableUUIDFilter(is_null=False))
                )
            )


@dataclass(frozen=True)
class AScopeIdFindsThePresetForThatScope(
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
        return "a-scope-id-finds-the-preset-for-that-scope-alone"

    @override
    def describe(self) -> str:
        return Says(
            "슈퍼관리자가 한 스코프의 id로 프리셋을 검색하면, 그 스코프 하나에만 역할을 만드는 "
            "프리셋만 반환된다"
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
        return SearchingByTheScopeOfOnePreset()

    @override
    def then(self) -> Then[PresetsForPublicAndEveryProjectAndACaller, SearchRolePresetsPayload]:
        return OnlyThatPresetComesBack(self.started, RemainingPreset.FOR_PUBLIC)


@dataclass(frozen=True)
class NoScopeIdFindsThePresetsForEveryScope(
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
        return "no-scope-id-finds-the-presets-for-every-scope-of-their-type"

    @override
    def describe(self) -> str:
        return Says(
            "슈퍼관리자가 스코프 id가 비어 있는 프리셋을 검색하면, 그 타입의 모든 스코프에 "
            "역할을 만드는 프리셋만 반환된다"
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
        return SearchingWithoutAScopeId()

    @override
    def then(self) -> Then[PresetsForPublicAndEveryProjectAndACaller, SearchRolePresetsPayload]:
        return OnlyThatPresetComesBack(self.started, RemainingPreset.FOR_EVERY_PROJECT)


@dataclass(frozen=True)
class SomeScopeIdFindsThePresetsForOneScope(
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
        return "some-scope-id-finds-the-presets-for-one-scope"

    @override
    def describe(self) -> str:
        return Says(
            "슈퍼관리자가 스코프 id가 있는 프리셋을 검색하면, 스코프 하나에만 역할을 만드는 "
            "프리셋만 반환된다"
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
        return SearchingWithAScopeId()

    @override
    def then(self) -> Then[PresetsForPublicAndEveryProjectAndACaller, SearchRolePresetsPayload]:
        return OnlyThatPresetComesBack(self.started, RemainingPreset.FOR_PUBLIC)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[
        TestSeedingSession,
        PresetsForPublicAndEveryProjectAndACaller,
        RolePresetAdapter,
        SearchRolePresetsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-presets"

    @override
    def describe(self) -> str:
        return Says("아무 권한도 받지 않은 사용자가 프리셋을 검색하려 하면, 권한 부족으로 거부된다")

    @override
    def given(self) -> Given[TestSeedingSession, PresetsForPublicAndEveryProjectAndACaller]:
        return PresetsForPublicAndEveryProjectAndSomeone()

    @override
    def when(
        self,
    ) -> When[
        PresetsForPublicAndEveryProjectAndACaller, RolePresetAdapter, SearchRolePresetsPayload
    ]:
        return SearchingWithAScopeId()

    @override
    def then(self) -> Then[PresetsForPublicAndEveryProjectAndACaller, SearchRolePresetsPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    AScopeIdFindsThePresetForThatScope(started=datetime.now(UTC)),
    NoScopeIdFindsThePresetsForEveryScope(started=datetime.now(UTC)),
    SomeScopeIdFindsThePresetsForOneScope(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
