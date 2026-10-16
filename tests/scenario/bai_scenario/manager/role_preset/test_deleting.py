"""프리셋 soft delete, restore, purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    PresetLook,
    ThePresetComesBack,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type DeletingStep = Scenario[
    TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode
]


@dataclass(frozen=True)
class SoftDeleting(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """프리셋을 soft delete 한다."""

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.preset.name}을 soft delete 함"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            return (await adapter.delete(laid.preset.id)).role_preset


@dataclass(frozen=True)
class SoftDeletingThenRestoring(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """soft delete 한 다음 restore 한다. restore 의 답을 준다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.preset.name}을 soft delete 했다가 restore 함"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            await adapter.delete(laid.preset.id)
            return (await adapter.restore(laid.preset.id)).role_preset


@dataclass(frozen=True)
class Restoring(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """프리셋을 restore 한다."""

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.preset.name}을 restore 함"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            return (await adapter.restore(laid.preset.id)).role_preset


@dataclass(frozen=True)
class Purging(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """프리셋을 purge 한다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.preset.name}을 purge 함"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            return (await adapter.purge(laid.preset.id)).role_preset


@dataclass(frozen=True)
class TheSuperadminSoftDeletesIt(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-soft-deletes-a-preset"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 프리셋을 soft delete 하면, 삭제 표시가 켜진 프리셋 전체가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return SoftDeleting()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return ThePresetComesBack(PresetLook(self.started, deleted=True))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSoftDelete(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-soft-delete-a-preset"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 프리셋을 soft delete 하려 하면, 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return SoftDeleting()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RestoringBringsItBack(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-a-soft-deleted-preset-brings-it-back"

    @override
    def describe(self) -> str:
        return "soft delete 된 프리셋을 restore 하면, 삭제 표시가 꺼진 프리셋 전체가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return SoftDeletingThenRestoring()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return ThePresetComesBack(PresetLook(self.started))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestore(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-a-preset"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 프리셋을 restore 하려 하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Restoring()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminPurgesIt(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-preset"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 프리셋을 purge 하면, purge 하기 전의 프리셋 전체가 온다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Purging()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return ThePresetComesBack(PresetLook(self.started))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-preset"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 프리셋을 purge 하려 하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Purging()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[DeletingStep] = [
    TheSuperadminSoftDeletesIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSoftDelete(),
    RestoringBringsItBack(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRestore(),
    TheSuperadminPurgesIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotPurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deleting(
    scenario: DeletingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
