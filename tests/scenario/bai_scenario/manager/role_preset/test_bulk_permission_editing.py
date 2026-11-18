"""프리셋 권한 항목 넣기, 빼기: 옛 응답 모양."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkRemoveRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkAddRolePermissionPresetsPayload,
    BulkRemoveRolePermissionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
    RolePermissionPresetEntry,
)
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.role_preset import RolePermissionPresetConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    ENTRIES,
    APresetAndACaller,
    APresetAndSomeone,
    APresetWithEntriesAndACaller,
    APresetWithEntriesAndSomeone,
    NothingIsRemovedInBulk,
    TheEntriesAreAddedInBulk,
    TheEntriesAreRemovedInBulk,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type BulkStep = Scenario[TestSeedingSession, Any, RolePresetAdapter, Any]


@dataclass(frozen=True)
class AddingTwoEntries(When[Any, RolePresetAdapter, BulkAddRolePermissionPresetsPayload]):
    """권한 항목 둘을 한 번에 넣는다."""

    @override
    def operation(self) -> str:
        return "bulk_add_permissions"

    @override
    def describe(self, laid: Any) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.preset.name}에 권한 항목 {len(ENTRIES)}개를 추가합니다",
            english=(
                f"{laid.caller.username} adds {len(ENTRIES)} permission entries "
                f"to {laid.preset.name}"
            ),
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: Any
    ) -> BulkAddRolePermissionPresetsPayload:
        entries = [
            RolePermissionPresetEntry.model_validate({
                "entity_type": entity_type,
                "permission": permission,
            })
            for entity_type, permission in ENTRIES
        ]
        with ActingAs(laid.caller):
            return await adapter.bulk_add_permissions(
                laid.preset.id, BulkAddRolePermissionPresetsInput(permissions=entries)
            )


@dataclass(frozen=True)
class RemovingEveryEntry(
    When[APresetWithEntriesAndACaller, RolePresetAdapter, BulkRemoveRolePermissionPresetsPayload]
):
    """프리셋의 권한 항목을 한 번에 뺀다."""

    @override
    def operation(self) -> str:
        return "bulk_remove_permissions"

    @override
    def describe(self, laid: APresetWithEntriesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.preset.name}의 권한 항목 "
            f"{len(laid.entries)}개를 한 번에 제거합니다",
            english=(
                f"{laid.caller.username} removes {len(laid.entries)} permission entries "
                f"from {laid.preset.name} at once"
            ),
        )

    @override
    async def call(
        self, adapter: RolePresetAdapter, laid: APresetWithEntriesAndACaller
    ) -> BulkRemoveRolePermissionPresetsPayload:
        with ActingAs(laid.caller):
            return await adapter.bulk_remove_permissions(
                BulkRemoveRolePermissionPresetsInput(
                    permission_preset_ids=[entry.id for entry in laid.entries]
                )
            )


@dataclass(frozen=True)
class AUserGrantedUpdateAddsEntries(
    Scenario[
        TestSeedingSession,
        APresetAndACaller,
        RolePresetAdapter,
        BulkAddRolePermissionPresetsPayload,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-adds-entries-in-bulk"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 수정 권한을 받은 사용자가 항목 없는 프리셋에 권한 항목 둘을 추가하면, "
            "추가한 두 항목이 그 프리셋 아래에 오고 실패한 항목은 없습니다",
            english=(
                "when a user granted update on presets adds two permission entries to a "
                "preset that has none, the two entries added come back under the preset "
                "and none failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(granted=Permission.UPDATE)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RolePresetAdapter, BulkAddRolePermissionPresetsPayload]:
        return AddingTwoEntries()

    @override
    def then(self) -> Then[APresetAndACaller, BulkAddRolePermissionPresetsPayload]:
        return TheEntriesAreAddedInBulk(started=self.started)


@dataclass(frozen=True)
class AUserWithoutUpdateMayNotAddEntries(
    Scenario[
        TestSeedingSession,
        APresetAndACaller,
        RolePresetAdapter,
        BulkAddRolePermissionPresetsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-without-update-may-not-add-entries-in-bulk"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 읽기 권한만 받은 사용자가 프리셋에 권한 항목을 추가하려 하면, "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read on presets tries to add permission entries "
                "to a preset, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(granted=Permission.READ)

    @override
    def when(
        self,
    ) -> When[APresetAndACaller, RolePresetAdapter, BulkAddRolePermissionPresetsPayload]:
        return AddingTwoEntries()

    @override
    def then(self) -> Then[APresetAndACaller, BulkAddRolePermissionPresetsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnEntryAlreadyThereIsRefused(
    Scenario[
        TestSeedingSession,
        APresetWithEntriesAndACaller,
        RolePresetAdapter,
        BulkAddRolePermissionPresetsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "an-entry-already-there-is-refused-in-bulk"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 수정 권한을 받은 사용자가 프리셋에 이미 있는 권한 항목을 다시 추가하려 하면, "
            "항목이 겹쳐 거부됩니다",
            english=(
                "when a user granted update on presets adds permission entries a preset "
                "already has, it is rejected as an entry conflict"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetWithEntriesAndACaller]:
        return APresetWithEntriesAndSomeone(granted=Permission.UPDATE)

    @override
    def when(
        self,
    ) -> When[APresetWithEntriesAndACaller, RolePresetAdapter, BulkAddRolePermissionPresetsPayload]:
        return AddingTwoEntries()

    @override
    def then(self) -> Then[APresetWithEntriesAndACaller, BulkAddRolePermissionPresetsPayload]:
        return TheCallIsRefused(RolePermissionPresetConflict)


@dataclass(frozen=True)
class AUserGrantedUpdateRemovesEntries(
    Scenario[
        TestSeedingSession,
        APresetWithEntriesAndACaller,
        RolePresetAdapter,
        BulkRemoveRolePermissionPresetsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-removes-entries-in-bulk"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 수정 권한을 받은 사용자가 권한 항목 둘을 한 번에 제거하면, "
            "제거한 두 항목이 모두 오고 실패한 항목은 없습니다",
            english=(
                "when a user granted update on presets removes two permission entries at "
                "once, the two entries removed come back and none failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetWithEntriesAndACaller]:
        return APresetWithEntriesAndSomeone(granted=Permission.UPDATE)

    @override
    def when(
        self,
    ) -> When[
        APresetWithEntriesAndACaller, RolePresetAdapter, BulkRemoveRolePermissionPresetsPayload
    ]:
        return RemovingEveryEntry()

    @override
    def then(
        self,
    ) -> Then[APresetWithEntriesAndACaller, BulkRemoveRolePermissionPresetsPayload]:
        return TheEntriesAreRemovedInBulk()


@dataclass(frozen=True)
class AUserWithoutUpdateRemovesNone(
    Scenario[
        TestSeedingSession,
        APresetWithEntriesAndACaller,
        RolePresetAdapter,
        BulkRemoveRolePermissionPresetsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-without-update-removes-none-of-the-entries-in-bulk"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 읽기 권한만 받은 사용자가 권한 항목 여럿을 한 번에 제거하려 하면, "
            "제거된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted only read on presets tries to remove several "
                "permission entries at once, none is removed and every one comes back in "
                "the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetWithEntriesAndACaller]:
        return APresetWithEntriesAndSomeone(granted=Permission.READ)

    @override
    def when(
        self,
    ) -> When[
        APresetWithEntriesAndACaller, RolePresetAdapter, BulkRemoveRolePermissionPresetsPayload
    ]:
        return RemovingEveryEntry()

    @override
    def then(
        self,
    ) -> Then[APresetWithEntriesAndACaller, BulkRemoveRolePermissionPresetsPayload]:
        return NothingIsRemovedInBulk(reason="Insufficient permission")


SCENARIOS: list[BulkStep] = [
    AUserGrantedUpdateAddsEntries(started=datetime.now(UTC)),
    AUserWithoutUpdateMayNotAddEntries(),
    AnEntryAlreadyThereIsRefused(),
    AUserGrantedUpdateRemovesEntries(),
    AUserWithoutUpdateRemovesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_permission_editing(
    scenario: BulkStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
