"""object storage 검색."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.object_storage.request import (
    AdminSearchObjectStoragesInput,
    ObjectStorageFilter,
    ObjectStorageOrder,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    AdminSearchObjectStoragesPayload,
    ObjectStorageNode,
)
from ai.backend.common.dto.manager.v2.object_storage.types import (
    ObjectStorageOrderField,
    OrderDirection,
)
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.object_storage import (
    ManyStoragesAndACaller,
    ManyStoragesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchStep = Scenario[
    TestSeedingSession, Any, ObjectStorageAdapter, AdminSearchObjectStoragesPayload
]


def storage_snapshot(storage: ObjectStorageData | ObjectStorageNode) -> tuple[Any, ...]:
    return (
        storage.id,
        storage.entity_id if isinstance(storage, ObjectStorageNode) else storage.entity_id(),
        storage.name,
        storage.host,
        storage.access_key,
        storage.secret_key,
        storage.endpoint,
        storage.region,
    )


def the_storages(
    got: Sequence[ObjectStorageNode], wanted: Sequence[ObjectStorageData]
) -> list[Verdict]:
    return [
        Held(
            "items",
            sorted(storage_snapshot(one) for one in got),
            SameAs(
                sorted(storage_snapshot(one) for one in wanted),
                Says("미리 저장한 object storage", english="the object storages seeded in advance"),
            ),
        )
    ]


@dataclass(frozen=True)
class Searching(
    When[ManyStoragesAndACaller, ObjectStorageAdapter, AdminSearchObjectStoragesPayload]
):
    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyStoragesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 이름으로 object storage 를 거르고 이름 오름차순으로 "
            "정렬해 한 쪽을 요청합니다",
            english=(
                f"{laid.caller.username} filters object storages by name, orders them by name "
                "ascending and asks for one page"
            ),
        )

    @override
    async def call(
        self, adapter: ObjectStorageAdapter, laid: ManyStoragesAndACaller
    ) -> AdminSearchObjectStoragesPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchObjectStoragesInput(
                    filter=ObjectStorageFilter(name=StringFilter(equals=laid.laid[0].name)),
                    order=[
                        ObjectStorageOrder(
                            field=ObjectStorageOrderField.NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                    offset=0,
                )
            )


@dataclass(frozen=True)
class OnlyTheNamedStorageIsReturned(Then[ManyStoragesAndACaller, AdminSearchObjectStoragesPayload]):
    @override
    def says(self) -> str:
        return Says(
            "이름이 일치하는 object storage 만 반환됩니다",
            english="only the object storage with the matching name comes back",
        )

    @override
    def look(
        self,
        laid: ManyStoragesAndACaller,
        answered: Answered[AdminSearchObjectStoragesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            *the_storages(payload.items, [laid.laid[0]]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheSuperadminFiltersByName(
    Scenario[
        TestSeedingSession,
        ManyStoragesAndACaller,
        ObjectStorageAdapter,
        AdminSearchObjectStoragesPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "filtering-by-name-leaves-only-the-matching-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이름으로 거르고 이름 오름차순으로 정렬해 한 쪽을 요청하면 그 이름의 "
            "object storage 하나만 반환됩니다. 이 호출은 전역 역할을 검사합니다",
            english=(
                "when the superadmin filters by name, orders by name ascending and asks for one "
                "page, only the object storage with that name comes back. This call is gated by "
                "the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ManyStoragesAndACaller, ObjectStorageAdapter, AdminSearchObjectStoragesPayload]:
        return Searching()

    @override
    def then(
        self,
    ) -> Then[ManyStoragesAndACaller, AdminSearchObjectStoragesPayload]:
        return OnlyTheNamedStorageIsReturned()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[
        TestSeedingSession,
        ManyStoragesAndACaller,
        ObjectStorageAdapter,
        AdminSearchObjectStoragesPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-object-storages"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 object storage 를 검색하려 하면 권한 부족으로 거부됩니다. "
            "이 호출은 전역 역할을 검사합니다",
            english=(
                "when a user who is not the superadmin tries to search object storages, it is "
                "rejected for lack of permission. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone()

    @override
    def when(
        self,
    ) -> When[ManyStoragesAndACaller, ObjectStorageAdapter, AdminSearchObjectStoragesPayload]:
        return Searching()

    @override
    def then(
        self,
    ) -> Then[ManyStoragesAndACaller, AdminSearchObjectStoragesPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchStep] = [
    TheSuperadminFiltersByName(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep,
    adapter: ObjectStorageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
