"""What a kernel allocation scenario table says besides the call.

An allocation row belongs to the session its kernel runs under, and a session is
created in its project, which is created in its domain. A caller therefore reads the
row through a role in the project or in the domain, and the overview of a domain or a
project through a role in that scope. A table needs the kernel and what it asked for,
and the caller with the scope their role sits in.
"""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    ActiveResourceOverviewInfoDTO,
    AdminSearchResourceAllocationsPayload,
    ResourceAllocationNode,
)
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Then,
    Verdict,
)
from bai_scenario.components.deployment import lay_a_deployment
from bai_scenario.components.deployment import lay_a_place as lay_a_deployment_place
from bai_scenario.components.deployment_revision import WhatARevisionStandsOn, lay_revisions
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.resource_slot import ASlotTypeAndACaller
from bai_scenario.components.system import role_named
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.image.image import SeedImage
from bai_scenario.seeds.image.registry import SeedContainerRegistry
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_group.resource_group import SeedResourceGroup
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_slot.slot_type import SeedResourceSlotType
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.session.kernel import SeedKernelOf
from bai_scenario.seeds.session.session import SeedSession
from bai_scenario.seeds.user.fields import SeedKeypairOf

type Slots = tuple[tuple[str, Decimal], ...]
"""커널이 슬롯마다 요구한 양. 슬롯 이름과 양의 짝이다."""


class Granted(enum.Enum):
    """호출자가 세션 조회 권한을 받은 스코프."""

    NOTHING = "nothing"
    THE_PROJECT = "project"
    THE_DOMAIN = "domain"


@dataclass(frozen=True)
class AKernel:
    """커널 하나와, 그것이 슬롯마다 요구한 양."""

    session: SessionEntityData
    kernel: KernelInfo
    slots: Slots


@dataclass(frozen=True)
class AKernelAndACaller:
    """커널 하나와, 그것을 호출할 사용자."""

    domain: DomainData
    project: ProjectData
    kernel: AKernel
    caller: UserData


@dataclass(frozen=True)
class KernelsAndACaller:
    """검색 대상 할당을 가진 커널 여럿과, 검색을 호출할 사용자. ``named``는 그중 필터로 골라낼 하나다."""

    kernels: tuple[AKernel, ...]
    named: AKernel
    caller: UserData

    def allocations(self) -> list[tuple[str, str]]:
        """미리 만들어 둔 할당 전부를 커널 id와 슬롯 이름의 짝으로."""
        return [(str(one.kernel.id), name) for one in self.kernels for name, _ in one.slots]


@dataclass(frozen=True)
class SomeoneReadingSessionsIn[S](SeedNest[Laid[UserData]]):
    """그 스코프에서 세션을 읽을 수 있는 사용자."""

    domain: Laid[DomainData]
    scope: Laid[S]
    scope_of: Callable[[S], EntityIdentifier]
    where: str

    @override
    def kind(self) -> str:
        return f"{self.where} 범위의 세션 조회 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(SeedRole(self.scope_of, name_hint="session-reader"), self.scope)
        seed.adding(
            SeedPermission(entity_type=SessionEntityType(), permission=Permission.READ), role
        )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class LaidPlace:
    """커널이 놓이는 자리를 이루는 행들의 손잡이."""

    domain: Laid[DomainData]
    project: Laid[ProjectData]
    group: Laid[ResourceGroupData]
    owner: Laid[UserData]
    image: Laid[ImageData]
    slot_types: tuple[Laid[ResourceSlotTypeData], ...]
    access_key: AccessKey


async def lay_a_place(seeding: Any, *, slots: int) -> LaidPlace:
    """커널이 놓일 도메인·프로젝트·리소스 그룹과, 세션을 요청한 사용자와 그 키, 커널이 실행할
    이미지, 커널이 요구할 슬롯 종류를 만든다."""
    domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    policy = await seeding.once(SeedProjectPolicy())
    project = await seeding.creating_from_two(SeedProject(name_hint="team"), domain, policy)
    group = await seeding.creating(SeedResourceGroup())
    owner = await seeding.within(SomeoneOf(domain))
    key_policy = await seeding.creating(SeedKeypairPolicy())
    key = await seeding.adding(SeedKeypairOf(resource_policy=seeding.made(key_policy).name), owner)
    registry = await seeding.creating(SeedContainerRegistry())
    image = await seeding.creating_from(SeedImage(), registry)
    slot_types = [await seeding.creating(SeedResourceSlotType()) for _ in range(slots)]
    return LaidPlace(
        domain=domain,
        project=project,
        group=group,
        owner=owner,
        image=image,
        slot_types=tuple(slot_types),
        access_key=seeding.made(key).access_key,
    )


def asked_for(seeding: Any, place: LaidPlace) -> Slots:
    """그 자리의 슬롯 종류마다 차례로 1, 2, 3, … 을 요구한다."""
    return tuple(
        (seeding.made(one).slot_name, Decimal(i + 1)) for i, one in enumerate(place.slot_types)
    )


