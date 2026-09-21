"""What a model card scenario table says besides the call.

A card is created in a project, on a folder of that project, so a table lays the project
and the folder before the card and authorizes through the card. The presets a card can
run on are laid beside it in the public scope: which of them fit is the card's
requirements' to say, and the read is answered for the card.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.common.types import IntrinsicSlotNames
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import Answered, Given, Refused, Same, Then, Verdict
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.system import role_named
from bai_scenario.components.vfolder import STORAGE_HOST
from bai_scenario.seeds.deployment_revision_preset.preset import (
    SeedDeploymentPreset,
    SeedPresetSlot,
)
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.image.image import SeedImage
from bai_scenario.seeds.image.registry import SeedContainerRegistry
from bai_scenario.seeds.model_card.model_card import SeedModelCard, SeedRequirement
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_slot.slot_type import SeedSlotType
from bai_scenario.seeds.runtime_variant.runtime_variant import SeedRuntimeVariant
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.vfolder.vfolder import SeedProjectVFolder


@dataclass(frozen=True)
class Allocation:
    """cpu와 메모리 한 쌍. 카드가 요구하는 양이기도 하고 프리셋이 할당하는 양이기도 하다."""

    cpu: Decimal
    memory: Decimal


ASKED = Allocation(cpu=Decimal("4"), memory=Decimal("2048"))
"""What the card a table lays asks for."""

FITS = Allocation(cpu=Decimal("8"), memory=Decimal("4096"))
LACKS = Allocation(cpu=Decimal("1"), memory=Decimal("1024"))
"""The two presets laid beside the card: one meets both asks, one meets neither."""


@dataclass(frozen=True)
class ACardAndACaller:
    """프리셋을 물을 카드 하나와, 그것을 부를 사람. ``fitting``은 카드의 요구를 채우는 프리셋이다."""

    project: ProjectData
    card: ModelCardData
    fitting: tuple[DeploymentRevisionPresetData, ...]
    caller: UserData


@dataclass(frozen=True)
class SomeoneOfTheProject(SeedNest[Laid[UserData]]):
    """그 프로젝트 안에서 모델 카드에 대해 정해진 권한만 가진 사용자.

    카드는 프로젝트 스코프에 생기므로 역할도 거기 앉는다. 권한을 하나도 대지 않으면 역할을
    만들지 않는다.
    """

    domain: Laid[DomainData]
    project: Laid[ProjectData]
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        if not self.granted:
            return "모델 카드 권한을 하나도 받지 않은 사용자 준비"
        names = ", ".join(one.name or str(int(one)) for one in self.granted)
        return f"모델 카드에 {names} 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        if not self.granted:
            return someone
        role = seed.creating_from(
            SeedRole(lambda p: ProjectID(p.id), name_hint="card-user"), self.project
        )
        for one in self.granted:
            seed.adding(SeedPermission(entity_type=ModelCardEntityType(), permission=one), role)
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class LaidSlots:
    """카드와 프리셋이 가리키는 슬롯 타입의 손잡이."""

    cpu: Laid[ResourceSlotTypeData]
    memory: Laid[ResourceSlotTypeData]


@dataclass(frozen=True)
class TheTwoIntrinsicSlots(SeedNest[LaidSlots]):
    """카드의 요구와 프리셋의 할당이 가리키는 cpu, 메모리 슬롯 타입."""

    @override
    def kind(self) -> str:
        return "cpu와 메모리 슬롯 타입 준비"

    @override
    def lay(self, seed: Seeder) -> LaidSlots:
        return LaidSlots(
            cpu=seed.creating(SeedSlotType(IntrinsicSlotNames.CPU)),
            memory=seed.creating(SeedSlotType(IntrinsicSlotNames.MEMORY)),
        )


async def lay_a_preset(
    seeding: Any,
    runtime: Laid[RuntimeVariantData],
    image: Laid[ImageData],
    slots: LaidSlots,
    *,
    name_hint: str,
    gives: Allocation,
) -> Laid[DeploymentRevisionPresetData]:
    """공개 스코프에 프리셋 하나를 심고, 그 프리셋이 할당하는 cpu와 메모리를 붙인다."""
    preset: Laid[DeploymentRevisionPresetData] = await seeding.creating_from_two(
        SeedDeploymentPreset(name_hint=name_hint), runtime, image
    )
    await seeding.adding(SeedPresetSlot(seeding.made(slots.cpu).slot_name, gives.cpu), preset)
    await seeding.adding(SeedPresetSlot(seeding.made(slots.memory).slot_name, gives.memory), preset)
    return preset


@dataclass(frozen=True)
class ACardAndSomeone(Given[Any, ACardAndACaller]):
    """요구 자원이 있는 카드 하나, 그것을 채우는 프리셋과 못 채우는 프리셋, 그리고 그 프로젝트 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        names = ", ".join(one.name or str(int(one)) for one in self.granted)
        who = (
            f"모델 카드에 {names} 권한을 받은 {role_named(self.role)} 한 명"
            if self.granted
            else f"아무 모델 카드 권한도 받지 않은 {role_named(self.role)} 한 명"
        )
        return f"요구 자원이 있는 카드 하나와, 그것을 채우는 프리셋 하나와 못 채우는 프리셋 하나, 그리고 {who}"

    @override
    async def lay(self, seeding: Any) -> ACardAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="store"), domain, policy)
        caller = await seeding.within(
            SomeoneOfTheProject(domain, project, granted=self.granted, role=self.role)
        )
        folder = await seeding.creating_from_two(
            SeedProjectVFolder(host=STORAGE_HOST), project, caller
        )
        slots = await seeding.within(TheTwoIntrinsicSlots())
        card = await seeding.creating_from_three(SeedModelCard(), project, folder, caller)
        await seeding.adding(SeedRequirement(seeding.made(slots.cpu).slot_name, ASKED.cpu), card)
        await seeding.adding(
            SeedRequirement(seeding.made(slots.memory).slot_name, ASKED.memory), card
        )
        registry = await seeding.creating(SeedContainerRegistry())
        image = await seeding.creating_from(SeedImage(), registry)
        runtime = await seeding.creating(SeedRuntimeVariant())
        fitting = await lay_a_preset(
            seeding, runtime, image, slots, name_hint="fitting", gives=FITS
        )
        await lay_a_preset(seeding, runtime, image, slots, name_hint="lacking", gives=LACKS)
        return ACardAndACaller(
            project=seeding.made(project),
            card=seeding.made(card),
            fitting=(seeding.made(fitting),),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheFittingPresets(Then[ACardAndACaller, SearchDeploymentRevisionPresetsPayload]):
    """카드의 요구를 모두 채우는 프리셋만 온다."""

    @override
    def says(self) -> str:
        return "카드의 요구를 모두 채우는 프리셋만 온다"

    @override
    def look(
        self, laid: ACardAndACaller, answered: Answered[SearchDeploymentRevisionPresetsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.name for one in page.items),
                sorted(one.name for one in laid.fitting),
            ),
            Same("total_count", page.total_count, len(laid.fitting)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
