"""What a resource slot type scenario table says besides the call.

A slot type is created in no scope and addressed by its name in every call. A table needs
the caller, and the slot type or slot types the call reads. The agent resources and kernel
allocations the same adapter reads are not laid here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.resource_slot.slot_type import SeedResourceSlotType

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchResourceSlotTypesPayload,
    PurgeResourceSlotTypePayload,
    ResourceSlotTypeNode,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import NumberFormatInfo
from ai.backend.common.types import SlotTypes
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Skipped,
    Then,
    Verdict,
)

DISPLAYED = "미리 만들어 둔 슬롯"
"""시드가 미리 만들어 두는 슬롯 종류의 표시 이름. 시나리오가 기대값으로 다시 쓰므로 한 곳에 둔다."""

DECIMAL = NumberFormatInfo(binary=False, round_length=0)
"""서식을 생략하면 어댑터가 채우는 기본값. 십진에 반올림 없음."""


@dataclass(frozen=True)
class ASlotTypeAndACaller:
    """슬롯 종류 하나와, 그것을 호출할 사용자."""

    slot_type: ResourceSlotTypeData
    caller: UserData


@dataclass(frozen=True)
class ManySlotTypesAndACaller:
    """검색 대상 슬롯 종류 여럿과, 검색을 호출할 사용자. ``named``는 그중 이름 필터로 골라낼 하나다."""

    laid: tuple[ResourceSlotTypeData, ...]
    named: ResourceSlotTypeData
    caller: UserData


@dataclass(frozen=True)
class ASlotTypeAndSomeone(Given[Any, ASlotTypeAndACaller]):
    """슬롯 종류 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    enabled: bool = True

    @override
    def describe(self) -> str:
        return f"자원 슬롯 종류 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ASlotTypeAndACaller:
        slot_type = await seeding.creating(SeedResourceSlotType(enabled=self.enabled))
        caller = await lay_a_caller(seeding, self.role)
        return ASlotTypeAndACaller(seeding.made(slot_type), seeding.made(caller))


