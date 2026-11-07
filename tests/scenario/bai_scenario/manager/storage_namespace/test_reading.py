"""object storage 가 가진 네임스페이스 조회와 여러 id 조회."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.common.dto.manager.v2.storage_namespace.response import StorageNamespaceNode
from ai.backend.manager.api.adapters.storage_namespace.adapter import StorageNamespaceAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.storage_namespace import (
    EveryIdIsRefused,
    Loaded,
    ManyNamespacesAndACaller,
    ManyNamespacesAndSomeone,
    TheNamespacesAreListed,
    TheOrderIsKept,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING_ID = uuid4()

type ReadingStep = Scenario[TestSeedingSession, Any, StorageNamespaceAdapter, Any]


@dataclass(frozen=True)
class ListingOneStoragesNamespaces(
    When[ManyNamespacesAndACaller, StorageNamespaceAdapter, list[StorageNamespaceNode]]
):
    @override
    def operation(self) -> str:
        return "get_namespaces"

    @override
    def describe(self, laid: ManyNamespacesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.storage.name}에 등록된 네임스페이스를 읽습니다",
            english=f"{laid.caller.username} reads the namespaces registered on {laid.storage.name}",
        )

    @override
    async def call(
        self, adapter: StorageNamespaceAdapter, laid: ManyNamespacesAndACaller
    ) -> list[StorageNamespaceNode]:
        with ActingAs(laid.caller):
            return await adapter.get_namespaces(laid.storage.id)


@dataclass(frozen=True)
class ReadingMany(When[ManyNamespacesAndACaller, StorageNamespaceAdapter, Loaded]):
    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyNamespacesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 네임스페이스 둘과 존재하지 않는 id 하나를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} loads two namespaces seeded in advance and one id that "
                "does not exist at once"
            ),
        )

    def ids(self, laid: ManyNamespacesAndACaller) -> list[StorageNamespaceID]:
        return [
            StorageNamespaceID(laid.laid[0].id),
            StorageNamespaceID(MISSING_ID),
            StorageNamespaceID(laid.laid[1].id),
        ]

    @override
    async def call(
        self, adapter: StorageNamespaceAdapter, laid: ManyNamespacesAndACaller
    ) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(self.ids(laid))


@dataclass(frozen=True)
class AUserGrantedReadReadsTheNamespaces(
    Scenario[
        TestSeedingSession,
        ManyNamespacesAndACaller,
        StorageNamespaceAdapter,
        list[StorageNamespaceNode],
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-every-namespace-of-an-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "저장소 네임스페이스 조회 권한을 받은 사용자가 object storage 에 등록된 네임스페이스를 "
            "읽으면 등록된 네임스페이스가 모두 반환됩니다",
            english=(
                "when a user granted permission to read storage namespaces reads the namespaces of "
                "an object storage, every registered namespace comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyNamespacesAndACaller]:
        return ManyNamespacesAndSomeone(granted=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[ManyNamespacesAndACaller, StorageNamespaceAdapter, list[StorageNamespaceNode]]:
        return ListingOneStoragesNamespaces()

    @override
    def then(
        self,
    ) -> Then[ManyNamespacesAndACaller, list[StorageNamespaceNode]]:
        return TheNamespacesAreListed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheNamespaces(
    Scenario[
        TestSeedingSession,
        ManyNamespacesAndACaller,
        StorageNamespaceAdapter,
        list[StorageNamespaceNode],
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-namespaces-of-an-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 object storage 의 네임스페이스를 읽으려 하면 권한 "
            "부족으로 거부됩니다",
            english=(
                "when a user granted nothing reads the namespaces of an object storage, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyNamespacesAndACaller]:
        return ManyNamespacesAndSomeone()

    @override
    def when(
        self,
    ) -> When[ManyNamespacesAndACaller, StorageNamespaceAdapter, list[StorageNamespaceNode]]:
        return ListingOneStoragesNamespaces()

    @override
    def then(
        self,
    ) -> Then[ManyNamespacesAndACaller, list[StorageNamespaceNode]]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedReadReadsManyInOrder(
    Scenario[TestSeedingSession, ManyNamespacesAndACaller, StorageNamespaceAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-several-namespaces-in-the-requested-order"

    @override
    def describe(self) -> str:
        return Says(
            "저장소 네임스페이스 조회 권한을 받은 사용자가 미리 저장한 네임스페이스 둘과 존재하지 않는 "
            "id 하나를 한 번에 조회하면, 둘은 요청한 순서대로 반환되고 존재하지 않는 id 의 항목은 "
            "비어 있습니다",
            english=(
                "when a user granted permission to read storage namespaces loads two namespaces "
                "seeded in advance and one id that does not exist at once, the two come back in "
                "the requested order and the entry for the id that does not exist is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyNamespacesAndACaller]:
        return ManyNamespacesAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyNamespacesAndACaller, StorageNamespaceAdapter, Loaded]:
        return ReadingMany()

    @override
    def then(self) -> Then[ManyNamespacesAndACaller, Loaded]:
        return TheOrderIsKept()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedOnEveryId(
    Scenario[TestSeedingSession, ManyNamespacesAndACaller, StorageNamespaceAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-many-namespace-ids-is-refused-on-every-id"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 네임스페이스 id 여럿을 한 번에 조회하면, 요청 전체가 "
            "거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다",
            english=(
                "when a user granted nothing loads several namespace ids at once, instead of "
                "rejecting the whole request, every entry comes back holding a rejection for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyNamespacesAndACaller]:
        return ManyNamespacesAndSomeone()

    @override
    def when(self) -> When[ManyNamespacesAndACaller, StorageNamespaceAdapter, Loaded]:
        return ReadingMany()

    @override
    def then(self) -> Then[ManyNamespacesAndACaller, Loaded]:
        return EveryIdIsRefused()


SCENARIOS: list[ReadingStep] = [
    AUserGrantedReadReadsTheNamespaces(),
    AUserGrantedNothingMayNotReadTheNamespaces(),
    AUserGrantedReadReadsManyInOrder(),
    AUserGrantedNothingIsRefusedOnEveryId(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep,
    adapter: StorageNamespaceAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
