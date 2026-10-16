"""What a resource preset scenario table says besides the call.

A preset bound to no resource group sits in public. A table needs the caller and the
preset or presets the call writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInfo,
    PartialBulkPayload,
    ResourceSlotEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import ResourcePresetNode
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ResourcePresetNotFound
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, Mentions, SomeoneOf
from bai_scenario.components.system import role_named
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_preset.preset import TestSeedResourcePreset
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest


@dataclass(frozen=True)
class APresetAndACaller:
    """프리셋 하나와, 그것을 부를 사람."""

    preset: ResourcePresetData
    caller: UserData


@dataclass(frozen=True)
class ManyPresetsAndACaller:
    """프리셋 여럿과, 그것들을 부를 사람."""

    laid: tuple[ResourcePresetData, ...]
    caller: UserData


@dataclass(frozen=True)
class SomeoneGrantedInPublic(TestSeedNest[Laid[UserData]]):
    """public 에서 리소스 프리셋에 대한 권한 하나를 받은 사용자."""

    domain: Laid[Any]
    permission: Permission

    @override
    def kind(self) -> str:
        return f"public 에서 리소스 프리셋 {self.permission.name} 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        granted = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.PUBLIC), name_hint="preset-writer"
            ),
            someone,
        )
        seed.adding(
            TestSeedPermission(entity_type=ResourcePresetEntityType(), permission=self.permission),
            granted,
        )
        seed.granting(granted, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def _lay_caller(seeding: Any, role: UserRole, granted: Permission | None) -> Laid[UserData]:
    home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
    caller: Laid[UserData]
    if granted is not None:
        caller = await seeding.within(SomeoneGrantedInPublic(home, granted))
    else:
        caller = await seeding.within(SomeoneOf(home, role=role))
    return caller


def _caller_named(role: UserRole, granted: Permission | None) -> str:
    if granted is not None:
        return f"public 에서 {granted.name} 권한을 받은 일반 사용자"
    return role_named(role)


@dataclass(frozen=True)
class APresetAndSomeone(Given[Any, APresetAndACaller]):
    """프리셋 하나와 사용자 한 명. `granted`가 있으면 public 에서 그 권한을 받는다."""

    role: UserRole = UserRole.USER
    granted: Permission | None = None

    @override
    def describe(self) -> str:
        return f"프리셋 하나와 {_caller_named(self.role, self.granted)} 한 명"

    @override
    async def lay(self, seeding: Any) -> APresetAndACaller:
        preset = await seeding.creating(TestSeedResourcePreset())
        caller = await _lay_caller(seeding, self.role, self.granted)
        return APresetAndACaller(seeding.made(preset), seeding.made(caller))


@dataclass(frozen=True)
class ManyPresetsAndSomeone(Given[Any, ManyPresetsAndACaller]):
    """프리셋 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return f"프리셋 {self.count}개와 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        presets = [await seeding.creating(TestSeedResourcePreset()) for _ in range(self.count)]
        caller = await _lay_caller(seeding, self.role, None)
        return ManyPresetsAndACaller(
            laid=tuple(seeding.made(one) for one in presets),
            caller=seeding.made(caller),
        )


def preset_verdicts(
    at: str,
    node: ResourcePresetNode,
    laid: ResourcePresetData,
    *,
    named: str | None = None,
    shared_memory: BinarySizeInfo | None = None,
) -> list[Verdict]:
    """Every place of one preset node, against the row the seed laid and the edit asked."""
    return [
        Held[UUID](f"{at}id", node.id, SameAs(laid.id, "미리 만든 프리셋의 id")),
        Held[UUID](f"{at}entity_id", node.entity_id, SameAs(laid.id, "미리 만든 프리셋의 id")),
        Same(f"{at}name", node.name, named if named is not None else laid.name),
        Same(
            f"{at}resource_slots",
            node.resource_slots,
            [
                ResourceSlotEntryInfo(resource_type=k, quantity=v)
                for k, v in laid.resource_slots.items()
            ],
        ),
        Same(f"{at}shared_memory", node.shared_memory, shared_memory),
        Same(f"{at}resource_group_name", node.resource_group_name, None),
    ]


@dataclass(frozen=True)
class ThePresetNode(Then[APresetAndACaller, ResourcePresetNode]):
    """미리 만든 프리셋 전체가 온다. 수정한 이름만 바뀐다."""

    named: str | None = None

    @override
    def says(self) -> str:
        return "미리 만든 프리셋 전체가 온다"

    @override
    def look(
        self, laid: APresetAndACaller, answered: Answered[ResourcePresetNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(ResourcePresetNotFound, answered.raised)]
        return preset_verdicts("", node, laid.preset, named=self.named)


@dataclass(frozen=True)
class ThePurgedPresetId(Then[APresetAndACaller, UUID]):
    """지운 프리셋의 id 가 온다."""

    @override
    def says(self) -> str:
        return "지운 프리셋의 id 가 온다"

    @override
    def look(self, laid: APresetAndACaller, answered: Answered[UUID]) -> list[Verdict]:
        purged = answered.response
        if purged is None:
            return [Refused(ResourcePresetNotFound, answered.raised)]
        return [Held[UUID]("id", purged, SameAs(laid.preset.id, "미리 만든 프리셋의 id"))]


@dataclass(frozen=True)
class NoPresetIsProcessed(Then[ManyPresetsAndACaller, PartialBulkPayload[ResourcePresetNode]]):
    """처리된 프리셋 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 프리셋 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: ManyPresetsAndACaller,
        answered: Answered[PartialBulkPayload[ResourcePresetNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.laid)),
        ]
        for i, (failure, preset) in enumerate(zip(payload.failed, laid.laid, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(preset.id, "대상 프리셋의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class EveryPresetComesBack(Then[ManyPresetsAndACaller, PartialBulkPayload[ResourcePresetNode]]):
    """대상이 모두 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    shared_memory: BinarySizeInfo | None = None
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return "대상 프리셋이 모두 처리된 목록에 오고, 실패한 것은 없다"
        return "대상 프리셋이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"

    @override
    def look(
        self,
        laid: ManyPresetsAndACaller,
        answered: Answered[PartialBulkPayload[ResourcePresetNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, preset) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += preset_verdicts(
                f"successes[{i}].", node, preset, shared_memory=self.shared_memory
            )
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts
