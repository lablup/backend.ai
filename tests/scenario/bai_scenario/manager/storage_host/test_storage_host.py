"""내가 쓸 수 있는 저장소 호스트 — 등록된 볼륨만, 내 권한만큼."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.storage_host.response import (
    MyStorageHostPermissionsPayload,
)
from ai.backend.manager.api.adapters.storage_host.adapter import StorageHostAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.storage_host import (
    AViewerAndTheirHosts,
    HostsOfSomeone,
    TheHostsOnTheList,
)
from bai_scenario.components.vfolder import STORAGE_HOST
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type HostStep = Scenario[
    TestSeedingSession, AViewerAndTheirHosts, StorageHostAdapter, MyStorageHostPermissionsPayload
]


@dataclass(frozen=True)
class ListingTheHosts(
    When[AViewerAndTheirHosts, StorageHostAdapter, MyStorageHostPermissionsPayload]
):
    """내가 쓸 수 있는 저장소 호스트를 조회한다."""

    @override
    def operation(self) -> str:
        return "my_storage_host_permissions"

    @override
    def describe(self, laid: AViewerAndTheirHosts) -> str:
        return Says(
            f"{laid.caller.username}이 자기 저장소 호스트 권한을 조회합니다",
            english=f"{laid.caller.username} lists the storage host permissions they hold",
        )

    @override
    async def call(
        self, adapter: StorageHostAdapter, laid: AViewerAndTheirHosts
    ) -> MyStorageHostPermissionsPayload:
        with ActingAs(laid.caller):
            return await adapter.my_storage_host_permissions()


@dataclass(frozen=True)
class AGrantedUserSeesTheRegisteredHost(
    Scenario[
        TestSeedingSession,
        AViewerAndTheirHosts,
        StorageHostAdapter,
        MyStorageHostPermissionsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-vfolder-read-sees-only-the-registered-host"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프에서 vfolder 읽기 권한을 받은 사용자가 저장소 호스트 권한을 조회하면, "
            "도메인이 허용하지만 저장소에 등록되지 않은 호스트는 빠지고 등록된 호스트만 "
            "응답으로 옵니다",
            english=(
                "when a user granted vfolder read in their own scope lists their storage hosts, "
                "a host the domain allows but no storage registers is left out and only the "
                "registered host comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AViewerAndTheirHosts]:
        return HostsOfSomeone(
            domain_hosts=(STORAGE_HOST, "local:volume2"), policy_hosts=(STORAGE_HOST,)
        )

    @override
    def when(
        self,
    ) -> When[AViewerAndTheirHosts, StorageHostAdapter, MyStorageHostPermissionsPayload]:
        return ListingTheHosts()

    @override
    def then(self) -> Then[AViewerAndTheirHosts, MyStorageHostPermissionsPayload]:
        return TheHostsOnTheList(hosts=(STORAGE_HOST,))


@dataclass(frozen=True)
class AGrantedUserWithNoRegisteredHostSeesNone(
    Scenario[
        TestSeedingSession,
        AViewerAndTheirHosts,
        StorageHostAdapter,
        MyStorageHostPermissionsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-whose-only-allowed-host-is-unregistered-sees-none"

    @override
    def describe(self) -> str:
        return Says(
            "허용된 호스트가 저장소에 하나도 등록되어 있지 않은 사용자가 저장소 호스트 권한을 "
            "조회하면, 응답은 비어 있습니다",
            english=(
                "when every host the user may use is unregistered with the storage, listing "
                "the storage hosts comes back empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AViewerAndTheirHosts]:
        return HostsOfSomeone(domain_hosts=("local:volume2",), policy_hosts=("local:volume2",))

    @override
    def when(
        self,
    ) -> When[AViewerAndTheirHosts, StorageHostAdapter, MyStorageHostPermissionsPayload]:
        return ListingTheHosts()

    @override
    def then(self) -> Then[AViewerAndTheirHosts, MyStorageHostPermissionsPayload]:
        return TheHostsOnTheList(hosts=())


@dataclass(frozen=True)
class AUserGrantedNothingMayNotListHosts(
    Scenario[
        TestSeedingSession,
        AViewerAndTheirHosts,
        StorageHostAdapter,
        MyStorageHostPermissionsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-list-their-storage-hosts"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 저장소 호스트 권한을 조회하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to list their storage hosts, it is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AViewerAndTheirHosts]:
        return HostsOfSomeone(granted=False)

    @override
    def when(
        self,
    ) -> When[AViewerAndTheirHosts, StorageHostAdapter, MyStorageHostPermissionsPayload]:
        return ListingTheHosts()

    @override
    def then(self) -> Then[AViewerAndTheirHosts, MyStorageHostPermissionsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[HostStep] = [
    AGrantedUserSeesTheRegisteredHost(),
    AGrantedUserWithNoRegisteredHostSeesNone(),
    AUserGrantedNothingMayNotListHosts(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_storage_host(
    scenario: HostStep, adapter: StorageHostAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
