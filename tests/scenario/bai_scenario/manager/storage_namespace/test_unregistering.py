"""object storage 아래에서 네임스페이스 하나 빼기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    UnregisterStorageNamespaceInput,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    UnregisterStorageNamespacePayload,
)
from ai.backend.manager.api.adapters.storage_namespace.adapter import StorageNamespaceAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.storage_namespace import (
    ANamespaceAndACaller,
    ANamespaceAndSomeone,
    TheUnregisteredStorageId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING_NAMESPACE = "missing-bucket"

type UnregisteringStep = Scenario[
    TestSeedingSession,
    ANamespaceAndACaller,
    StorageNamespaceAdapter,
    UnregisterStorageNamespacePayload,
]


@dataclass(frozen=True)
class Unregistering(
    When[ANamespaceAndACaller, StorageNamespaceAdapter, UnregisterStorageNamespacePayload]
):
    missing: bool = False

    @override
    def operation(self) -> str:
        return "unregister"

    @override
    def describe(self, laid: ANamespaceAndACaller) -> str:
        target_ko = MISSING_NAMESPACE if self.missing else laid.namespace.namespace
        target_en = MISSING_NAMESPACE if self.missing else laid.namespace.namespace
        return Says(
            f"{laid.caller.username}이 {laid.storage.name}에서 네임스페이스 {target_ko}를 뺍니다",
            english=(
                f"{laid.caller.username} unregisters the namespace {target_en} from "
                f"{laid.storage.name}"
            ),
        )

    @override
    async def call(
        self, adapter: StorageNamespaceAdapter, laid: ANamespaceAndACaller
    ) -> UnregisterStorageNamespacePayload:
        namespace = MISSING_NAMESPACE if self.missing else laid.namespace.namespace
        with ActingAs(laid.caller):
            return await adapter.unregister(
                UnregisterStorageNamespaceInput(storage_id=laid.storage.id, namespace=namespace)
            )


@dataclass(frozen=True)
class AUserGrantedReadAndDeleteUnregisters(
    Scenario[
        TestSeedingSession,
        ANamespaceAndACaller,
        StorageNamespaceAdapter,
        UnregisterStorageNamespacePayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-and-delete-unregisters-a-namespace-from-an-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "저장소 네임스페이스 조회와 완전 삭제 권한을 받은 사용자가 네임스페이스를 빼면 그 "
            "네임스페이스가 있던 object storage 의 id 가 반환됩니다",
            english=(
                "when a user granted permission to read and purge storage namespaces unregisters a "
                "namespace, the id of the object storage it was on comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ANamespaceAndACaller]:
        return ANamespaceAndSomeone(granted=(Permission.READ, Permission.HARD_DELETE))

    @override
    def when(
        self,
    ) -> When[ANamespaceAndACaller, StorageNamespaceAdapter, UnregisterStorageNamespacePayload]:
        return Unregistering()

    @override
    def then(
        self,
    ) -> Then[ANamespaceAndACaller, UnregisterStorageNamespacePayload]:
        return TheUnregisteredStorageId()


@dataclass(frozen=True)
class ANamespaceNothingAnswersToIsNotFound(
    Scenario[
        TestSeedingSession,
        ANamespaceAndACaller,
        StorageNamespaceAdapter,
        UnregisterStorageNamespacePayload,
    ]
):
    @override
    def summary(self) -> str:
        return "unregistering-a-namespace-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 등록되지 않은 네임스페이스를 빼려 하면 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when the superadmin unregisters a namespace that was never registered, it is "
                "rejected because the target cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ANamespaceAndACaller]:
        return ANamespaceAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ANamespaceAndACaller, StorageNamespaceAdapter, UnregisterStorageNamespacePayload]:
        return Unregistering(missing=True)

    @override
    def then(
        self,
    ) -> Then[ANamespaceAndACaller, UnregisterStorageNamespacePayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotUnregister(
    Scenario[
        TestSeedingSession,
        ANamespaceAndACaller,
        StorageNamespaceAdapter,
        UnregisterStorageNamespacePayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-unregister-a-namespace"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 네임스페이스를 빼려 하면 거부됩니다. 이 호출은 "
            "네임스페이스를 먼저 찾아 읽어야 하므로, 읽을 수 없는 대상은 있는지도 드러나지 "
            "않습니다",
            english=(
                "when a user granted nothing tries to unregister a namespace, it is rejected. "
                "This call reads the namespace first, so a target the caller cannot read does "
                "not reveal whether it exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ANamespaceAndACaller]:
        return ANamespaceAndSomeone()

    @override
    def when(
        self,
    ) -> When[ANamespaceAndACaller, StorageNamespaceAdapter, UnregisterStorageNamespacePayload]:
        return Unregistering()

    @override
    def then(
        self,
    ) -> Then[ANamespaceAndACaller, UnregisterStorageNamespacePayload]:
        return TheCallIsRefused(GenericBadRequest)


SCENARIOS: list[UnregisteringStep] = [
    AUserGrantedReadAndDeleteUnregisters(),
    ANamespaceNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotUnregister(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_unregistering(
    scenario: UnregisteringStep,
    adapter: StorageNamespaceAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
