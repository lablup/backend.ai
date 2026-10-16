"""프리셋 여럿 soft delete, restore, purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.role_preset.request import (
    PartialBulkDeleteRolePresetsInput,
    PartialBulkPurgeRolePresetsInput,
    PartialBulkRestoreRolePresetsInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.role_preset import (
    EveryTargetComesBack,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NothingIsProcessed,
    PresetLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = PartialBulkPayload[RolePresetNode]
type DeletingStep = Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Deleted]

MISSING = UUID(int=1)


@dataclass(frozen=True)
class SoftDeletingEvery(When[ManyPresetsAndACaller, RolePresetAdapter, Deleted]):
    """대상 프리셋들을 한 번에 soft delete 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_delete"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return (
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개{besides}를 한 번에 soft delete 함"
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Deleted:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_delete(PartialBulkDeleteRolePresetsInput(ids=ids))


@dataclass(frozen=True)
class SoftDeletingThenRestoringEvery(When[ManyPresetsAndACaller, RolePresetAdapter, Deleted]):
    """대상 프리셋들을 한 번에 soft delete 했다가 한 번에 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_restore"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return (
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개를 한 번에 soft delete "
            "했다가 한 번에 restore 함"
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Deleted:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        with ActingAs(laid.caller):
            await adapter.partial_bulk_delete(PartialBulkDeleteRolePresetsInput(ids=ids))
            return await adapter.partial_bulk_restore(PartialBulkRestoreRolePresetsInput(ids=ids))


@dataclass(frozen=True)
class PurgingEvery(When[ManyPresetsAndACaller, RolePresetAdapter, Deleted]):
    """대상 프리셋들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 프리셋 {len(laid.laid)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Deleted:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeRolePresetsInput(ids=ids))


@dataclass(frozen=True)
class SoftDeletingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "soft-deleting-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "프리셋 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제 표시가 켜진 채 오고 "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Deleted]:
        return SoftDeletingEvery(missing=MISSING)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Deleted]:
        return EveryTargetComesBack(PresetLook(self.started, deleted=True), missing=MISSING)


@dataclass(frozen=True)
class AUserGrantedNothingSoftDeletesNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-soft-deletes-none-of-several-presets"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 soft delete 하려 하면, "
            "soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Deleted]:
        return SoftDeletingEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Deleted]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class RestoringBringsSeveralBack(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-several-brings-them-back"

    @override
    def describe(self) -> str:
        return "soft delete 된 프리셋 여럿을 한 번에 restore 하면, 모두 삭제 표시가 꺼진 채 온다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Deleted]:
        return SoftDeletingThenRestoringEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Deleted]:
        return EveryTargetComesBack(PresetLook(self.started))


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Deleted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "purging-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 하기 전의 모습으로 오고 "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Deleted]:
        return PurgingEvery(missing=MISSING)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Deleted]:
        return EveryTargetComesBack(PresetLook(self.started), missing=MISSING)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-presets"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, "
            "purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Deleted]:
        return PurgingEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Deleted]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[DeletingStep] = [
    SoftDeletingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingSoftDeletesNone(),
    RestoringBringsSeveralBack(started=datetime.now(UTC)),
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_deleting(
    scenario: DeletingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
