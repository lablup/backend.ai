"""object storage 아래에 네임스페이스 하나 등록하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    RegisterStorageNamespaceInput,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    RegisterStorageNamespacePayload,
    StorageNamespaceNode,
)
from ai.backend.manager.api.adapters.storage_namespace.adapter import StorageNamespaceAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.storage_namespace import AStorageAndACaller, AStorageAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

REGISTERED = "registered-bucket"

type RegisteringStep = Scenario[
    TestSeedingSession,
    AStorageAndACaller,
    StorageNamespaceAdapter,
    RegisterStorageNamespacePayload,
]


@dataclass(frozen=True)
class Registering(
    When[AStorageAndACaller, StorageNamespaceAdapter, RegisterStorageNamespacePayload]
):
    @override
    def operation(self) -> str:
        return "register"

    @override
    def describe(self, laid: AStorageAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.storage.name}에 네임스페이스를 등록합니다",
            english=f"{laid.caller.username} registers a namespace on {laid.storage.name}",
        )

    @override
    async def call(
        self, adapter: StorageNamespaceAdapter, laid: AStorageAndACaller
    ) -> RegisterStorageNamespacePayload:
        with ActingAs(laid.caller):
            return await adapter.register(
                RegisterStorageNamespaceInput(storage_id=laid.storage.id, namespace=REGISTERED)
            )


@dataclass(frozen=True)
class TheRegisteredNamespaceNode(Then[AStorageAndACaller, RegisterStorageNamespacePayload]):
    @override
    def says(self) -> str:
        return Says(
            "등록한 네임스페이스 전체가 반환됩니다",
            english="the whole registered namespace comes back",
        )

    @override
    def look(
        self, laid: AStorageAndACaller, answered: Answered[RegisterStorageNamespacePayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node: StorageNamespaceNode = payload.namespace
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Skipped(
                "entity_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Same("storage_id", node.storage_id, laid.storage.id),
            Same("namespace", node.namespace, REGISTERED),
        ]


@dataclass(frozen=True)
class TheSuperadminRegisters(
    Scenario[
        TestSeedingSession,
        AStorageAndACaller,
        StorageNamespaceAdapter,
        RegisterStorageNamespacePayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-registers-a-namespace-on-an-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 object storage 에 네임스페이스를 등록하면 등록한 네임스페이스 전체가 "
            "반환됩니다. 이 호출은 전역 역할을 검사합니다",
            english=(
                "when the superadmin registers a namespace on an object storage, the whole "
                "registered namespace comes back. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AStorageAndACaller, StorageNamespaceAdapter, RegisterStorageNamespacePayload]:
        return Registering()

    @override
    def then(self) -> Then[AStorageAndACaller, RegisterStorageNamespacePayload]:
        return TheRegisteredNamespaceNode()


@dataclass(frozen=True)
class APlainUserMayNotRegister(
    Scenario[
        TestSeedingSession,
        AStorageAndACaller,
        StorageNamespaceAdapter,
        RegisterStorageNamespacePayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-register-a-namespace"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 네임스페이스를 등록하려 하면 권한 부족으로 거부됩니다. "
            "이 호출은 전역 역할을 검사합니다",
            english=(
                "when a user who is not the superadmin tries to register a namespace, it is "
                "rejected for lack of permission. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone()

    @override
    def when(
        self,
    ) -> When[AStorageAndACaller, StorageNamespaceAdapter, RegisterStorageNamespacePayload]:
        return Registering()

    @override
    def then(self) -> Then[AStorageAndACaller, RegisterStorageNamespacePayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[RegisteringStep] = [
    TheSuperadminRegisters(),
    APlainUserMayNotRegister(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_registering(
    scenario: RegisteringStep,
    adapter: StorageNamespaceAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