async def lay_a_kernel(seeding: Any, place: LaidPlace) -> AKernel:
    """그 자리에 세션 하나와 그 커널을 만든다. 커널은 자리의 슬롯 종류 전부를 요구한다."""
    session = await seeding.creating_from_three(
        SeedSession(access_key=place.access_key), place.project, place.owner, place.group
    )
    slots = asked_for(seeding, place)
    kernel = await seeding.adding_with_nested(
        SeedKernelOf(session=seeding.made(session), image=seeding.made(place.image), slots=slots),
        session,
    )
    return AKernel(session=seeding.made(session), kernel=seeding.made(kernel), slots=slots)


async def lay_a_caller_of(
    seeding: Any, place: LaidPlace, *, role: UserRole, granted: Granted
) -> Laid[UserData]:
    """그 자리에서 호출할 사용자를 둔다. ``granted``가 말하는 스코프에 세션 조회 역할이 앉는다."""
    caller: Laid[UserData]
    match granted:
        case Granted.NOTHING:
            caller = await seeding.within(SomeoneOf(place.domain, role=role))
        case Granted.THE_PROJECT:
            caller = await seeding.within(
                SomeoneReadingSessionsIn(
                    place.domain, place.project, lambda p: ProjectID(p.id), "프로젝트"
                )
            )
        case Granted.THE_DOMAIN:
            caller = await seeding.within(
                SomeoneReadingSessionsIn(
                    place.domain, place.domain, lambda d: DomainID(d.id), "도메인"
                )
            )
    return caller


def _who(role: UserRole, granted: Granted) -> str:
    match granted:
        case Granted.NOTHING:
            return f"{role_named(role)} 한 명"
        case Granted.THE_PROJECT:
            return "프로젝트 범위에서 세션을 읽을 수 있는 일반 사용자 한 명"
        case Granted.THE_DOMAIN:
            return "도메인 범위에서 세션을 읽을 수 있는 일반 사용자 한 명"


