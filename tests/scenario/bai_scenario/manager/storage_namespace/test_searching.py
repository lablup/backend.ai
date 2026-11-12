"""등록된 네임스페이스 검색."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    AdminSearchStorageNamespacesInput,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    AdminSearchStorageNamespacesPayload,
    StorageNamespaceNode,
)
from ai.backend.manager.api.adapters.storage_namespace.adapter import StorageNamespaceAdapter
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, OneOfTheSeeded, TheCallIsRefused
from bai_scenario.components.storage_namespace import (
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


def namespace_snapshot(one: StorageNamespaceNode | StorageNamespaceData) -> tuple[Any, ...]:
    if isinstance(one, StorageNamespaceNode):
        return (one.id, one.entity_id, one.storage_id, one.namespace)
    return (one.id, one.id, one.storage_id, one.namespace)


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
            f"{laid.caller.username}이 등록된 네임스페이스를 검색해 한 쪽을 요청합니다",
            english=f"{laid.caller.username} searches registered namespaces and asks for one page",
        )

    @override
    async def call(
        self, adapter: StorageNamespaceAdapter, laid: ManyNamespacesAndACaller
    ) -> AdminSearchStorageNamespacesPayload:
        with ActingAs(laid.caller):
            return await adapter.search(AdminSearchStorageNamespacesInput(limit=1, offset=0))


@dataclass(frozen=True)
class OneSeededNamespaceIsOnThePage(
    Then[ManyNamespacesAndACaller, AdminSearchStorageNamespacesPayload]
):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 네임스페이스 둘 가운데 하나만 한 쪽에 오고, 남은 하나는 다음 쪽에 있습니다",
            english=(
                "only one of the two namespaces seeded in advance comes on the page and the "
                "other is on the next page"
            ),
        )

    @override
    def look(
        self,
        laid: ManyNamespacesAndACaller,
        answered: Answered[AdminSearchStorageNamespacesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("length", len(payload.items), 1),
            Held(
                "items",
                [namespace_snapshot(one) for one in payload.items],
                OneOfTheSeeded(
                    frozenset(namespace_snapshot(one) for one in laid.laid),
                    Says(
                        "미리 저장한 네임스페이스 가운데 하나",
                        english="one of the namespaces seeded in advance",
                    ),
                ),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


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
        return "the-superadmin-searching-namespaces-gets-one-page"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 네임스페이스를 검색해 한 쪽을 요청하면 미리 저장한 네임스페이스 둘 "
            "가운데 하나만 오고, 전체 개수는 둘입니다. 이 호출은 전역 역할을 검사합니다",
            english=(
                "when the superadmin searches namespaces and asks for one page, one of the two "
                "namespaces seeded in advance comes back and the total count is two. This call is "
                "gated by the global role"
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
        return OneSeededNamespaceIsOnThePage()


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
