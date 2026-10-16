"""프리셋 권한 항목 넣기, 빼기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    PartialBulkRemoveRolePresetPermissionsInput,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    RolePermissionPresetNode,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
    RolePermissionPresetEntry,
)
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    ENTRIES,
    APresetAndACaller,
    APresetAndSomeone,
    APresetWithEntriesAndACaller,
    APresetWithEntriesAndSomeone,
    NothingIsProcessed,
    TheEntriesAreAdded,
    TheEntriesAreRemoved,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Added = list[RolePermissionPresetNode]
type Removed = PartialBulkPayload[RolePermissionPresetNode]
type PermissionStep = Scenario[TestSeedingSession, Any, RolePresetAdapter, Any]

MISSING = UUID(int=1)


@dataclass(frozen=True)
class AddingTwoEntries(When[APresetAndACaller, RolePresetAdapter, Added]):
    """권한 항목 둘을 한 번에 넣는다."""

    @override
    def operation(self) -> str:
        return "atomic_bulk_add_permissions"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.preset.name}에 권한 항목 {len(ENTRIES)}개를 넣음"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> Added:
        entries = [
            RolePermissionPresetEntry.model_validate({
                "entity_type": entity_type,
                "permission": permission,
            })
            for entity_type, permission in ENTRIES
        ]
        with ActingAs(laid.caller):
            payload = await adapter.atomic_bulk_add_permissions(
                laid.preset.id, BulkAddRolePermissionPresetsInput(permissions=entries)
            )
        return payload.items


@dataclass(frozen=True)
class RemovingEveryEntry(When[APresetWithEntriesAndACaller, RolePresetAdapter, Removed]):
    """프리셋의 권한 항목을 한 번에 뺀다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_remove_permissions"

    @override
    def describe(self, laid: APresetWithEntriesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return (
            f"{laid.caller.username}이 {laid.preset.name}의 권한 항목 "
            f"{len(laid.entries)}개{besides}를 한 번에 뺌"
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetWithEntriesAndACaller) -> Removed:
        ids: list[UUID] = [entry.id for entry in laid.entries]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_remove_permissions(
                PartialBulkRemoveRolePresetPermissionsInput(ids=ids)
            )


@dataclass(frozen=True)
class TheSuperadminAddsEntries(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, Added]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-adds-entries-to-a-preset"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 항목 없는 프리셋에 권한 항목 둘을 넣으면, 넣은 두 항목이 그 프리셋 아래에 온다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, Added]:
        return AddingTwoEntries()

    @override
    def then(self) -> Then[APresetAndACaller, Added]:
        return TheEntriesAreAdded(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAddEntries(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, Added]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-add-entries"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 프리셋에 권한 항목을 넣으려 하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, Added]:
        return AddingTwoEntries()

    @override
    def then(self) -> Then[APresetAndACaller, Added]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RemovingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, APresetWithEntriesAndACaller, RolePresetAdapter, Removed]
):
    @override
    def summary(self) -> str:
        return "removing-entries-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 권한 항목 둘과 없는 id 하나를 한 번에 빼면, 둘은 처리된 목록에 오고 "
            "없는 id 는 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetWithEntriesAndACaller]:
        return APresetWithEntriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetWithEntriesAndACaller, RolePresetAdapter, Removed]:
        return RemovingEveryEntry(missing=MISSING)

    @override
    def then(self) -> Then[APresetWithEntriesAndACaller, Removed]:
        return TheEntriesAreRemoved(missing=MISSING)


@dataclass(frozen=True)
class AUserGrantedNothingRemovesNone(
    Scenario[TestSeedingSession, APresetWithEntriesAndACaller, RolePresetAdapter, Removed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-removes-none-of-the-entries"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 권한 항목 여럿을 한 번에 빼려 하면, "
            "뺀 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetWithEntriesAndACaller]:
        return APresetWithEntriesAndSomeone()

    @override
    def when(self) -> When[APresetWithEntriesAndACaller, RolePresetAdapter, Removed]:
        return RemovingEveryEntry()

    @override
    def then(self) -> Then[APresetWithEntriesAndACaller, Removed]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PermissionStep] = [
    TheSuperadminAddsEntries(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotAddEntries(),
    RemovingAnswersForTheMissingOne(),
    AUserGrantedNothingRemovesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_permission_editing(
    scenario: PermissionStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
