"""VFS storage 검색과 전체 목록."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.vfs_storage.request import AdminSearchVFSStoragesInput
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    AdminSearchVFSStoragesPayload,
    VFSStorageNode,
)
from ai.backend.manager.api.adapters.vfs_storage.adapter import VFSStorageAdapter
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
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
from bai_scenario.components.answers import MissingResponse, OneOfTheSeeded, TheCallIsRefused
from bai_scenario.components.vfs_storage import (
    ManyStoragesAndACaller,
    ManyStoragesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchStep = Scenario[TestSeedingSession, Any, VFSStorageAdapter, Any]


def storage_snapshot(storage: VFSStorageData | VFSStorageNode) -> tuple[Any, ...]:
    return (
        storage.id,
        storage.entity_id if isinstance(storage, VFSStorageNode) else storage.entity_id(),
        storage.name,
        storage.host,
        storage.base_path if isinstance(storage, VFSStorageNode) else str(storage.base_path),
    )


def the_seeded_storages(
    got: Sequence[VFSStorageNode], laid: ManyStoragesAndACaller
) -> list[Verdict]:
    wanted = sorted(storage_snapshot(one) for one in laid.laid)
    return [
        Held(
            "items",
            sorted(storage_snapshot(one) for one in got),
            SameAs(
                wanted,
                Says("미리 저장한 VFS storage", english="the VFS storages seeded in advance"),
            ),
        )
    ]


@dataclass(frozen=True)
class Searching(When[ManyStoragesAndACaller, VFSStorageAdapter, AdminSearchVFSStoragesPayload]):
    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyStoragesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 VFS storage 를 검색해 한 쪽을 요청합니다",
            english=f"{laid.caller.username} searches VFS storages and asks for one page",
        )

    @override
    async def call(
        self, adapter: VFSStorageAdapter, laid: ManyStoragesAndACaller
    ) -> AdminSearchVFSStoragesPayload:
        with ActingAs(laid.caller):
            return await adapter.search(AdminSearchVFSStoragesInput(limit=1, offset=0))


@dataclass(frozen=True)
class Listing(When[ManyStoragesAndACaller, VFSStorageAdapter, list[VFSStorageNode]]):
    @override
    def operation(self) -> str:
        return "list_all"

    @override
    def describe(self, laid: ManyStoragesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 VFS storage 전체 목록을 읽습니다",
            english=f"{laid.caller.username} lists every VFS storage",
        )

    @override
    async def call(
        self, adapter: VFSStorageAdapter, laid: ManyStoragesAndACaller
    ) -> list[VFSStorageNode]:
        with ActingAs(laid.caller):
            return await adapter.list_all()


@dataclass(frozen=True)
class OneSeededStorageIsOnThePage(Then[ManyStoragesAndACaller, AdminSearchVFSStoragesPayload]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 VFS storage 둘 가운데 하나만 한 쪽에 오고, 남은 하나는 다음 쪽에 있습니다",
            english=(
                "only one of the two VFS storages seeded in advance comes on the page and the "
                "other is on the next page"
            ),
        )

    @override
    def look(
        self,
        laid: ManyStoragesAndACaller,
        answered: Answered[AdminSearchVFSStoragesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("length", len(payload.items), 1),
            Held(
                "items",
                [storage_snapshot(one) for one in payload.items],
                OneOfTheSeeded(
                    frozenset(storage_snapshot(one) for one in laid.laid),
                    Says(
                        "미리 저장한 VFS storage 가운데 하나",
                        english="one of the VFS storages seeded in advance",
                    ),
                ),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheWholeListIsReturned(Then[ManyStoragesAndACaller, list[VFSStorageNode]]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 VFS storage 가 모두 순서 없이 반환됩니다",
            english="every VFS storage seeded in advance comes back",
        )

    @override
    def look(
        self, laid: ManyStoragesAndACaller, answered: Answered[list[VFSStorageNode]]
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        return the_seeded_storages(items, laid)


@dataclass(frozen=True)
class TheSuperadminSearches(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-vfs-storages-gets-one-page"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 VFS storage 를 검색해 한 쪽을 요청하면 미리 저장한 VFS storage 둘 "
            "가운데 하나만 오고, 전체 개수는 둘입니다",
            english=(
                "when the superadmin searches VFS storages and asks for one page, one of the two "
                "VFS storages seeded in advance comes back and the total count is two"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyStoragesAndACaller, VFSStorageAdapter, Any]:
        return Searching()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Any]:
        return OneSeededStorageIsOnThePage()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-vfs-storages"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 VFS storage 를 검색하려 하면 권한 부족으로 거부됩니다. "
            "이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다",
            english=(
                "when a user who is not the superadmin tries to search VFS storages, it is "
                "rejected for lack of permission. This call checks only whether the caller is "
                "the superadmin and does not look at the permissions granted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone()

    @override
    def when(self) -> When[ManyStoragesAndACaller, VFSStorageAdapter, Any]:
        return Searching()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Any]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminListsEveryStorage(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-listing-vfs-storages-gets-every-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 VFS storage 전체 목록을 읽으면 미리 저장한 VFS storage 가 모두 "
            "반환됩니다",
            english=(
                "when the superadmin lists VFS storages, every VFS storage seeded in advance "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyStoragesAndACaller, VFSStorageAdapter, Any]:
        return Listing()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Any]:
        return TheWholeListIsReturned()


@dataclass(frozen=True)
class APlainUserMayNotList(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-list-vfs-storages"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 VFS storage 전체 목록을 읽으려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다",
            english=(
                "when a user who is not the superadmin tries to list VFS storages, it is rejected "
                "for lack of permission. This call checks only whether the caller is the "
                "superadmin and does not look at the permissions granted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone()

    @override
    def when(self) -> When[ManyStoragesAndACaller, VFSStorageAdapter, Any]:
        return Listing()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Any]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchStep] = [
    TheSuperadminSearches(),
    APlainUserMayNotSearch(),
    TheSuperadminListsEveryStorage(),
    APlainUserMayNotList(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: VFSStorageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
