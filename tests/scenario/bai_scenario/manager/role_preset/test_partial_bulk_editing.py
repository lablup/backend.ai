"""프리셋 여럿 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.role_preset.request import (
    PartialBulkUpdateRolePresetItemInput,
    PartialBulkUpdateRolePresetsInput,
    UpdateRolePresetBody,
)
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.role_preset import (
    AProjectAndADomainPresetAndSomeone,
    EveryTargetComesBack,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NothingIsProcessed,
    OnlyTheFirstPresetComesBack,
    PresetLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Edited = PartialBulkPayload[RolePresetNode]
type EditingStep = Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]


@dataclass(frozen=True)
class TurningAutoAssignOnForEvery(When[ManyPresetsAndACaller, RolePresetAdapter, Edited]):
    """대상 프리셋 모두의 자동 부여를 한 번에 켠다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개의 자동 부여를 한 번에 켭니다",
            english=(
                f"{laid.caller.username} turns auto assign on for {len(laid.laid)} presets at once"
            ),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Edited:
        items = [
            PartialBulkUpdateRolePresetItemInput(
                id=preset.id, input=UpdateRolePresetBody(auto_assign=True)
            )
            for preset in laid.laid
        ]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(PartialBulkUpdateRolePresetsInput(items=items))


@dataclass(frozen=True)
class TurningOwnerAssignOnForEvery(When[ManyPresetsAndACaller, RolePresetAdapter, Edited]):
    """대상 프리셋 모두의 소유자 부여를 한 번에 켠다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 프리셋 {len(laid.laid)}개의 소유자 부여를 한 번에 켬"

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Edited:
        items = [
            PartialBulkUpdateRolePresetItemInput(
                id=preset.id, input=UpdateRolePresetBody(auto_assign_to_owner=True)
            )
            for preset in laid.laid
        ]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(PartialBulkUpdateRolePresetsInput(items=items))


@dataclass(frozen=True)
class TheSuperadminEditsSeveral(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-presets-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 프리셋 여럿의 자동 부여를 한 번에 켜면, 모두 새 값으로 오고 "
            "실패한 것은 없습니다",
            english=(
                "when the superadmin turns auto assign on for several presets at once, "
                "all of them come back with the new value and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Edited]:
        return TurningAutoAssignOnForEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return EveryTargetComesBack(PresetLook(self.started, auto_assign=True))


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 수정하려 하면, "
            "수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to edit several presets at once, "
                "none is edited and every one comes back in the failed list for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Edited]:
        return TurningAutoAssignOnForEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class OnlyTheProjectPresetTakesOwnerAssign(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "only-the-project-preset-takes-owner-assign"

    @override
    def describe(self) -> str:
        return (
            "프로젝트 스코프와 도메인 스코프 프리셋의 소유자 부여를 한 번에 켜면, "
            "프로젝트 스코프 프리셋만 고쳐지고 도메인 스코프 프리셋은 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return AProjectAndADomainPresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Edited]:
        return TurningOwnerAssignOnForEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return OnlyTheFirstPresetComesBack(PresetLook(self.started, auto_assign_to_owner=True))


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveral(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
    OnlyTheProjectPresetTakesOwnerAssign(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
