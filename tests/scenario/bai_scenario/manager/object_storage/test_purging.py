"""object storage purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.object_storage.response import PurgeObjectStoragePayload
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.object_storage import (
    AStorageAndACaller,
    AStorageAndSomeone,
    ThePurgedStorageId,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PurgingStep = Scenario[
    TestSeedingSession, Any, ObjectStorageAdapter, PurgeObjectStoragePayload
]


@dataclass(frozen=True)
class Purging(When[AStorageAndACaller, ObjectStorageAdapter, PurgeObjectStoragePayload]):
    """미리 만들어 둔 object storage 하나를 purge 한다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AStorageAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else laid.storage.name
        return f"{laid.caller.username}이 {target} purge"

    @override
    async def call(
        self, adapter: ObjectStorageAdapter, laid: AStorageAndACaller
    ) -> PurgeObjectStoragePayload:
        storage_id = ObjectStorageID(uuid4()) if self.unknown else laid.storage.id
        with ActingAs(laid.caller):
            return await adapter.purge(storage_id)


@dataclass(frozen=True)
class TheSuperadminPurgesAStorage(
    Scenario[
        TestSeedingSession, AStorageAndACaller, ObjectStorageAdapter, PurgeObjectStoragePayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-an-object-storage"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 object storage 를 purge 하면 purge 한 것의 id 가 반환된다"

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AStorageAndACaller, ObjectStorageAdapter, PurgeObjectStoragePayload]:
        return Purging()

    @override
    def then(self) -> Then[AStorageAndACaller, PurgeObjectStoragePayload]:
        return ThePurgedStorageId()


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[
        TestSeedingSession, AStorageAndACaller, ObjectStorageAdapter, PurgeObjectStoragePayload
    ]
):
    @override
    def summary(self) -> str:
        return "purging-an-object-storage-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 purge 하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AStorageAndACaller, ObjectStorageAdapter, PurgeObjectStoragePayload]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[AStorageAndACaller, PurgeObjectStoragePayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[
        TestSeedingSession, AStorageAndACaller, ObjectStorageAdapter, PurgeObjectStoragePayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-an-object-storage"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 object storage 를 purge 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone()

    @override
    def when(self) -> When[AStorageAndACaller, ObjectStorageAdapter, PurgeObjectStoragePayload]:
        return Purging()

    @override
    def then(self) -> Then[AStorageAndACaller, PurgeObjectStoragePayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesAStorage(),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotPurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: ObjectStorageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
