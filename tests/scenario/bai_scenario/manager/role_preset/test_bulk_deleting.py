"""프리셋 여럿 bulk soft delete, restore, purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkDeleteRolePresetsInput,
    BulkPurgeRolePresetsInput,
    BulkRestoreRolePresetsInput,
)
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.role_preset import (
    BulkPresetsPayload,
    EveryBulkTargetComesBack,
    ManyPresetsAndACaller,
    ManyPresetsAndAGrantedCaller,
    ManyPresetsAndSomeone,
    NoBulkTargetProcessed,
    PresetLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type DeletingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload
]


@dataclass(frozen=True)
class BulkSoftDeleting(When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]):
    """대상 프리셋들을 한 번에 soft delete 한다."""

    @override
    def operation(self) -> str:
        return "bulk_delete"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개를 한 번에 soft delete 합니다",
            english=f"{laid.caller.username} soft deletes {len(laid.laid)} presets at once",
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller
    ) -> BulkPresetsPayload:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        with ActingAs(laid.caller):
            return await adapter.bulk_delete(BulkDeleteRolePresetsInput(role_preset_ids=ids))


@dataclass(frozen=True)
class BulkRestoring(When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]):
    """대상 프리셋들을 한 번에 restore 한다."""

    @override
    def operation(self) -> str:
        return "bulk_restore"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개를 한 번에 restore 합니다",
            english=f"{laid.caller.username} restores {len(laid.laid)} presets at once",
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller
    ) -> BulkPresetsPayload:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        with ActingAs(laid.caller):
            return await adapter.bulk_restore(BulkRestoreRolePresetsInput(role_preset_ids=ids))


@dataclass(frozen=True)
class BulkSoftDeletingThenRestoring(
    When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]
):
    """대상 프리셋들을 한 번에 soft delete 했다가 한 번에 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "bulk_restore"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개를 한 번에 soft delete 한 뒤 "
            "한 번에 restore 합니다",
            english=(
                f"{laid.caller.username} soft deletes {len(laid.laid)} presets at once "
                "and then restores them at once"
            ),
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller
    ) -> BulkPresetsPayload:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        with ActingAs(laid.caller):
            await adapter.bulk_delete(BulkDeleteRolePresetsInput(role_preset_ids=ids))
            return await adapter.bulk_restore(BulkRestoreRolePresetsInput(role_preset_ids=ids))


@dataclass(frozen=True)
class BulkPurging(When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]):
    """대상 프리셋들을 한 번에 purge 한다."""

    @override
    def operation(self) -> str:
        return "bulk_purge"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개를 한 번에 purge 합니다",
            english=f"{laid.caller.username} purges {len(laid.laid)} presets at once",
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller
    ) -> BulkPresetsPayload:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        with ActingAs(laid.caller):
            return await adapter.bulk_purge(BulkPurgeRolePresetsInput(role_preset_ids=ids))


@dataclass(frozen=True)
class AUserGrantedSoftDeleteBulkSoftDeletesPresets(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-bulk-soft-deletes-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋에 soft_delete 권한을 받은 사용자가 프리셋 여럿을 한 번에 soft delete 하면, "
            "모두 삭제로 표시된 채 옵니다",
            english=(
                "when a user granted soft_delete on role presets bulk soft deletes several "
                "presets, all of them come back marked deleted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndAGrantedCaller(granted=(Permission.SOFT_DELETE,))

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]:
        return BulkSoftDeleting()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, BulkPresetsPayload]:
        return EveryBulkTargetComesBack(PresetLook(self.started, deleted=True))


@dataclass(frozen=True)
class AUserGrantedNothingBulkSoftDeletesNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-bulk-soft-deletes-none-of-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 soft delete 하려 하면, "
            "soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to bulk soft delete several presets, "
                "none is soft-deleted and every one comes back in the failed list for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]:
        return BulkSoftDeleting()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, BulkPresetsPayload]:
        return NoBulkTargetProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class AUserGrantedSoftDeleteBulkRestoresPresets(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-bulk-restores-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋에 soft_delete 권한을 받은 사용자가 프리셋 여럿을 한 번에 soft delete 한 뒤 "
            "한 번에 restore 하면, 모두 삭제로 표시되지 않은 채 옵니다",
            english=(
                "when a user granted soft_delete on role presets bulk soft deletes several "
                "presets and then bulk restores them, all of them come back not marked deleted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndAGrantedCaller(granted=(Permission.SOFT_DELETE,))

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]:
        return BulkSoftDeletingThenRestoring()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, BulkPresetsPayload]:
        return EveryBulkTargetComesBack(PresetLook(self.started))


@dataclass(frozen=True)
class AUserGrantedNothingBulkRestoresNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-bulk-restores-none-of-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 restore 하려 하면, "
            "restore 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to bulk restore several presets, "
                "none is restored and every one comes back in the failed list for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]:
        return BulkRestoring()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, BulkPresetsPayload]:
        return NoBulkTargetProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class AUserGrantedHardDeleteBulkPurgesPresets(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-bulk-purges-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋에 hard_delete 권한을 받은 사용자가 프리셋 여럿을 한 번에 purge 하면, "
            "모두 purge 하기 전의 모습으로 옵니다",
            english=(
                "when a user granted hard_delete on role presets bulk purges several presets, "
                "all of them come back as they were before the purge"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndAGrantedCaller(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]:
        return BulkPurging()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, BulkPresetsPayload]:
        return EveryBulkTargetComesBack(PresetLook(self.started))


@dataclass(frozen=True)
class AUserGrantedNothingBulkPurgesNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-bulk-purges-none-of-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, "
            "purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to bulk purge several presets, "
                "none is purged and every one comes back in the failed list for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, BulkPresetsPayload]:
        return BulkPurging()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, BulkPresetsPayload]:
        return NoBulkTargetProcessed(reason="Insufficient permission")


SCENARIOS: list[DeletingStep] = [
    AUserGrantedSoftDeleteBulkSoftDeletesPresets(started=datetime.now(UTC)),
    AUserGrantedNothingBulkSoftDeletesNone(),
    AUserGrantedSoftDeleteBulkRestoresPresets(started=datetime.now(UTC)),
    AUserGrantedNothingBulkRestoresNone(),
    AUserGrantedHardDeleteBulkPurgesPresets(started=datetime.now(UTC)),
    AUserGrantedNothingBulkPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_deleting(
    scenario: DeletingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
