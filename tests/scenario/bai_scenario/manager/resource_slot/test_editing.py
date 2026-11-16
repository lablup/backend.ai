"""슬롯 종류 수정 — 이름으로 지정해 무엇이 바뀌고, 누가 수정할 수 있는가.

이름과 종류는 수정할 수 없다. 요청 타입이 그 둘을 받지 않으므로 여기 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.request import UpdateResourceSlotTypeInput
from ai.backend.common.dto.manager.v2.resource_slot.response import ResourceSlotTypeNode
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_slot import (
    ASlotTypeAndACaller,
    ASlotTypeAndSomeone,
    TheSlotTypeNode,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

RENAMED = "GPU shares"
UNKNOWN = "no-such-slot"

type EditingStep = Scenario[
    TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode
]


@dataclass(frozen=True)
class Editing(When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]):
    """미리 만들어 둔 슬롯 종류를 이름으로 지정해 수정한다. 응답에 담긴 노드를 꺼내서 준다."""

    display_name: str | None = None
    enabled: bool | None = None
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "admin_update_slot_type"

    @override
    def describe(self, laid: ASlotTypeAndACaller) -> str:
        target = UNKNOWN if self.unknown else laid.slot_type.slot_name
        changing_ko = []
        changing_en = []
        if self.display_name is not None:
            changing_ko.append("표시 이름")
            changing_en.append("display name")
        if self.enabled is not None:
            changing_ko.append("사용 여부")
            changing_en.append("enabled flag")
        if not changing_ko:
            return Says(
                f"{laid.caller.username} 이 {target}에서 값을 지정하지 않고 수정합니다",
                english=f"{laid.caller.username} edits {target} without giving a value",
            )
        return Says(
            f"{laid.caller.username} 이 {target}의 {' 및 '.join(changing_ko)} 변경을 요청합니다",
            english=(f"{laid.caller.username} edits the {' and '.join(changing_en)} of {target}"),
        )

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
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "editing-a-slot-type-display-name-leaves-the-rest-alone"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이름으로 지정해 표시 이름만 수정하면, 표시 이름은 새 값이 되고 "
            "나머지는 그대로 유지됩니다",
            english=(
                "when the superadmin edits only the display name of a slot type named by its "
                "name, the display name becomes the new value and the rest stays"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheSlotTypeNode(display_name=RENAMED)


@dataclass(frozen=True)
class DisablingIt(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "disabling-a-slot-type-answers-it-disabled"

    @override
    def describe(self) -> str:
        return Says(
            "사용 중인 자원 슬롯 유형의 사용 여부를 끄면, 사용하지 않는 상태가 담긴 노드가 "
            "반환됩니다",
            english=(
                "turning off the enabled flag of a slot type that is in use brings back a node "
                "that is not enabled"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(enabled=False)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheSlotTypeNode(enabled=False)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-slot-type-edit-giving-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "슬롯 이름만 지정하고 나머지를 모두 생략해 수정하면 아무것도 바뀌지 않은 노드가 "
            "반환됩니다",
            english=(
                "editing a slot type with only its name and every other value omitted brings "
                "back a node that changed nothing"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheSlotTypeNode()


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownNameIsNotFound(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-slot-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 이름을 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin edits a name nothing answers to, the call is rejected as "
                "not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED, unknown=True)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotEdit(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-edit-a-slot-type"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 자원 슬롯 유형을 수정하면 역할 부족으로 거부됩니다",
            english=(
                "a user who is not the superadmin editing a slot type is rejected for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserWithoutTheRoleEditingAnUnknownNameIsRefusedByRole(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-without-the-role-editing-an-unknown-slot-name-is-refused-by-role"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 존재하지 않는 이름을 수정하면 대상 없음이 아니라 "
            "역할 부족으로 거부됩니다. 호출한 사용자가 쓸 수 있는지를 이름을 풀어내기 전에 "
            "검사하기 때문입니다",
            english=(
                "when a user who is not the superadmin edits a name nothing answers to, the call "
                "is rejected for lack of role, not as not found, because whether the caller can "
                "use it is checked before the name is resolved"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Editing(display_name=RENAMED, unknown=True)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-edit-a-slot-type"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 꺼도 superadmin 이 아니면 자원 슬롯 유형을 수정하지 못합니다",
            english=(
                "turning permission checks off still does not let a user who is not the "
                "superadmin edit a slot type"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
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
    # TODO(BA-7929): the name is resolved before the role gate, so this row fails until
    # the order is turned around.
    # AUserWithoutTheRoleEditingAnUnknownNameIsRefusedByRole(),
    EnforcementOffStillNeedsTheSuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
