"""What a role preset scenario table says besides the call.

A preset lives in the global scope: nothing scopes it, so a table lays the presets and a
caller side by side and never a role between them.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    RolePermissionPresetNode,
)
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData, RolePresetData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.components.system import lay_a_caller
from bai_scenario.seeds.role_preset.preset import TestSeedRolePreset, TestSeedRolePresetPermission

ENTRIES: tuple[tuple[str, PermissionBitDTO], ...] = (
    ("domain", PermissionBitDTO.READ),
    ("project", PermissionBitDTO.UPDATE),
)
"""The entries a row adds to a preset carrying none."""


@dataclass(frozen=True)
class APresetAndACaller:
    """이미 있는 프리셋 하나와, 그것을 호출할 사용자."""

    preset: RolePresetData
    caller: UserData


@dataclass(frozen=True)
class ManyPresetsAndACaller:
    """한 번에 다룰 프리셋 여럿과, 호출할 사용자."""

    laid: tuple[RolePresetData, ...]
    caller: UserData


@dataclass(frozen=True)
class APresetWithEntriesAndACaller:
    """권한 항목을 가진 프리셋 하나와, 호출할 사용자."""

    preset: RolePresetData
    entries: tuple[RolePermissionPresetData, ...]
    caller: UserData


@dataclass(frozen=True)
class APresetAndSomeone(Given[Any, APresetAndACaller]):
    """이미 있는 프리셋 하나와, 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"이미 있는 프리셋 하나와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> APresetAndACaller:
        preset = await seeding.creating(TestSeedRolePreset())
        caller = await lay_a_caller(seeding, self.role)
        return APresetAndACaller(preset=seeding.made(preset), caller=seeding.made(caller))