@dataclass(frozen=True)
class ManySlotTypesAndSomeone(Given[Any, ManySlotTypesAndACaller]):
    """슬롯 종류 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return f"자원 슬롯 종류 {self.besides + 1}개와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManySlotTypesAndACaller:
        wanted = await seeding.creating(SeedResourceSlotType(name_hint="wanted"))
        others = [
            await seeding.creating(SeedResourceSlotType(name_hint="other"))
            for _ in range(self.besides)
        ]
        caller = await lay_a_caller(seeding, self.role)
        return ManySlotTypesAndACaller(
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


def slot_type_verdicts(
    node: ResourceSlotTypeNode,
    *,
    named: str,
    slot_type: SlotTypes,
    required: bool,
    enabled: bool,
    display_name: str,
    description: str,
    display_unit: str,
    display_icon: str,
    number_format: NumberFormatInfo,
    rank: int,
) -> list[Verdict]:
    """Every place of one slot type node. The id is the name, so it is seen and the uuid is not."""
    return [
        Same("id", node.id, named),
        Skipped("uuid", "데이터베이스가 만든다"),
        Same("slot_name", node.slot_name, named),
        Same("slot_type", node.slot_type, slot_type.value),
        Same("required", node.required, required),
        Same("enabled", node.enabled, enabled),
        Same("display_name", node.display_name, display_name),
        Same("description", node.description, description),
        Same("display_unit", node.display_unit, display_unit),
        Same("display_icon", node.display_icon, display_icon),
        Same("number_format", node.number_format, number_format),
        Same("rank", node.rank, rank),
    ]


@dataclass(frozen=True)
class TheNewSlotTypeNode(Then[Any, ResourceSlotTypeNode]):
    """방금 생성한 슬롯 종류가 통째로 반환된다. 기대값은 요청이 지정한 값에서 읽는다."""

    named: str
    slot_type: SlotTypes
    required: bool = False
    enabled: bool = True
    display_name: str = ""
    description: str = ""
    display_unit: str = ""
    display_icon: str = ""
    number_format: NumberFormatInfo = field(default_factory=lambda: DECIMAL)
    rank: int = 0

    @override
    def says(self) -> str:
        return "생성한 슬롯 종류 전체가 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[ResourceSlotTypeNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return slot_type_verdicts(
            node,
            named=self.named,
            slot_type=self.slot_type,
            required=self.required,
            enabled=self.enabled,
            display_name=self.display_name,
            description=self.description,
            display_unit=self.display_unit,
            display_icon=self.display_icon,
            number_format=self.number_format,
            rank=self.rank,
        )


@dataclass(frozen=True)
class TheSlotTypeNode(Then[ASlotTypeAndACaller, ResourceSlotTypeNode]):
    """미리 만들어 둔 슬롯 종류가 통째로 반환된다. 수정 요청은 바뀌어야 하는 필드만 인자로 준다."""

    display_name: str | Kept = KEPT
    enabled: bool | Kept = KEPT

    @override
    def says(self) -> str:
        return "미리 만들어 둔 슬롯 종류 전체가 반환된다"

    @override
    def look(
        self, laid: ASlotTypeAndACaller, answered: Answered[ResourceSlotTypeNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seed = laid.slot_type
        return slot_type_verdicts(
            node,
            named=seed.slot_name,
            slot_type=SlotTypes(seed.slot_type),
            required=seed.required,
            enabled=seed.enabled if isinstance(self.enabled, Kept) else self.enabled,
            display_name=(
                seed.display_name if isinstance(self.display_name, Kept) else self.display_name
            ),
            description=seed.description,
            display_unit=seed.display_unit,
            display_icon=seed.display_icon,
            number_format=NumberFormatInfo(
                binary=seed.number_format.binary, round_length=seed.number_format.round_length
            ),
            rank=seed.rank,
        )


@dataclass(frozen=True)
class EveryLaidSlotTypeIsCounted(
    Then[ManySlotTypesAndACaller, AdminSearchResourceSlotTypesPayload]
):
    """미리 만들어 둔 슬롯 종류가 모두 집계된다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 슬롯 종류가 모두 집계된다"

    @override
    def look(
        self,
        laid: ManySlotTypesAndACaller,
        answered: Answered[AdminSearchResourceSlotTypesPayload],
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.slot_name for one in page.items),
                sorted(one.slot_name for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedSlotTypeIsLeft(
    Then[ManySlotTypesAndACaller, AdminSearchResourceSlotTypesPayload]
):
    """필터에 맞는 그 하나만 반환된다."""

    @override
    def says(self) -> str:
        return "필터에 맞는 슬롯 종류 하나만 반환된다"

    @override
    def look(
        self,
        laid: ManySlotTypesAndACaller,
        answered: Answered[AdminSearchResourceSlotTypesPayload],
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("items", [one.slot_name for one in page.items], [laid.named.slot_name]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheFirstPageOfSlotTypes(Then[ManySlotTypesAndACaller, AdminSearchResourceSlotTypesPayload]):
    """크기를 지정하지 않은 첫 페이지. 기본 크기만큼 반환되고 다음 페이지가 있다고 응답한다."""

    size: int

    @override
    def says(self) -> str:
        return "기본 크기의 첫 페이지가 반환된다"

    @override
    def look(
        self,
        laid: ManySlotTypesAndACaller,
        answered: Answered[AdminSearchResourceSlotTypesPayload],
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("len(items)", len(page.items), self.size),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheDeletedSlotName(Then[ASlotTypeAndACaller, PurgeResourceSlotTypePayload]):
    """삭제한 슬롯 종류의 이름을 담은 응답."""

    @override
    def says(self) -> str:
        return "삭제한 슬롯 종류의 이름이 반환된다"

    @override
    def look(
        self, laid: ASlotTypeAndACaller, answered: Answered[PurgeResourceSlotTypePayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("slot_name", payload.slot_name, laid.slot_type.slot_name)]
