"""object storage 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.object_storage.request import (
    PartialBulkPurgeObjectStoragesInput,
)
from ai.backend.common.dto.manager.v2.object_storage.response import ObjectStorageNode
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.object_storage import (
    EveryStorageIsProcessed,
    ManyStoragesAndACaller,
    ManyStoragesAndSomeone,
    NothingIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[ObjectStorageNode]
type PurgingStep = Scenario[
    TestSeedingSession, ManyStoragesAndACaller, ObjectStorageAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryStorage(When[ManyStoragesAndACaller, ObjectStorageAdapter, Purged]):
    """미리 만들어 둔 object storage 들을 한 번에 purge 한다. ``missing``이 있으면 그 id 도 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyStoragesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return (
            f"{laid.caller.username}이 object storage {len(laid.laid)}개{besides}를 한 번에 purge"
        )

    @override
    async def call(self, adapter: ObjectStorageAdapter, laid: ManyStoragesAndACaller) -> Purged:
        ids: list[UUID] = [one.id for one in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeObjectStoragesInput(ids=ids))


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, ObjectStorageAdapter, Purged]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "the-superadmin-purges-several-object-storages-and-a-missing-id"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 object storage 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 된 "
            "목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyStoragesAndACaller, ObjectStorageAdapter, Purged]:
        return PurgingEveryStorage(missing=self.missing)

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Purged]:
        return EveryStorageIsProcessed(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, ObjectStorageAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-object-storages"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 purge 하려 하면, purge "
            "된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone()

    @override
    def when(self) -> When[ManyStoragesAndACaller, ObjectStorageAdapter, Purged]:
        return PurgingEveryStorage()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Purged]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: ObjectStorageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