@dataclass(frozen=True)
class ManyPresetsAndSomeone(Given[Any, ManyPresetsAndACaller]):
    """프리셋 여럿과, 호출자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return f"프리셋 {self.count}개와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        laid = [await seeding.creating(TestSeedRolePreset()) for _ in range(self.count)]
        caller = await lay_a_caller(seeding, self.role)
        return ManyPresetsAndACaller(
            laid=tuple(seeding.made(one) for one in laid), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class APresetWithEntriesAndSomeone(Given[Any, APresetWithEntriesAndACaller]):
    """권한 항목 둘을 가진 프리셋 하나와, 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"권한 항목 둘을 가진 프리셋 하나와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> APresetWithEntriesAndACaller:
        preset = await seeding.creating(TestSeedRolePreset())
        entries = [
            await seeding.adding(
                TestSeedRolePresetPermission(DomainEntityType(), Permission.READ), preset
            ),
            await seeding.adding(
                TestSeedRolePresetPermission(ProjectEntityType(), Permission.UPDATE), preset
            ),
        ]
        caller = await lay_a_caller(seeding, self.role)
        return APresetWithEntriesAndACaller(
            preset=seeding.made(preset),
            entries=tuple(seeding.made(one) for one in entries),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class PresetLook:
    """노드 하나를 미리 만든 프리셋과 맞춰 본다. 바뀌어야 하는 값만 인자로 받는다."""

    started: datetime
    named: str | None = None
    auto_assign: bool | None = None
    deleted: bool = False

    def verdicts(self, at: str, node: RolePresetNode, seeded: RolePresetData) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        return [
            Held[UUID](f"{at}id", node.id, SameAs(seeded.id, "미리 만든 프리셋의 id")),
            Held[UUID](
                f"{at}entity_id", node.entity_id, SameAs(seeded.id, "미리 만든 프리셋의 id")
            ),
            Same(f"{at}name", node.name, self.named if self.named is not None else seeded.name),
            Same(f"{at}scope_type", str(node.scope_type), str(seeded.scope_type)),
            Same(
                f"{at}auto_assign",
                node.auto_assign,
                self.auto_assign if self.auto_assign is not None else seeded.auto_assign,
            ),
            Same(f"{at}deleted", node.deleted, self.deleted),
            Held(f"{at}created_at", node.created_at, written),
            Held(f"{at}updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class ThePresetComesBack(Then[APresetAndACaller, RolePresetNode]):
    """미리 만든 프리셋이 통째로 온다. 바뀌어야 하는 값은 `expected`가 말한다."""

    expected: PresetLook

    @override
    def says(self) -> str:
        if self.expected.named is not None:
            return "새 이름을 실은 프리셋 전체가 온다"
        if self.expected.deleted:
            return "삭제 표시가 켜진 프리셋 전체가 온다"
        return "삭제 표시가 꺼진 프리셋 전체가 온다"

    @override
    def look(self, laid: APresetAndACaller, answered: Answered[RolePresetNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return self.expected.verdicts("", node, laid.preset)


@dataclass(frozen=True)
class EveryTargetComesBack(Then[ManyPresetsAndACaller, PartialBulkPayload[RolePresetNode]]):
    """대상이 모두 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    expected: PresetLook
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.expected.auto_assign is not None:
            done = "새 값으로"
        elif self.expected.deleted:
            done = "삭제 표시가 켜진 채"
        else:
            done = "삭제 표시가 꺼진 채"
        if self.missing is None:
            return f"대상 프리셋이 모두 {done} 오고, 실패한 것은 없다"
        return f"대상 프리셋이 모두 {done} 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"

    @override
    def look(
        self,
        laid: ManyPresetsAndACaller,
        answered: Answered[PartialBulkPayload[RolePresetNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, preset) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += self.expected.verdicts(f"successes[{i}].", node, preset)
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NothingIsProcessed(Then[Any, PartialBulkPayload[Any]]):
    """처리된 것 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 것 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(self, laid: Any, answered: Answered[PartialBulkPayload[Any]]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = targets_of(laid)
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(targets)),
        ]
        for i, (failure, target) in enumerate(zip(payload.failed, targets, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(target, "대상의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


def targets_of(laid: Any) -> Sequence[UUID]:
    """여럿 연산이 한 번에 다루는 대상의 id. 프리셋 여럿이면 프리셋, 항목이 있으면 항목이다."""
    if isinstance(laid, APresetWithEntriesAndACaller):
        return [entry.id for entry in laid.entries]
    return [preset.id for preset in laid.laid]


@dataclass(frozen=True)
class TheEntriesAreAdded(Then[APresetAndACaller, list[RolePermissionPresetNode]]):
    """넣은 항목이 요청한 순서대로, 그 프리셋 아래에 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "넣은 두 항목이 프리셋 아래에 온다"

    @override
    def look(
        self, laid: APresetAndACaller, answered: Answered[list[RolePermissionPresetNode]]
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        got = sorted(items, key=lambda one: str(one.entity_type))
        verdicts: list[Verdict] = [Same("items count", len(items), len(ENTRIES))]
        for i, (node, (entity_type, permission)) in enumerate(zip(got, ENTRIES, strict=False)):
            verdicts += [
                Skipped(f"items[{i}].id", "데이터베이스가 만든다"),
                Skipped(f"items[{i}].field_id", "데이터베이스가 만든다"),
                Held[UUID](
                    f"items[{i}].role_preset_id",
                    node.role_preset_id,
                    SameAs(laid.preset.id, "미리 만든 프리셋의 id"),
                ),
                Same(f"items[{i}].entity_type", str(node.entity_type), entity_type),
                Same(f"items[{i}].permission", node.permission, permission),
                Held(f"items[{i}].created_at", node.created_at, written),
            ]
        return verdicts


@dataclass(frozen=True)
class TheEntriesAreRemoved(
    Then[APresetWithEntriesAndACaller, PartialBulkPayload[RolePermissionPresetNode]]
):
    """뺀 항목이 처리된 목록에 온다. `missing`이 있으면 그 id 는 실패 목록에 온다."""

    missing: UUID

    @override
    def says(self) -> str:
        return "뺀 두 항목이 처리된 목록에 오고, 없는 id 는 실패 목록에 온다"

    @override
    def look(
        self,
        laid: APresetWithEntriesAndACaller,
        answered: Answered[PartialBulkPayload[RolePermissionPresetNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        got = sorted(payload.successes, key=lambda one: str(one.entity_type))
        wanted = sorted(laid.entries, key=lambda one: str(one.entity_type))
        verdicts: list[Verdict] = [Same("successes count", len(got), len(wanted))]
        for i, (node, entry) in enumerate(zip(got, wanted, strict=False)):
            verdicts += [
                Held[UUID](f"successes[{i}].id", node.id, SameAs(entry.id, "미리 만든 항목의 id")),
                Held[UUID](
                    f"successes[{i}].field_id",
                    node.field_id,
                    SameAs(entry.id, "미리 만든 항목의 id"),
                ),
                Held[UUID](
                    f"successes[{i}].role_preset_id",
                    node.role_preset_id,
                    SameAs(laid.preset.id, "미리 만든 프리셋의 id"),
                ),
                Same(f"successes[{i}].entity_type", str(node.entity_type), str(entry.entity_type)),
                Same(
                    f"successes[{i}].permission",
                    node.permission,
                    PermissionBitDTO.of(entry.permission),
                ),
                Held[datetime](
                    f"successes[{i}].created_at",
                    node.created_at,
                    SameAs(entry.created_at, "미리 만든 항목의 시각"),
                ),
            ]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts
