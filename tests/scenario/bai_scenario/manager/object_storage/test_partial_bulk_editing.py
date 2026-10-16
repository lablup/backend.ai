"""object storage 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.object_storage.request import (
    PartialBulkUpdateObjectStoragesInput,
    UpdateObjectStorageInput,
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

MOVED = "moved.object-storage.test"

type Edited = PartialBulkPayload[ObjectStorageNode]
type EditingStep = Scenario[
    TestSeedingSession, ManyStoragesAndACaller, ObjectStorageAdapter, Edited
]


@dataclass(frozen=True)
class EditingEveryHost(When[ManyStoragesAndACaller, ObjectStorageAdapter, Edited]):
    """미리 만들어 둔 object storage 들의 호스트를 한 번에 바꾼다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyStoragesAndACaller) -> str:
        return f"{laid.caller.username}이 object storage {len(laid.laid)}개의 호스트를 한 번에 수정"

    @override
    async def call(self, adapter: ObjectStorageAdapter, laid: ManyStoragesAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateObjectStoragesInput(
                    items=[UpdateObjectStorageInput(id=one.id, host=MOVED) for one in laid.laid]
                )
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralStorages(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, ObjectStorageAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-object-storages-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 object storage 여럿의 호스트를 한 번에 바꾸면, 모두 새 호스트로 오고 "
            "실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyStoragesAndACaller, ObjectStorageAdapter, Edited]:
        return EditingEveryHost()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Edited]:
        return EveryStorageIsProcessed(host=MOVED)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, ObjectStorageAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-object-storages"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 고치려 하면, 고쳐진 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone()

    @override
    def when(self) -> When[ManyStoragesAndACaller, ObjectStorageAdapter, Edited]:
        return EditingEveryHost()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralStorages(),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: ObjectStorageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
