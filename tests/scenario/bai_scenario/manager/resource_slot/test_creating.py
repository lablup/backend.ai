"""슬롯 종류 생성 — 생략한 항목이 무엇으로 채워지고, 누가 생성할 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.request import CreateResourceSlotTypeInput
from ai.backend.common.dto.manager.v2.resource_slot.response import ResourceSlotTypeNode
from ai.backend.common.dto.manager.v2.resource_slot.types import NumberFormatInfo, NumberFormatInput
from ai.backend.common.types import SlotTypes
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeAlreadyExists
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_slot import (
    ASlotTypeAndACaller,
    ASlotTypeAndSomeone,
    TheNewSlotTypeNode,
)
from bai_scenario.components.system import ENFORCEMENT, ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MADE = "cuda.shares"
BINARY_ROUNDED = NumberFormatInfo(binary=True, round_length=2)

type CreatingStep = Scenario[TestSeedingSession, Any, ResourceSlotAdapter, ResourceSlotTypeNode]


@dataclass(frozen=True)
class Creating(When[ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]):
    """슬롯 종류 하나를 생성한다. 응답에 담긴 노드를 꺼내서 준다."""

    named: str = MADE
    slot_type: SlotTypes = SlotTypes.COUNT
    shown: bool = False

    @override
    def operation(self) -> str:
        return "admin_create_slot_type"

    @override
    def describe(self, laid: ACaller) -> str:
        how_ko = "표시 항목까지 지정해" if self.shown else "이름과 종류만 지정해"
        how_en = "giving every display value" if self.shown else "giving only a name and a kind"
        return Says(
            f"{laid.caller.username} 이 {self.slot_type.value} 종류 슬롯 {self.named}을 {how_ko} 생성합니다",
            english=(
                f"{laid.caller.username} creates the {self.slot_type.value} slot "
                f"{self.named} {how_en}"
            ),
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ACaller) -> ResourceSlotTypeNode:
        if self.shown:
            asked = CreateResourceSlotTypeInput(
                slot_name=self.named,
                slot_type=self.slot_type,
                required=True,
                enabled=False,
                display_name="GPU shares",
                description="fractional GPU",
                display_unit="share",
                display_icon="gpu",
                number_format=NumberFormatInput(binary=True, round_length=2),
                rank=3,
            )
        else:
            asked = CreateResourceSlotTypeInput(slot_name=self.named, slot_type=self.slot_type)
        with ActingAs(laid.caller):
            payload = await adapter.admin_create_slot_type(asked)
        return payload.resource_slot_type


@dataclass(frozen=True)
class CreatingWithTheLaidName(When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]):
    """미리 만들어 둔 슬롯 종류와 같은 이름으로 생성한다."""

    @override
    def operation(self) -> str:
        return "admin_create_slot_type"

    @override
    def describe(self, laid: ASlotTypeAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 이미 있는 이름 {laid.slot_type.slot_name}으로 다시 생성합니다",
            english=(
                f"{laid.caller.username} creates it again with the name "
                f"{laid.slot_type.slot_name} that already exists"
            ),
        )

    @override
    async def call(
        self, adapter: ResourceSlotAdapter, laid: ASlotTypeAndACaller
    ) -> ResourceSlotTypeNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create_slot_type(
                CreateResourceSlotTypeInput(
                    slot_name=laid.slot_type.slot_name, slot_type=SlotTypes.COUNT
                )
            )
        return payload.resource_slot_type


@dataclass(frozen=True)
class TheSuperadminMakesOneWithANameAndAKind(
    Scenario[TestSeedingSession, ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-slot-type-with-a-name-and-a-kind-alone"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 슬롯 이름과 종류만 지정해 생성하면, 표시용 문자열은 모두 비고 "
            "필수 여부는 거짓, 사용 여부는 참, 순위는 0, 숫자 서식은 십진에 반올림 없음인 "
            "노드가 반환됩니다",
            english=(
                "when the superadmin creates a slot type with only a name and a kind, the node "
                "comes back with every display string empty, required false, enabled true, "
                "rank 0, and a decimal number format without rounding"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, ResourceSlotTypeNode]:
        return TheNewSlotTypeNode(named=MADE, slot_type=SlotTypes.COUNT)


@dataclass(frozen=True)
class EveryDisplayValueComesBackAsGiven(
    Scenario[TestSeedingSession, ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-slot-type-made-with-every-display-value-carries-them-back"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 표시 이름, 설명, 단위, 아이콘, 서식, 순위까지 지정해 생성하면, "
            "지정한 값이 그대로 담긴 노드가 반환됩니다",
            english=(
                "when the superadmin creates a slot type with the display name, description, "
                "unit, icon, number format and rank given, the node comes back with those "
                "values as given"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Creating(shown=True)

    @override
    def then(self) -> Then[ACaller, ResourceSlotTypeNode]:
        return TheNewSlotTypeNode(
            named=MADE,
            slot_type=SlotTypes.COUNT,
            required=True,
            enabled=False,
            display_name="GPU shares",
            description="fractional GPU",
            display_unit="share",
            display_icon="gpu",
            number_format=BINARY_ROUNDED,
            rank=3,
        )


@dataclass(frozen=True)
class EachKindIsAccepted(
    Scenario[TestSeedingSession, ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    slot_type: SlotTypes

    @override
    def summary(self) -> str:
        return f"a-slot-type-of-the-{self.slot_type.value}-kind-is-made"

    @override
    def describe(self) -> str:
        return Says(
            f"superadmin 이 {self.slot_type.value} 종류로 생성하면 그 종류가 담긴 노드가 반환됩니다",
            english=(
                f"when the superadmin creates a slot type of the {self.slot_type.value} kind, "
                "the node comes back with that kind"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Creating(slot_type=self.slot_type)

    @override
    def then(self) -> Then[ACaller, ResourceSlotTypeNode]:
        return TheNewSlotTypeNode(named=MADE, slot_type=self.slot_type)


@dataclass(frozen=True)
class ANameAlreadyTakenIsRefused(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-slot-name-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "같은 이름의 자원 슬롯 유형이 있을 때 그 이름으로 다시 생성하면, 이름 중복으로 "
            "거부됩니다. 이 시나리오는 에이전트 자원, 커널 할당, 모델 카드 자원 요구, "
            "배포 preset 자원 슬롯, 배포 리비전 자원 슬롯 테이블이 참조하므로 덮어쓰지 않습니다",
            english=(
                "when a slot type of the same name exists, creating it again with that name is "
                "rejected as a duplicate. This scenario is not overwritten because the agent "
                "resource, kernel allocation, model card resource request, deployment preset "
                "resource slot and deployment revision resource slot tables refer to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return CreatingWithTheLaidName()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(ResourceSlotTypeAlreadyExists)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotCreate(
    Scenario[TestSeedingSession, ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-slot-type"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 자원 슬롯 유형을 생성하면 역할 부족으로 거부됩니다",
            english=(
                "a user who is not the superadmin creating a slot type is rejected for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheSuperadmin(
    Scenario[TestSeedingSession, ACaller, ResourceSlotAdapter, ResourceSlotTypeNode], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-user-create-a-slot-type"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 꺼도 superadmin 이 아니면 자원 슬롯 유형을 생성하지 못합니다",
            english=(
                "turning permission checks off still does not let a user who is not the "
                "superadmin create a slot type"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesOneWithANameAndAKind(),
    EveryDisplayValueComesBackAsGiven(),
    EachKindIsAccepted(slot_type=SlotTypes.COUNT),
    EachKindIsAccepted(slot_type=SlotTypes.BYTES),
    EachKindIsAccepted(slot_type=SlotTypes.UNIQUE),
    EachKindIsAccepted(slot_type=SlotTypes.UNIFIED),
    ANameAlreadyTakenIsRefused(),
    AUserWhoIsNotTheSuperadminMayNotCreate(),
    EnforcementOffStillNeedsTheSuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
