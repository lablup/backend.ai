"""object storage 하나 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.object_storage.request import CreateObjectStorageInput
from ai.backend.common.dto.manager.v2.object_storage.response import (
    CreateObjectStoragePayload,
    ObjectStorageNode,
)
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
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
from bai_scenario.components.system import ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

NAME = "made-object-storage"
HOST = "made.object-storage.test"

type CreatingStep = Scenario[
    TestSeedingSession, ACaller, ObjectStorageAdapter, CreateObjectStoragePayload
]


@dataclass(frozen=True)
class Creating(When[ACaller, ObjectStorageAdapter, CreateObjectStoragePayload]):
    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACaller) -> str:
        return Says(
            f"{laid.caller.username}이 object storage 를 만듭니다",
            english=f"{laid.caller.username} creates an object storage",
        )

    @override
    async def call(
        self, adapter: ObjectStorageAdapter, laid: ACaller
    ) -> CreateObjectStoragePayload:
        with ActingAs(laid.caller):
            return await adapter.create(
                CreateObjectStorageInput(
                    name=NAME,
                    host=HOST,
                    access_key="made-access-key",
                    secret_key="made-secret-key",
                    endpoint="https://made.object-storage.test",
                    region="made-region",
                )
            )


@dataclass(frozen=True)
class TheNewStorageNode(Then[ACaller, CreateObjectStoragePayload]):
    @override
    def says(self) -> str:
        return Says(
            "만든 object storage 전체가 반환됩니다",
            english="the whole created object storage comes back",
        )

    @override
    def look(self, laid: ACaller, answered: Answered[CreateObjectStoragePayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node: ObjectStorageNode = payload.object_storage
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Skipped(
                "entity_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Same("name", node.name, NAME),
            Same("host", node.host, HOST),
            Same("access_key", node.access_key, "made-access-key"),
            Same("secret_key", node.secret_key, "made-secret-key"),
            Same("endpoint", node.endpoint, "https://made.object-storage.test"),
            Same("region", node.region, "made-region"),
        ]


@dataclass(frozen=True)
class TheSuperadminCreatesAStorage(
    Scenario[TestSeedingSession, ACaller, ObjectStorageAdapter, CreateObjectStoragePayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-creates-an-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 object storage 를 만들면 만든 object storage 전체가 반환됩니다. 이 "
            "호출은 전역 역할을 검사합니다",
            english=(
                "when the superadmin creates an object storage, the whole created one comes back. "
                "This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ObjectStorageAdapter, CreateObjectStoragePayload]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, CreateObjectStoragePayload]:
        return TheNewStorageNode()


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[TestSeedingSession, ACaller, ObjectStorageAdapter, CreateObjectStoragePayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-an-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 object storage 를 만들려 하면 권한 부족으로 거부됩니다. "
            "이 호출은 전역 역할을 검사합니다",
            english=(
                "when a user who is not the superadmin tries to create an object storage, it is "
                "rejected for lack of permission. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, ObjectStorageAdapter, CreateObjectStoragePayload]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, CreateObjectStoragePayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminCreatesAStorage(),
    APlainUserMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep,
    adapter: ObjectStorageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
