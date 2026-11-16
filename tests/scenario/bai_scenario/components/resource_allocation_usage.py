"""What a resource allocation scenario says besides the call.

A usage read answers for one scope: a keypair, a user, a project, a domain or a resource
group. Every scope's limits come from its policy and the usage comes from the rows that
hold resources, so a table lays the place a caller asks about and the caller themselves.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import (
    ResourceLimitEntryInfo,
    ResourceSlotEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    CheckPresetAvailabilityPayload,
    EffectiveBreakdownNode,
    EffectiveResourceAllocationPayload,
    ResourceGroupUsageNode,
    ScopeResourceUsageNode,
)
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.defs import INTRINSIC_SLOTS
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.system import role_named
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import TestSeedResourceGroup
from bai_scenario.seeds.resource_policy.keypair import TestSeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.resource_preset.preset import TestSeedResourcePreset
from bai_scenario.seeds.resource_slot.slot_type import TestSeedResourceSlotType
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest, joined
from bai_scenario.seeds.user.fields import TestSeedKeypairOf

ZERO = Decimal("0")


@dataclass(frozen=True)
class AUsagePlace:
    """한 번의 사용량 조회가 묻는 자리와, 그 자리에서 부를 사용자."""

    domain: DomainData
    project: ProjectData
    group: ResourceGroupData
    caller: UserData
    access_key: AccessKey
    resource_policy: Mapping[str, Any]
    slot_name: str | None
    presets: tuple[ResourcePresetData, ...]


@dataclass(frozen=True)
class SomeoneGrantedReadInAScope(TestSeedNest[Laid[None]]):
    """스코프 하나에서 엔티티 하나를 읽을 수 있는 역할을 사용자에게 준다."""

    scope: Laid[Any]
    scope_of: Callable[[Any], EntityIdentifier]
    entity_type: EntityType
    holder: Laid[UserData]
    reading: Says

    @override
    def kind(self) -> str:
        return self.reading

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(TestSeedRole(self.scope_of, name_hint="reader"), self.scope)
        seed.adding(
            TestSeedPermission(entity_type=self.entity_type, permission=Permission.READ), role
        )
        return seed.granting(
            role, self.holder, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class APlaceAndSomeone(Given[Any, AUsagePlace]):
    """자리 하나와 사용자 한 명.

    ``sessions_read``, ``self_read``, ``project_read``, ``preset_read``, ``domain_read`` 는
    그 사용자에게 어느 범위에서 무엇을 읽을 권한이 있는지다. ``slot_type`` 이면 슬롯 종류를
    하나 두어 한도가 무한대로 채워지고, ``presets`` 가 0 보다 크면 그만큼 프리셋을 둔다.
    """

    role: UserRole = UserRole.USER
    sessions_read: bool = False
    self_read: bool = False
    project_read: bool = False
    preset_read: bool = False
    domain_read: bool = False
    slot_type: bool = True
    presets: int = 0

    @override
    def describe(self) -> str:
        named = role_named(self.role)
        named_en = in_language(named, Language.ENGLISH)
        parts = [Says(f"자리 하나와 {named} 한 명", english=f"one place and one {named_en}")]
        parts.extend(self._readings())
        if self.slot_type:
            parts.append(
                Says(
                    "슬롯 종류 하나가 등록되어 있습니다",
                    english="one resource slot type is registered",
                )
            )
        if self.presets:
            parts.append(
                Says(
                    f"프리셋 {self.presets}개가 있습니다",
                    english=(
                        "one preset exists"
                        if self.presets == 1
                        else f"{self.presets} presets exist"
                    ),
                )
            )
        return joined(parts, ". ")

    def _readings(self) -> list[Says]:
        said: list[Says] = []
        if self.sessions_read:
            said.append(
                Says(
                    "그 사용자는 프로젝트 범위에서 세션을 읽을 수 있습니다",
                    english="that user can read sessions in the project scope",
                )
            )
        if self.self_read:
            said.append(
                Says(
                    "그 사용자는 자기 사용자 범위에서 사용자를 읽을 수 있습니다",
                    english="that user can read users in their own user scope",
                )
            )
        if self.project_read:
            said.append(
                Says(
                    "그 사용자는 프로젝트 범위에서 프로젝트를 읽을 수 있습니다",
                    english="that user can read the project in the project scope",
                )
            )
        if self.preset_read:
            said.append(
                Says(
                    "그 사용자는 프로젝트 범위에서 리소스 프리셋을 읽을 수 있습니다",
                    english="that user can read resource presets in the project scope",
                )
            )
        if self.domain_read:
            said.append(
                Says(
                    "그 사용자는 도메인 범위에서 도메인을 읽을 수 있습니다",
                    english="that user can read the domain in the domain scope",
                )
            )
        return said

    def _grants(
        self, project: Laid[ProjectData], domain: Laid[DomainData], holder: Laid[UserData]
    ) -> list[SomeoneGrantedReadInAScope]:
        grants: list[SomeoneGrantedReadInAScope] = []
        if self.sessions_read:
            grants.append(
                SomeoneGrantedReadInAScope(
                    project,
                    lambda one: ProjectID(one.id),
                    SessionEntityType(),
                    holder,
                    Says(
                        "프로젝트 범위의 세션 조회 권한을 받은 사용자",
                        english="a user granted permission to read sessions in the project scope",
                    ),
                )
            )
        if self.self_read:
            grants.append(
                SomeoneGrantedReadInAScope(
                    holder,
                    lambda one: UserID(one.id),
                    UserEntityType(),
                    holder,
                    Says(
                        "자기 사용자 범위의 사용자 조회 권한을 받은 사용자",
                        english="a user granted permission to read users in their own user scope",
                    ),
                )
            )
        if self.project_read:
            grants.append(
                SomeoneGrantedReadInAScope(
                    project,
                    lambda one: ProjectID(one.id),
                    ProjectEntityType(),
                    holder,
                    Says(
                        "프로젝트 범위의 프로젝트 조회 권한을 받은 사용자",
                        english="a user granted permission to read the project in its scope",
                    ),
                )
            )
        if self.preset_read:
            grants.append(
                SomeoneGrantedReadInAScope(
                    project,
                    lambda one: ProjectID(one.id),
                    ResourcePresetEntityType(),
                    holder,
                    Says(
                        "프로젝트 범위의 리소스 프리셋 조회 권한을 받은 사용자",
                        english=(
                            "a user granted permission to read resource presets in the project "
                            "scope"
                        ),
                    ),
                )
            )
        if self.domain_read:
            grants.append(
                SomeoneGrantedReadInAScope(
                    domain,
                    lambda one: one.id,
                    DomainEntityType(),
                    holder,
                    Says(
                        "도메인 범위의 도메인 조회 권한을 받은 사용자",
                        english="a user granted permission to read the domain in its scope",
                    ),
                )
            )
        return grants

    @override
    async def lay(self, seeding: Any) -> AUsagePlace:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        project_policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(name_hint="team"), domain, project_policy
        )
        group = await seeding.creating(TestSeedResourceGroup(name_hint="group"))
        slot_name: str | None = None
        if self.slot_type:
            slot = await seeding.creating(TestSeedResourceSlotType(name_hint="slot"))
            slot_name = slot.name
        holder = await seeding.within(SomeoneOf(domain, role=self.role))
        key_policy = await seeding.creating(TestSeedKeypairPolicy())
        key = await seeding.adding(
            TestSeedKeypairOf(resource_policy=seeding.made(key_policy).name), holder
        )
        for read in self._grants(project, domain, holder):
            await seeding.within(read)
        presets = [await seeding.creating(TestSeedResourcePreset()) for _ in range(self.presets)]
        policy = seeding.made(key_policy)
        return AUsagePlace(
            domain=seeding.made(domain),
            project=seeding.made(project),
            group=seeding.made(group),
            caller=seeding.made(holder),
            access_key=seeding.made(key).access_key,
            resource_policy={
                "total_resource_slots": policy.total_resource_slots,
                "default_for_unspecified": policy.default_for_unspecified,
            },
            slot_name=slot_name,
            presets=tuple(seeding.made(one) for one in presets),
        )


def limit_entries(slot_name: str | None) -> list[ResourceLimitEntryInfo]:
    """A limit list: one unlimited entry when a slot type was laid, empty otherwise."""
    if slot_name is None:
        return []
    return [ResourceLimitEntryInfo(resource_type=slot_name, quantity=None, unlimited=True)]


def used_entries(slot_name: str | None) -> list[ResourceSlotEntryInfo]:
    """A usage list: one zero entry when a slot type was laid, empty otherwise."""
    if slot_name is None:
        return []
    return [ResourceSlotEntryInfo(resource_type=slot_name, quantity=ZERO)]


def intrinsic_limit_entries() -> list[ResourceLimitEntryInfo]:
    """The unlimited limit every intrinsic slot type gets from an unlimited policy."""
    return [
        ResourceLimitEntryInfo(resource_type=str(name), quantity=None, unlimited=True)
        for name in INTRINSIC_SLOTS
    ]


def intrinsic_used_entries() -> list[ResourceSlotEntryInfo]:
    """Every intrinsic slot type with nothing used."""
    return [
        ResourceSlotEntryInfo(resource_type=str(name), quantity=ZERO) for name in INTRINSIC_SLOTS
    ]


def scope_usage_verdicts(
    at: str, node: ScopeResourceUsageNode, slot_name: str | None
) -> list[Verdict]:
    """Every place of one scope usage node."""
    return [
        Same(f"{at}limits", node.limits, limit_entries(slot_name)),
        Same(f"{at}used", node.used, used_entries(slot_name)),
        Same(f"{at}assignable", node.assignable, limit_entries(slot_name)),
    ]


def effective_scope_verdicts(at: str, node: ScopeResourceUsageNode) -> list[Verdict]:
    """Every place of one scope usage node of the effective allocation.

    The effective path reads the intrinsic slots from the config loader, so the limits are
    the two intrinsic types rather than the registry the usage reads consult.
    """
    return [
        Same(f"{at}limits", node.limits, intrinsic_limit_entries()),
        Same(f"{at}used", node.used, intrinsic_used_entries()),
        Same(f"{at}assignable", node.assignable, intrinsic_limit_entries()),
    ]


def resource_group_usage_verdicts(
    at: str, node: ResourceGroupUsageNode, slot_name: str | None
) -> list[Verdict]:
    """Every place of one resource group usage node. No agent reports a slot, so all are empty."""
    del slot_name
    return [
        Same(f"{at}capacity", node.capacity, []),
        Same(f"{at}used", node.used, []),
        Same(f"{at}free", node.free, []),
        Same(f"{at}max_per_node", node.max_per_node, []),
    ]


def effective_verdicts(
    payload: EffectiveResourceAllocationPayload,
    *,
    project: bool,
    resource_group: bool,
) -> list[Verdict]:
    """Every place of one effective allocation payload."""
    breakdown: EffectiveBreakdownNode = payload.breakdown
    verdicts: list[Verdict] = [
        Same("assignable", payload.assignable, intrinsic_limit_entries()),
        *effective_scope_verdicts("breakdown.keypair.", breakdown.keypair),
        *effective_scope_verdicts("breakdown.domain.", breakdown.domain),
    ]
    if project:
        if breakdown.project is None:
            verdicts.append(Same("breakdown.project", None, Says("노드", english="a node")))
        else:
            verdicts += effective_scope_verdicts("breakdown.project.", breakdown.project)
    else:
        verdicts.append(Same("breakdown.project", breakdown.project, None))
    if resource_group:
        if breakdown.resource_group is None:
            verdicts.append(Same("breakdown.resource_group", None, Says("노드", english="a node")))
        else:
            verdicts += resource_group_usage_verdicts(
                "breakdown.resource_group.", breakdown.resource_group, None
            )
    else:
        verdicts.append(Same("breakdown.resource_group", breakdown.resource_group, None))
    return verdicts


@dataclass(frozen=True)
class TheEffectiveAllocation(Then[AUsagePlace, EffectiveResourceAllocationPayload]):
    """유효 할당 전체가 온다. 어느 범위를 보여 줄지는 설정과 호출자 역할이 정한다."""

    project: bool
    resource_group: bool

    @override
    def says(self) -> str:
        parts = ["유효 할당 전체가 응답으로 옵니다"]
        if self.project:
            parts.append("프로젝트 범위가 담깁니다")
        else:
            parts.append("프로젝트 범위는 담기지 않습니다")
        if self.resource_group:
            parts.append("자원 그룹 범위가 담깁니다")
        else:
            parts.append("자원 그룹 범위는 담기지 않습니다")
        return Says(
            ". ".join(parts),
            english=(
                "the whole effective allocation comes back. "
                + (
                    "the project scope is included. "
                    if self.project
                    else "the project scope is absent. "
                )
                + (
                    "the resource group scope is included"
                    if self.resource_group
                    else "the resource group scope is absent"
                )
            ),
        )

    @override
    def look(
        self, laid: AUsagePlace, answered: Answered[EffectiveResourceAllocationPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return effective_verdicts(
            payload,
            project=self.project,
            resource_group=self.resource_group,
        )


@dataclass(frozen=True)
class ThePresetAvailability(Then[AUsagePlace, CheckPresetAvailabilityPayload]):
    """미리 만들어 둔 프리셋이 모두 오고, 자원 그룹에 에이전트가 없어 모두 쓸 수 있는 것으로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 프리셋이 모두 쓰일 수 있는 것으로 응답으로 옵니다",
            english="every preset seeded in advance comes back marked as available",
        )

    @override
    def look(
        self, laid: AUsagePlace, answered: Answered[CheckPresetAvailabilityPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        if len(payload.presets) != len(laid.presets):
            return [Same("len(presets)", len(payload.presets), len(laid.presets))]
        by_name = {node.name: node for node in payload.presets}
        verdicts: list[Verdict] = [Same("len(presets)", len(payload.presets), len(laid.presets))]
        for i, preset in enumerate(laid.presets):
            node = by_name.get(preset.name)
            if node is None:
                verdicts.append(
                    Same(
                        f"presets[{i}].name",
                        None,
                        Says(preset.name, english=preset.name),
                    )
                )
                continue
            verdicts += [
                Held[Any](
                    f"presets[{i}].id",
                    node.id,
                    SameAs(
                        preset.id,
                        Says(
                            "미리 저장한 프리셋의 id",
                            english="the id of the preset seeded in advance",
                        ),
                    ),
                ),
                Same(f"presets[{i}].name", node.name, preset.name),
                Same(
                    f"presets[{i}].resource_slots",
                    sorted(node.resource_slots, key=lambda entry: entry.resource_type),
                    sorted(
                        (
                            ResourceSlotEntryInfo(resource_type=k, quantity=v)
                            for k, v in preset.resource_slots.items()
                        ),
                        key=lambda entry: entry.resource_type,
                    ),
                ),
                Same(f"presets[{i}].shared_memory", node.shared_memory, None),
                Same(f"presets[{i}].resource_group_name", node.resource_group_name, None),
                Same(f"presets[{i}].available", node.available, True),
            ]
        return verdicts
