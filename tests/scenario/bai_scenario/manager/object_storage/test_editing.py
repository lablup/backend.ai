"""object storage 수정."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.object_storage.request import UpdateObjectStorageInput
from ai.backend.common.dto.manager.v2.object_storage.response import ObjectStorageNode
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.object_storage import (
    AStorageAndACaller,
    AStorageAndSomeone,
    TheStorageNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MOVED = "moved.object-storage.test"

type EditingStep = Scenario[TestSeedingSession, Any, ObjectStorageAdapter, ObjectStorageNode]


@dataclass(frozen=True)
class EditingTheHost(When[AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]):
    """미리 만들어 둔 object storage 의 호스트를 바꾼다. 응답에 담긴 노드를 꺼내서 준다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AStorageAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else laid.storage.name
        return f"{laid.caller.username}이 {target}의 호스트 수정"

    @override
    async def call(
        self, adapter: ObjectStorageAdapter, laid: AStorageAndACaller
    ) -> ObjectStorageNode:
        storage_id = ObjectStorageID(uuid4()) if self.unknown else laid.storage.id
        with ActingAs(laid.caller):
            payload = await adapter.update(
                storage_id, UpdateObjectStorageInput(id=storage_id, host=MOVED)
            )
        return payload.object_storage


@dataclass(frozen=True)
class TheSuperadminMovesTheHost(
    Scenario[TestSeedingSession, AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-changes-the-host-of-an-object-storage"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 호스트만 바꾸면, 호스트는 새 값이 되고 나머지는 그대로 남는다"

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]:
        return EditingTheHost()

    @override
    def then(self) -> Then[AStorageAndACaller, ObjectStorageNode]:
        return TheStorageNode(host=MOVED)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]:
        return EditingTheHost(unknown=True)

    @override
    def then(self) -> Then[AStorageAndACaller, ObjectStorageNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-an-object-storage"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 object storage 를 수정하면 권한 부족으로 거부된다. "
            "object storage 는 global 에만 속해 그 권한을 받을 방법이 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone()

    @override
    def when(self) -> When[AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]:
        return EditingTheHost()

    @override
    def then(self) -> Then[AStorageAndACaller, ObjectStorageNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[EditingStep] = [
    TheSuperadminMovesTheHost(),
    TheSuperadminEditingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: ObjectStorageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
