"""VFS storage 하나 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.vfs_storage.request import CreateVFSStorageInput
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    CreateVFSStoragePayload,
    VFSStorageNode,
)
from ai.backend.manager.api.adapters.vfs_storage.adapter import VFSStorageAdapter
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

NAME = "made-vfs-storage"
HOST = "made-host"
BASE_PATH = "/made/vfs-storage"

type CreatingStep = Scenario[
    TestSeedingSession, ACaller, VFSStorageAdapter, CreateVFSStoragePayload
]


@dataclass(frozen=True)
class Creating(When[ACaller, VFSStorageAdapter, CreateVFSStoragePayload]):
    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACaller) -> str:
        return Says(
            f"{laid.caller.username}이 VFS storage 를 만듭니다",
            english=f"{laid.caller.username} creates a VFS storage",
        )

    @override
    async def call(self, adapter: VFSStorageAdapter, laid: ACaller) -> CreateVFSStoragePayload:
        with ActingAs(laid.caller):
            return await adapter.create(
                CreateVFSStorageInput(name=NAME, host=HOST, base_path=BASE_PATH)
            )


@dataclass(frozen=True)
class TheNewStorageNode(Then[ACaller, CreateVFSStoragePayload]):
    @override
    def says(self) -> str:
        return Says(
            "만든 VFS storage 전체가 반환됩니다",
            english="the whole created VFS storage comes back",
        )

    @override
    def look(self, laid: ACaller, answered: Answered[CreateVFSStoragePayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node: VFSStorageNode = payload.vfs_storage
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Skipped(
                "entity_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Same("name", node.name, NAME),
            Same("host", node.host, HOST),
            Same("base_path", node.base_path, BASE_PATH),
        ]


@dataclass(frozen=True)
class TheSuperadminCreatesAStorage(
    Scenario[TestSeedingSession, ACaller, VFSStorageAdapter, CreateVFSStoragePayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-creates-a-vfs-storage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 VFS storage 를 만들면 만든 VFS storage 전체가 반환됩니다",
            english="when the superadmin creates a VFS storage, the whole created one comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, VFSStorageAdapter, CreateVFSStoragePayload]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, CreateVFSStoragePayload]:
        return TheNewStorageNode()


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[TestSeedingSession, ACaller, VFSStorageAdapter, CreateVFSStoragePayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-vfs-storage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 VFS storage 를 만들려 하면 권한 부족으로 거부됩니다. "
            "이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다",
            english=(
                "when a user who is not the superadmin tries to create a VFS storage, it is "
                "rejected for lack of permission. This call checks only whether the caller is "
                "the superadmin and does not look at the permissions granted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, VFSStorageAdapter, CreateVFSStoragePayload]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, CreateVFSStoragePayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminCreatesAStorage(),
    APlainUserMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: VFSStorageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
