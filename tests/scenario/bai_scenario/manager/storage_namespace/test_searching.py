"""등록된 네임스페이스 검색."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    AdminSearchStorageNamespacesInput,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    AdminSearchStorageNamespacesPayload,
)
from ai.backend.manager.api.adapters.storage_namespace.adapter import StorageNamespaceAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.storage_namespace import (
    EveryNamespaceIsSearched,
    ManyNamespacesAndACaller,
    ManyNamespacesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchingStep = Scenario[
    TestSeedingSession,
    ManyNamespacesAndACaller,
    StorageNamespaceAdapter,
    AdminSearchStorageNamespacesPayload,
]


@dataclass(frozen=True)
class Searching(
    When[ManyNamespacesAndACaller, StorageNamespaceAdapter, AdminSearchStorageNamespacesPayload]
):
    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyNamespacesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 등록된 네임스페이스를 검색합니다",
            english=f"{laid.caller.username} searches registered namespaces",
        )

    @override
    async def call(
        self, adapter: StorageNamespaceAdapter, laid: ManyNamespacesAndACaller
    ) -> AdminSearchStorageNamespacesPayload:
        with ActingAs(laid.caller):
            return await adapter.search(AdminSearchStorageNamespacesInput())


@dataclass(frozen=True)
class TheSuperadminSearches(
    Scenario[
        TestSeedingSession,
        ManyNamespacesAndACaller,
        StorageNamespaceAdapter,
        AdminSearchStorageNamespacesPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-namespaces-counts-every-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 네임스페이스를 검색하면 미리 저장한 네임스페이스가 모두 반환됩니다. "
            "이 호출은 전역 역할을 검사합니다",
            english=(
                "when the superadmin searches namespaces, every namespace seeded in advance comes "
                "back. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyNamespacesAndACaller]:
        return ManyNamespacesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[
        ManyNamespacesAndACaller, StorageNamespaceAdapter, AdminSearchStorageNamespacesPayload
    ]:
        return Searching()

    @override
    def then(
        self,
    ) -> Then[ManyNamespacesAndACaller, AdminSearchStorageNamespacesPayload]:
        return EveryNamespaceIsSearched()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[
        TestSeedingSession,
        ManyNamespacesAndACaller,
        StorageNamespaceAdapter,
        AdminSearchStorageNamespacesPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-namespaces"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 네임스페이스를 검색하려 하면 권한 부족으로 거부됩니다. "
            "이 호출은 전역 역할을 검사합니다",
            english=(
                "when a user who is not the superadmin tries to search namespaces, it is "
                "rejected for lack of permission. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyNamespacesAndACaller]:
        return ManyNamespacesAndSomeone()

    @override
    def when(
        self,
    ) -> When[
        ManyNamespacesAndACaller, StorageNamespaceAdapter, AdminSearchStorageNamespacesPayload
    ]:
        return Searching()

    @override
    def then(
        self,
    ) -> Then[ManyNamespacesAndACaller, AdminSearchStorageNamespacesPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSearches(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep,
    adapter: StorageNamespaceAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