@dataclass(frozen=True)
class AKernelAndSomeone(Given[Any, AKernelAndACaller]):
    """슬롯 둘을 요구하는 커널 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: Granted = Granted.NOTHING

    @override
    def describe(self) -> str:
        return f"슬롯 둘을 요구하며 대기 중인 커널 하나와, {_who(self.role, self.granted)}"

    @override
    async def lay(self, seeding: Any) -> AKernelAndACaller:
        place = await lay_a_place(seeding, slots=2)
        kernel = await lay_a_kernel(seeding, place)
        caller = await lay_a_caller_of(seeding, place, role=self.role, granted=self.granted)
        return AKernelAndACaller(
            domain=seeding.made(place.domain),
            project=seeding.made(place.project),
            kernel=kernel,
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class KernelsAndSomeone(Given[Any, KernelsAndACaller]):
    """커널 여럿과 사용자 한 명. 커널마다 같은 슬롯 종류들을 요구한다."""

    role: UserRole = UserRole.USER
    kernels: int = 1
    slots_each: int = 2

    @override
    def describe(self) -> str:
        return (
            f"슬롯 {self.slots_each}개씩 요구하는 커널 {self.kernels}개와, "
            f"{role_named(self.role)} 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> KernelsAndACaller:
        place = await lay_a_place(seeding, slots=self.slots_each)
        laid = [await lay_a_kernel(seeding, place) for _ in range(self.kernels)]
        caller = await lay_a_caller_of(seeding, place, role=self.role, granted=Granted.NOTHING)
        return KernelsAndACaller(kernels=tuple(laid), named=laid[0], caller=seeding.made(caller))


@dataclass(frozen=True)
class ASlotTypeAKernelAsksForAndSomeone(Given[Any, ASlotTypeAndACaller]):
    """커널 하나가 요구하는 슬롯 종류 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return (
            f"대기 중인 커널 하나가 요구하는 자원 슬롯 종류 하나와, {role_named(self.role)} 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> ASlotTypeAndACaller:
        place = await lay_a_place(seeding, slots=1)
        await lay_a_kernel(seeding, place)
        caller = await lay_a_caller_of(seeding, place, role=self.role, granted=Granted.NOTHING)
        return ASlotTypeAndACaller(
            slot_type=seeding.made(place.slot_types[0]), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class ASlotTypeARevisionUsesAndSomeone(Given[Any, ASlotTypeAndACaller]):
    """배포 리비전 하나가 사용하는 슬롯 종류 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"배포 리비전 하나가 사용하는 자원 슬롯 종류 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ASlotTypeAndACaller:
        place = await lay_a_deployment_place(seeding, role=self.role)
        deployment = await lay_a_deployment(seeding, place)
        materials = await seeding.within(WhatARevisionStandsOn(place.caller))
        await lay_revisions(seeding, place, deployment, materials, 1)
        return ASlotTypeAndACaller(
            slot_type=seeding.made(materials.cpu), caller=seeding.made(place.caller)
        )


@dataclass(frozen=True)
class AmountOf(Condition[str]):
    """이 양이어야 한다. 응답은 열의 소수 자릿수까지 붙인 문자열이므로 수로 비교한다."""

    wanted: Decimal

    @override
    def says(self) -> str:
        return f"수로 보아 {self.wanted}"

    @override
    def holds(self, got: str) -> bool:
        return Decimal(got) == self.wanted


def allocation_verdicts(node: ResourceAllocationNode, kernel: AKernel, slot: str) -> list[Verdict]:
    """Every place of one allocation node. The ids are the kernel's, so they are compared
    with the laid kernel rather than written into the report."""
    return [
        Held(
            "id",
            node.id,
            SameAs(f"{kernel.kernel.id}:{slot}", "미리 만들어 둔 커널의 id와 슬롯 이름"),
        ),
        Held(
            "kernel_id", node.kernel_id, SameAs(str(kernel.kernel.id), "미리 만들어 둔 커널의 id")
        ),
        Same("slot_name", node.slot_name, slot),
        Held("requested", node.requested, AmountOf(dict(kernel.slots)[slot])),
        Same("used", node.used, None),
    ]


@dataclass(frozen=True)
class TheAllocationNode(Then[AKernelAndACaller, ResourceAllocationNode]):
    """미리 만들어 둔 커널의 첫 슬롯 할당이 통째로 반환된다. 아직 스케줄링되지 않았으므로
    요구한 양만 있고 실제 사용량은 없다."""

    @override
    def says(self) -> str:
        return "그 커널의 할당 전체가 반환된다"

    @override
    def look(
        self, laid: AKernelAndACaller, answered: Answered[ResourceAllocationNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return allocation_verdicts(node, laid.kernel, laid.kernel.slots[0][0])


@dataclass(frozen=True)
class EveryLaidAllocationIsCounted(Then[KernelsAndACaller, AdminSearchResourceAllocationsPayload]):
    """미리 만들어 둔 할당이 모두 집계된다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 할당이 모두 집계된다"

    @override
    def look(
        self, laid: KernelsAndACaller, answered: Answered[AdminSearchResourceAllocationsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        wanted = laid.allocations()
        return [
            Held(
                "items",
                sorted((one.kernel_id, one.slot_name) for one in page.items),
                SameAs(sorted(wanted), "미리 만들어 둔 커널들의 id와 슬롯 이름"),
            ),
            Same("total_count", page.total_count, len(wanted)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedSlotIsLeft(Then[KernelsAndACaller, AdminSearchResourceAllocationsPayload]):
    """필터에 맞는 슬롯의 할당만 반환된다."""

    @override
    def says(self) -> str:
        return "필터에 맞는 슬롯의 할당 하나만 반환된다"

    @override
    def look(
        self, laid: KernelsAndACaller, answered: Answered[AdminSearchResourceAllocationsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        slot = laid.named.slots[0][0]
        return [
            Same("items", [one.slot_name for one in page.items], [slot]),
            Held(
                "items[0].kernel_id",
                [one.kernel_id for one in page.items],
                SameAs([str(laid.named.kernel.id)], "골라낼 커널의 id"),
            ),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedKernelIsLeft(Then[KernelsAndACaller, AdminSearchResourceAllocationsPayload]):
    """필터에 맞는 커널의 할당만 반환된다."""

    @override
    def says(self) -> str:
        return "필터에 맞는 커널의 할당만 반환된다"

    @override
    def look(
        self, laid: KernelsAndACaller, answered: Answered[AdminSearchResourceAllocationsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held(
                "items",
                sorted((one.kernel_id, one.slot_name) for one in page.items),
                SameAs(
                    sorted((str(laid.named.kernel.id), name) for name, _ in laid.named.slots),
                    "골라낼 커널의 id와 그 슬롯 이름",
                ),
            ),
            Same("total_count", page.total_count, len(laid.named.slots)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheFirstPageOfAllocations(Then[KernelsAndACaller, AdminSearchResourceAllocationsPayload]):
    """크기를 지정하지 않은 첫 페이지. 기본 크기만큼 반환되고 다음 페이지가 있다고 응답한다."""

    size: int

    @override
    def says(self) -> str:
        return "기본 크기의 첫 페이지가 반환된다"

    @override
    def look(
        self, laid: KernelsAndACaller, answered: Answered[AdminSearchResourceAllocationsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("len(items)", len(page.items), self.size),
            Same("total_count", page.total_count, len(laid.allocations())),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class NothingIsOccupied(Then[Any, ActiveResourceOverviewInfoDTO]):
    """점유된 슬롯이 없고 세션 수가 0인 개요. 대기 중인 커널은 세지 않는다."""

    @override
    def says(self) -> str:
        return "점유된 슬롯이 없고 세션 수가 0인 개요가 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[ActiveResourceOverviewInfoDTO]) -> list[Verdict]:
        overview = answered.response
        if overview is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("slots.entries", list(overview.slots.entries), []),
            Same("session_count", overview.session_count, 0),
        ]
