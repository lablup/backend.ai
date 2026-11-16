"""프리셋 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.role_preset.request import UpdateRolePresetBody
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.role_preset import RolePresetOwnerAssignNotAllowed
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
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

RENAMED = "renamed-preset"

type EditingStep = Scenario[
    TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode
]


@dataclass(frozen=True)
class Renaming(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """프리셋 이름을 바꾼다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.preset.name}의 이름을 {RENAMED}(으)로 변경합니다",
            english=f"{laid.caller.username} renames {laid.preset.name} to {RENAMED}",
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(laid.preset.id, UpdateRolePresetBody(name=RENAMED))
        return payload.role_preset


@dataclass(frozen=True)
class TurningOwnerAssignOn(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """프리셋의 소유자 부여를 켠다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.preset.name}의 소유자 부여를 켭니다",
            english=(f"{laid.caller.username} turns on owner assignment of {laid.preset.name}"),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                laid.preset.id, UpdateRolePresetBody(auto_assign_to_owner=True)
            )
        return payload.role_preset


@dataclass(frozen=True)
class TheSuperadminRenamesIt(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-renames-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 프리셋 이름을 변경하면, 새 이름을 담은 프리셋 전체가 응답으로 옵니다",
            english=(
                "when the superadmin renames a preset, "
                "the whole preset carrying the new name comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Renaming()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return ThePresetComesBack(PresetLook(self.started, named=RENAMED))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRename(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-rename-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 이름을 변경하려 하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to rename a preset, "
                "it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Renaming()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AProjectPresetTakesOwnerAssign(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-project-preset-takes-owner-assign"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트 스코프 프리셋의 소유자 부여를 켜면, 켜진 프리셋 전체가 응답으로 옵니다",
            english=(
                "turning on owner assignment of a project-scope preset brings the whole "
                "preset back turned on"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return TurningOwnerAssignOn()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return ThePresetComesBack(PresetLook(self.started, auto_assign_to_owner=True))


@dataclass(frozen=True)
class ADomainPresetRefusesOwnerAssign(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-domain-preset-refuses-owner-assign"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트 외 스코프 프리셋의 소유자 부여를 켜려 하면, 소유자가 없어 거부됩니다",
            english=(
                "turning on owner assignment of a preset in a scope other than a project "
                "is rejected because there is no owner"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN, scope_type=DomainEntityType())

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return TurningOwnerAssignOn()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheCallIsRefused(RolePresetOwnerAssignNotAllowed)


SCENARIOS: list[EditingStep] = [
    TheSuperadminRenamesIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRename(),
    AProjectPresetTakesOwnerAssign(started=datetime.now(UTC)),
    ADomainPresetRefusesOwnerAssign(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
