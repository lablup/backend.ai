"""슬롯 종류 고치기 — 이름으로 지목해 무엇이 바뀌고, 누가 고칠 수 있는가.

이름과 종류는 고치지 못한다. 요청 타입이 그 둘을 받지 않으므로 여기 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_slot import (
    ASlotTypeAndACaller,
    ASlotTypeAndSomeone,
    TheSlotTypeNode,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.request import UpdateResourceSlotTypeInput
from ai.backend.common.dto.manager.v2.resource_slot.response import ResourceSlotTypeNode
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

RENAMED = "GPU shares"
UNKNOWN = "no-such-slot"

type EditingStep = Scenario[
    SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode
]


@dataclass(frozen=True)
class Editing(When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]):
    """심은 슬롯 종류를 이름으로 지목해 고친다. 답이 실은 노드를 벗겨서 준다."""

    display_name: str | None = None
    enabled: bool | None = None
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "admin_update_slot_type"

    @override
    def describe(self, laid: ASlotTypeAndACaller) -> str:
        target = UNKNOWN if self.unknown else laid.slot_type.slot_name
        changing = []
        if self.display_name is not None:
            changing.append("표시 이름")
        if self.enabled is not None:
            changing.append("사용 여부")
        return f"{laid.caller.username}이 {target}의 {' 및 '.join(changing) or '아무것도'} 고침"

    @override
    async def call(
        self, adapter: ResourceSlotAdapter, laid: ASlotTypeAndACaller
    ) -> ResourceSlotTypeNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_update_slot_type(
                UpdateResourceSlotTypeInput(
                    slot_name=UNKNOWN if self.unknown else laid.slot_type.slot_name,
                    display_name=self.display_name,
                    enabled=self.enabled,
                )
            )
        return payload.resource_slot_type


@dataclass(frozen=True)
class TheDisplayNameChangesAndTheRestStays(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "editing-a-slot-type-display-name-leaves-the-rest-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름으로 지목해 표시 이름만 고치면, 표시 이름은 새 값이 되고 나머지는 그대로 남는다"

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheSlotTypeNode(display_name=RENAMED)


@dataclass(frozen=True)
class DisablingIt(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "disabling-a-slot-type-answers-it-disabled"

    @override
    def describe(self) -> str:
        return "사용 중인 슬롯 종류의 사용 여부를 내리면, 사용하지 않는다는 상태를 실은 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(enabled=False)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheSlotTypeNode(enabled=False)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-slot-type-edit-giving-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return "슬롯 이름만 주고 나머지를 모두 생략해 고치면 아무것도 바뀌지 않은 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheSlotTypeNode()


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownNameIsNotFound(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-slot-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무 슬롯 종류도 갖지 않은 이름을 고치면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED, unknown=True)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotEdit(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-edit-a-slot-type"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 슬롯 종류를 고치면 역할로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserWithoutTheRoleStillHearsNotFound(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-without-the-role-editing-an-unknown-slot-name-hears-not-found"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 없는 이름을 고치면 역할이 아니라 대상 없음으로 거부된다. "
            "이름 해석이 권한을 보지 않고 먼저 돌기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED, unknown=True)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-edit-a-slot-type"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 꺼도 슈퍼관리자가 아니면 슬롯 종류를 고치지 못한다. "
            "고치기의 문은 지우기와 달리 역할이라 스위치와 무관하다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[EditingStep] = [
    TheDisplayNameChangesAndTheRestStays(),
    DisablingIt(),
    AnEmptyEditChangesNothing(),
    TheSuperadminEditingAnUnknownNameIsNotFound(),
    AUserWhoIsNotTheSuperadminMayNotEdit(),
    AUserWithoutTheRoleStillHearsNotFound(),
    EnforcementOffStillNeedsTheSuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
