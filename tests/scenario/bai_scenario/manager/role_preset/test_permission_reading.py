"""프리셋의 권한 항목 읽기와 검색."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO, PermissionBitFilter
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    RolePermissionPresetFilter,
    RolePermissionPresetOrder,
    SearchRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    RolePermissionPresetNode,
    SearchRolePermissionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
    RolePermissionPresetOrderField,
)
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    APresetWithEntriesAndACaller,
    APresetWithEntriesAndSomeone,
    EveryEntryIsDenied,
    PresetEntriesForSearchAndSomeone,
    PresetEntriesToFind,
    TheMatchingEntryPage,
    TheWholePermissionsInOrder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Loaded = list[RolePermissionPresetNode | Exception | None]
type LoadingStep = Scenario[
    TestSeedingSession, APresetWithEntriesAndACaller, RolePresetAdapter, Loaded
]
type SearchStep = Scenario[
    TestSeedingSession, PresetEntriesToFind, RolePresetAdapter, SearchRolePermissionPresetsPayload
]


@dataclass(frozen=True)
class LoadingEntries(When[APresetWithEntriesAndACaller, RolePresetAdapter, Loaded]):
    """미리 만들어 둔 권한 항목들의 id 를 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_permissions_by_ids"

    @override
    def describe(self, laid: APresetWithEntriesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.preset.name}의 권한 항목 "
            f"{len(laid.entries)}개의 id 를 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} reads the ids of {len(laid.entries)} permission entries "
                f"of {laid.preset.name} at once"
            ),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetWithEntriesAndACaller) -> Loaded:
        ids = [entry.id for entry in laid.entries]
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions_by_ids(ids)


@dataclass(frozen=True)
class SearchingEntries(
    When[PresetEntriesToFind, RolePresetAdapter, SearchRolePermissionPresetsPayload]
):
    """권한 비트 필터, 엔티티 타입 정렬, 한 페이지 크기로 항목을 검색한다."""

    @override
    def operation(self) -> str:
        return "search_permission_presets"

    @override
    def describe(self, laid: PresetEntriesToFind) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.preset.name}의 권한 항목을 조회 비트 필터, 엔티티 "
            "타입 정렬, 한 페이지 크기로 검색합니다",
            english=(
                f"{laid.caller.username} searches the permission entries of {laid.preset.name} "
                "with the read-bit filter, entity-type order and a page size of one"
            ),
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: PresetEntriesToFind
    ) -> SearchRolePermissionPresetsPayload:
        with ActingAs(laid.caller):
            return await adapter.search_permission_presets(
                laid.preset.id,
                SearchRolePermissionPresetsInput(
                    filter=RolePermissionPresetFilter(
                        permission=PermissionBitFilter(equals=PermissionBitDTO.READ)
                    ),
                    order=[
                        RolePermissionPresetOrder(
                            field=RolePermissionPresetOrderField.ENTITY_TYPE,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                ),
            )


@dataclass(frozen=True)
class AGrantedUserLoadsThemInOrder(
    Scenario[TestSeedingSession, APresetWithEntriesAndACaller, RolePresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-loads-permission-entries-in-order"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 조회 권한을 받은 사용자가 프리셋의 권한 항목 둘의 id 를 한 번에 "
            "조회하면, 둘 다 요청한 순서대로 각각 전체가 반환됩니다",
            english=(
                "when a user granted read in global loads the ids of two permission entries of a "
                "preset at once, both come back whole in the requested order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetWithEntriesAndACaller]:
        return APresetWithEntriesAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[APresetWithEntriesAndACaller, RolePresetAdapter, Loaded]:
        return LoadingEntries()

    @override
    def then(self) -> Then[APresetWithEntriesAndACaller, Loaded]:
        return TheWholePermissionsInOrder()


@dataclass(frozen=True)
class AUserGrantedNothingLoadsNone(
    Scenario[TestSeedingSession, APresetWithEntriesAndACaller, RolePresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-loading-entries-is-denied-on-every-id"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 권한 항목 둘의 id 를 한 번에 조회하면, 요청 전체가 "
            "거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다",
            english=(
                "when a user granted nothing loads the ids of two permission entries at once, "
                "instead of the whole request being rejected, every entry comes back holding a "
                "rejection for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetWithEntriesAndACaller]:
        return APresetWithEntriesAndSomeone()

    @override
    def when(self) -> When[APresetWithEntriesAndACaller, RolePresetAdapter, Loaded]:
        return LoadingEntries()

    @override
    def then(self) -> Then[APresetWithEntriesAndACaller, Loaded]:
        return EveryEntryIsDenied()


@dataclass(frozen=True)
class AGrantedUserFindsOnePage(
    Scenario[
        TestSeedingSession,
        PresetEntriesToFind,
        RolePresetAdapter,
        SearchRolePermissionPresetsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-finds-one-page-of-matching-entries"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 조회 권한을 받은 사용자가 권한 항목을 조회 비트 필터, 엔티티 타입 정렬, "
            "한 페이지 크기로 검색하면, 맞는 항목 가운데 정렬상 첫 하나만 오고 나머지 맞는 항목, "
            "필터에 걸리는 항목, 다른 프리셋의 항목은 오지 않습니다",
            english=(
                "when a user granted read in global searches permission entries with the read-bit "
                "filter, entity-type order and a page size of one, only the first matching entry "
                "in the order comes back and neither the other matching entry, the entry the "
                "filter excludes nor the entry of the other preset comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetEntriesToFind]:
        return PresetEntriesForSearchAndSomeone(granted=Permission.READ)

    @override
    def when(
        self,
    ) -> When[PresetEntriesToFind, RolePresetAdapter, SearchRolePermissionPresetsPayload]:
        return SearchingEntries()

    @override
    def then(self) -> Then[PresetEntriesToFind, SearchRolePermissionPresetsPayload]:
        return TheMatchingEntryPage()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[
        TestSeedingSession,
        PresetEntriesToFind,
        RolePresetAdapter,
        SearchRolePermissionPresetsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-permission-entries"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋의 권한 항목을 검색하려 하면, 요청 전체가 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to search the permission entries of a preset, "
                "the whole request is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetEntriesToFind]:
        return PresetEntriesForSearchAndSomeone(granted=None)

    @override
    def when(
        self,
    ) -> When[PresetEntriesToFind, RolePresetAdapter, SearchRolePermissionPresetsPayload]:
        return SearchingEntries()

    @override
    def then(self) -> Then[PresetEntriesToFind, SearchRolePermissionPresetsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[LoadingStep | SearchStep] = [
    AGrantedUserLoadsThemInOrder(),
    AUserGrantedNothingLoadsNone(),
    AGrantedUserFindsOnePage(),
    AUserGrantedNothingMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_permission_reading(
    scenario: LoadingStep | SearchStep,
    adapter: RolePresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
