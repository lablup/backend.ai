"""What a role preset scenario table says besides the call.

A preset lives in the global scope: nothing scopes it, so a table lays the presets and a
caller side by side and never a role between them.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast, override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    RolePermissionPresetNode,
    SearchRolePermissionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    RolePresetNode,
    SearchRolePresetsPayload,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
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
    Says,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, Mentions, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.role_preset.preset import TestSeedRolePreset, TestSeedRolePresetPermission
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest

ENTRIES: tuple[tuple[str, PermissionBitDTO], ...] = (
    ("domain", PermissionBitDTO.READ),
    ("project", PermissionBitDTO.UPDATE),
)
"""The entries a row adds to a preset carrying none."""


@dataclass(frozen=True)
class SomeoneGrantedOnPresets(TestSeedNest[Laid[UserData]]):
    """global 에서 역할 프리셋에 대한 권한 하나를 받은 사용자.

    프리셋은 global 스코프에 만들어지므로, 읽으려면 global 스코프에 만든 역할이 그 권한을
    가져야 한다.
    """

    domain: Laid[Any]
    permission: Permission
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return Says(
            f"global 에서 역할 프리셋 {self.permission.name} 권한을 받은 사용자 준비",
            english=(
                f"Prepare a user granted the {self.permission.name} permission "
                "on role presets in global"
            ),
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        role = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.GLOBAL), name_hint="preset-reader"
            ),
            someone,
        )
        seed.adding(
            TestSeedPermission(entity_type=RolePresetEntityType(), permission=self.permission),
            role,
        )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def _lay_caller(seeding: Any, role: UserRole, granted: Permission | None) -> Laid[UserData]:
    """A user of the given role, granted the permission on role presets when given."""
    home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
    if granted is not None:
        return cast(
            "Laid[UserData]",
            await seeding.within(SomeoneGrantedOnPresets(home, granted, role=role)),
        )
    return cast("Laid[UserData]", await seeding.within(SomeoneOf(home, role=role)))


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
    scope_type: EntityType = ProjectEntityType()
    granted: Permission | None = None
    auto_assign: bool = False
    auto_assign_to_owner: bool = False
    role_name_template: str | None = None

    @override
    def describe(self) -> str:
        role = self.role.value
        if self.granted is not None:
            if self.scope_type == ProjectEntityType():
                base_ko = "이미 있는 프리셋 하나와"
                base_en = "one preset that already exists and"
            else:
                base_ko = f"이미 있는 {self.scope_type} 스코프 프리셋 하나와"
                base_en = f"one preset that already exists in the {self.scope_type} scope and"
            return Says(
                f"{base_ko}, global 에서 {self.granted.name} 권한을 받은 {role} 한 명",
                english=f"{base_en} one {role} granted {self.granted.name} in global",
            )
        if self.scope_type == ProjectEntityType():
            return Says(
                f"이미 있는 프리셋 하나와, {role} 한 명",
                english=f"one preset that already exists and one {role}",
            )
        return Says(
            f"이미 있는 {self.scope_type} 스코프 프리셋 하나와, {role} 한 명",
            english=f"one preset that already exists in the {self.scope_type} scope and one {role}",
        )

    @override
    async def lay(self, seeding: Any) -> APresetAndACaller:
        preset = await seeding.creating(
            TestSeedRolePreset(
                scope_type=self.scope_type,
                auto_assign=self.auto_assign,
                auto_assign_to_owner=self.auto_assign_to_owner,
                role_name_template=self.role_name_template,
            )
        )
        caller = await _lay_caller(seeding, self.role, self.granted)
        return APresetAndACaller(preset=seeding.made(preset), caller=seeding.made(caller))


@dataclass(frozen=True)
class AProjectAndADomainPresetAndSomeone(Given[Any, ManyPresetsAndACaller]):
    """프로젝트 스코프 프리셋 하나, 도메인 스코프 프리셋 하나와, 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        role = self.role.value
        return Says(
            f"프로젝트 스코프 프리셋과 도메인 스코프 프리셋 하나씩과, {role} 한 명",
            english=(f"one project-scope preset, one domain-scope preset, and one {role}"),
        )

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        project = await seeding.creating(TestSeedRolePreset())
        domain = await seeding.creating(TestSeedRolePreset(scope_type=DomainEntityType()))
        caller = await _lay_caller(seeding, self.role, None)
        return ManyPresetsAndACaller(
            laid=(seeding.made(project), seeding.made(domain)), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class ManyPresetsAndSomeone(Given[Any, ManyPresetsAndACaller]):
    """프리셋 여럿과, 호출자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2
    granted: Permission | None = None

    @override
    def describe(self) -> str:
        role = self.role.value
        if self.granted is not None:
            return Says(
                f"프리셋 {self.count}개와, global 에서 {self.granted.name} 권한을 받은 {role} 한 명",
                english=(
                    f"{self.count} presets and one {role} granted {self.granted.name} in global"
                ),
            )
        return Says(
            f"프리셋 {self.count}개와, {role} 한 명",
            english=f"{self.count} presets and one {role}",
        )

    @override
    async def lay(self, seeding: Any) -> ManyPresetsAndACaller:
        laid = [await seeding.creating(TestSeedRolePreset()) for _ in range(self.count)]
        caller = await _lay_caller(seeding, self.role, self.granted)
        return ManyPresetsAndACaller(
            laid=tuple(seeding.made(one) for one in laid), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class APresetWithEntriesAndSomeone(Given[Any, APresetWithEntriesAndACaller]):
    """권한 항목 둘을 가진 프리셋 하나와, 호출자 한 명."""

    role: UserRole = UserRole.USER
    granted: Permission | None = None

    @override
    def describe(self) -> str:
        role = self.role.value
        if self.granted is not None:
            return Says(
                f"권한 항목 둘을 가진 프리셋 하나와, "
                f"global 에서 {self.granted.name} 권한을 받은 {role} 한 명",
                english=(
                    "one preset with two permission entries and one "
                    f"{role} granted {self.granted.name} in global"
                ),
            )
        return Says(
            f"권한 항목 둘을 가진 프리셋 하나와, {role} 한 명",
            english=f"one preset with two permission entries and one {role}",
        )

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
        caller = await _lay_caller(seeding, self.role, self.granted)
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
    auto_assign_to_owner: bool | None = None
    deleted: bool = False

    def verdicts(self, at: str, node: RolePresetNode, seeded: RolePresetData) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        owner_assign: list[Verdict] = (
            [Same(f"{at}auto_assign_to_owner", node.auto_assign_to_owner, True)]
            if self.auto_assign_to_owner
            else []
        )
        return [
            *owner_assign,
            Held[UUID](
                f"{at}id",
                node.id,
                SameAs(
                    seeded.id,
                    Says(
                        "미리 저장한 프리셋의 id",
                        english="the id of the preset seeded in advance",
                    ),
                ),
            ),
            Held[UUID](
                f"{at}entity_id",
                node.entity_id,
                SameAs(
                    seeded.id,
                    Says(
                        "미리 저장한 프리셋의 id",
                        english="the id of the preset seeded in advance",
                    ),
                ),
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
            return Says(
                "새 이름을 담은 프리셋 전체가 응답으로 옵니다",
                english="the whole preset carrying the new name comes back",
            )
        if self.expected.auto_assign_to_owner:
            return Says(
                "소유자 부여가 켜진 프리셋 전체가 응답으로 옵니다",
                english="the whole preset with owner assignment turned on comes back",
            )
        if self.expected.deleted:
            return Says(
                "삭제로 표시된 프리셋 전체가 응답으로 옵니다",
                english="the whole preset marked deleted comes back",
            )
        return Says(
            "삭제로 표시되지 않은 프리셋 전체가 응답으로 옵니다",
            english="the whole preset not marked deleted comes back",
        )

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
            done_ko, done_en = "새 값으로", "with the new value"
        elif self.expected.deleted:
            done_ko, done_en = "삭제로 표시된 채", "marked deleted"
        else:
            done_ko, done_en = "삭제로 표시되지 않은 채", "not marked deleted"
        if self.missing is None:
            return Says(
                f"대상 프리셋이 모두 {done_ko} 오고, 실패한 것은 없습니다",
                english=f"every target preset comes back {done_en}, and nothing failed",
            )
        return Says(
            f"대상 프리셋이 모두 {done_ko} 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                f"every target preset comes back {done_en}, and an unknown id comes back "
                "in the failed list because no target answers to it"
            ),
        )

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
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class OnlyTheFirstPresetComesBack(Then[ManyPresetsAndACaller, PartialBulkPayload[RolePresetNode]]):
    """처음 프리셋만 처리되고, 나머지 하나는 실패 목록에 온다."""

    expected: PresetLook

    @override
    def says(self) -> str:
        return Says(
            "프로젝트 스코프 프리셋만 수정되어 오고, 도메인 스코프 프리셋은 실패 목록에 옵니다",
            english=(
                "only the project-scope preset comes back edited, and the domain-scope "
                "preset comes back in the failed list"
            ),
        )

    @override
    def look(
        self,
        laid: ManyPresetsAndACaller,
        answered: Answered[PartialBulkPayload[RolePresetNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), 1),
            Same("failed count", len(payload.failed), 1),
        ]
        for node in payload.successes:
            verdicts += self.expected.verdicts("successes[0].", node, laid.laid[0])
        for failure in payload.failed:
            verdicts.append(
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        laid.laid[1].id,
                        Says("두 번째 프리셋의 id", english="the id of the second preset"),
                    ),
                )
            )
        return verdicts


@dataclass(frozen=True)
class NothingIsProcessed(Then[Any, PartialBulkPayload[Any]]):
    """처리된 것 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 것 없이 대상이 모두 실패 목록에 옵니다",
            english="nothing is processed and every target comes back in the failed list",
        )

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
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(target, Says("대상의 id", english="the id of the target")),
                ),
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
        return Says(
            "추가한 두 항목이 프리셋 아래에 옵니다",
            english="the two entries added come back under the preset",
        )

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
                Skipped(
                    f"items[{i}].id",
                    Says("데이터베이스가 생성합니다", english="the database generates it"),
                ),
                Skipped(
                    f"items[{i}].field_id",
                    Says("데이터베이스가 생성합니다", english="the database generates it"),
                ),
                Held[UUID](
                    f"items[{i}].role_preset_id",
                    node.role_preset_id,
                    SameAs(
                        laid.preset.id,
                        Says(
                            "미리 저장한 프리셋의 id",
                            english="the id of the preset seeded in advance",
                        ),
                    ),
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
        return Says(
            "제거한 두 항목이 처리된 목록에 오고, 없는 id 는 실패 목록에 옵니다",
            english=(
                "the two entries removed come back in the processed list, "
                "and the unknown id comes back in the failed list"
            ),
        )

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
                Held[UUID](
                    f"successes[{i}].id",
                    node.id,
                    SameAs(
                        entry.id,
                        Says(
                            "미리 저장한 항목의 id",
                            english="the id of the entry seeded in advance",
                        ),
                    ),
                ),
                Held[UUID](
                    f"successes[{i}].field_id",
                    node.field_id,
                    SameAs(
                        entry.id,
                        Says(
                            "미리 저장한 항목의 id",
                            english="the id of the entry seeded in advance",
                        ),
                    ),
                ),
                Held[UUID](
                    f"successes[{i}].role_preset_id",
                    node.role_preset_id,
                    SameAs(
                        laid.preset.id,
                        Says(
                            "미리 저장한 프리셋의 id",
                            english="the id of the preset seeded in advance",
                        ),
                    ),
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
                    SameAs(
                        entry.created_at,
                        Says(
                            "미리 저장한 항목의 시각",
                            english="the time of the entry seeded in advance",
                        ),
                    ),
                ),
            ]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


def preset_read_verdicts(at: str, node: RolePresetNode, seeded: RolePresetData) -> list[Verdict]:
    """Every place of one preset node, against the row the seed laid."""
    preset_id = Says("미리 저장한 프리셋의 id", english="the id of the preset seeded in advance")
    written = Says("미리 저장한 프리셋의 시각", english="the time the preset was seeded")
    return [
        Held[UUID](f"{at}id", node.id, SameAs(seeded.id, preset_id)),
        Held[UUID](f"{at}entity_id", node.entity_id, SameAs(seeded.id, preset_id)),
        Same(f"{at}name", node.name, seeded.name),
        Same(f"{at}scope_type", node.scope_type, str(seeded.scope_type)),
        Same(f"{at}role_name_template", node.role_name_template, seeded.role_name_template),
        Same(f"{at}auto_assign", node.auto_assign, seeded.auto_assign),
        Same(f"{at}auto_assign_to_owner", node.auto_assign_to_owner, seeded.auto_assign_to_owner),
        Same(f"{at}deleted", node.deleted, seeded.deleted_at is not None),
        Same(f"{at}deleted_at", node.deleted_at, seeded.deleted_at),
        Held[datetime](f"{at}created_at", node.created_at, SameAs(seeded.created_at, written)),
        Held[datetime](f"{at}updated_at", node.updated_at, SameAs(seeded.updated_at, written)),
    ]


def permission_read_verdicts(
    at: str,
    node: RolePermissionPresetNode,
    entry: RolePermissionPresetData,
    preset: RolePresetData,
) -> list[Verdict]:
    """Every place of one permission entry node, against the row the seed laid."""
    entry_id = Says("미리 저장한 항목의 id", english="the id of the entry seeded in advance")
    preset_id = Says("미리 저장한 프리셋의 id", english="the id of the preset seeded in advance")
    written = Says("미리 저장한 항목의 시각", english="the time the entry was seeded")
    return [
        Held[UUID](f"{at}id", node.id, SameAs(entry.id, entry_id)),
        Held[UUID](f"{at}field_id", node.field_id, SameAs(entry.id, entry_id)),
        Held[UUID](f"{at}role_preset_id", node.role_preset_id, SameAs(preset.id, preset_id)),
        Same(f"{at}entity_type", str(node.entity_type), str(entry.entity_type)),
        Same(f"{at}permission", node.permission, PermissionBitDTO.of(entry.permission)),
        Held[datetime](f"{at}created_at", node.created_at, SameAs(entry.created_at, written)),
    ]


def _named_count(laid: Any) -> int:
    """How many ids the bulk read named: presets, or permission entries."""
    if isinstance(laid, APresetWithEntriesAndACaller):
        return len(laid.entries)
    return len(laid.laid)


@dataclass(frozen=True)
class TheWholePreset(Then[APresetAndACaller, RolePresetNode]):
    """미리 만든 프리셋 전체가 온다. 필드를 빠뜨리지 않고 본다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 프리셋 전체가 반환됩니다",
            english="the whole preset seeded in advance comes back",
        )

    @override
    def look(self, laid: APresetAndACaller, answered: Answered[RolePresetNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return preset_read_verdicts("", node, laid.preset)


@dataclass(frozen=True)
class TheWholePresetsInOrder(Then[ManyPresetsAndACaller, list[RolePresetNode | Exception | None]]):
    """미리 만든 프리셋이 요청한 순서대로, 각각 전체가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 프리셋이 요청한 순서대로 반환됩니다",
            english="the presets seeded in advance come back in the requested order",
        )

    @override
    def look(
        self,
        laid: ManyPresetsAndACaller,
        answered: Answered[list[RolePresetNode | Exception | None]],
    ) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(got), len(laid.laid))]
        for i, (one, seeded) in enumerate(zip(got, laid.laid, strict=False)):
            if isinstance(one, RolePresetNode):
                verdicts += preset_read_verdicts(f"[{i}].", one, seeded)
            else:
                verdicts.append(MissingResponse(one if isinstance(one, BaseException) else None))
        return verdicts


@dataclass(frozen=True)
class TheWholePermissionsInOrder(
    Then[APresetWithEntriesAndACaller, list[RolePermissionPresetNode | Exception | None]]
):
    """미리 만든 권한 항목이 요청한 순서대로, 각각 전체가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 권한 항목이 요청한 순서대로 반환됩니다",
            english="the entries seeded in advance come back in the requested order",
        )

    @override
    def look(
        self,
        laid: APresetWithEntriesAndACaller,
        answered: Answered[list[RolePermissionPresetNode | Exception | None]],
    ) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(got), len(laid.entries))]
        for i, (one, entry) in enumerate(zip(got, laid.entries, strict=False)):
            if isinstance(one, RolePermissionPresetNode):
                verdicts += permission_read_verdicts(f"[{i}].", one, entry, laid.preset)
            else:
                verdicts.append(MissingResponse(one if isinstance(one, BaseException) else None))
        return verdicts


@dataclass(frozen=True)
class EveryEntryIsDenied(Then[Any, list[Any]]):
    """부르기를 거부하지 않고, 요청한 항목마다 권한 부족 거부가 담겨 온다."""

    @override
    def says(self) -> str:
        return Says(
            "항목마다 권한 부족 거부가 담겨 반환됩니다",
            english="every entry comes back holding a rejection for lack of permission",
        )

    @override
    def look(self, laid: Any, answered: Answered[list[Any]]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("length", len(got), _named_count(laid)),
            *[
                Refused(NotEnoughPermission, one if isinstance(one, BaseException) else None)
                for one in got
            ],
        ]


@dataclass(frozen=True)
class PresetsToFind:
    """한 페이지에 담길 프리셋들, 필터가 걸러 낼 프리셋, 그리고 호출자."""

    matching: tuple[RolePresetData, ...]
    filtered_out: RolePresetData
    caller: UserData


@dataclass(frozen=True)
class ProjectPresetsAndADomainOne(Given[Any, PresetsToFind]):
    """프로젝트 스코프 프리셋 둘, 도메인 스코프 프리셋 하나와, 호출자 한 명."""

    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        role = self.role.value
        return Says(
            f"프로젝트 스코프 프리셋 둘, 도메인 스코프 프리셋 하나와, {role} 한 명",
            english=f"two project-scope presets, one domain-scope preset, and one {role}",
        )

    @override
    async def lay(self, seeding: Any) -> PresetsToFind:
        matching = [await seeding.creating(TestSeedRolePreset()) for _ in range(2)]
        filtered_out = await seeding.creating(TestSeedRolePreset(scope_type=DomainEntityType()))
        caller = await _lay_caller(seeding, self.role, None)
        return PresetsToFind(
            matching=tuple(seeding.made(one) for one in matching),
            filtered_out=seeding.made(filtered_out),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheMatchingPresetPage(Then[PresetsToFind, SearchRolePresetsPayload]):
    """필터에 맞는 것 가운데 정렬상 첫 하나만 한 페이지로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "필터에 맞는 프리셋 가운데 정렬상 첫 하나만 한 페이지로 오고, 나머지 맞는 프리셋과 "
            "필터에 걸리는 프리셋은 오지 않습니다",
            english=(
                "of the presets matching the filter, only the first in the order comes back as "
                "one page, and neither the other matching preset nor the preset the filter "
                "excludes comes back"
            ),
        )

    @override
    def look(
        self, laid: PresetsToFind, answered: Answered[SearchRolePresetsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        first = sorted(laid.matching, key=lambda one: one.name)[0]
        verdicts: list[Verdict] = [Same("items count", len(payload.items), 1)]
        verdicts += preset_read_verdicts("items[0].", payload.items[0], first)
        verdicts += [
            Same("total_count", payload.total_count, len(laid.matching)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        return verdicts


@dataclass(frozen=True)
class PresetEntriesToFind:
    """검색할 프리셋의 항목들, 다른 프리셋의 항목, 그리고 호출자."""

    preset: RolePresetData
    matching: tuple[RolePermissionPresetData, ...]
    filtered_out: RolePermissionPresetData
    outside_preset: RolePermissionPresetData
    caller: UserData


@dataclass(frozen=True)
class PresetEntriesForSearchAndSomeone(Given[Any, PresetEntriesToFind]):
    """권한 항목 여럿을 가진 프리셋 하나, 다른 프리셋 하나와, 호출자 한 명."""

    role: UserRole = UserRole.USER
    granted: Permission | None = Permission.READ

    @override
    def describe(self) -> str:
        role = self.role.value
        if self.granted is None:
            who_ko, who_en = f"{role} 한 명", f"one {role}"
        else:
            who_ko = f"global 에서 {self.granted.name} 권한을 받은 {role} 한 명"
            who_en = f"one {role} granted {self.granted.name} in global"
        return Says(
            f"권한 항목 여럿을 가진 프리셋 하나, 다른 프리셋 하나와, {who_ko}",
            english=f"one preset with several permission entries, another preset, and {who_en}",
        )

    @override
    async def lay(self, seeding: Any) -> PresetEntriesToFind:
        preset = await seeding.creating(TestSeedRolePreset())
        domain_read = await seeding.adding(
            TestSeedRolePresetPermission(DomainEntityType(), Permission.READ), preset
        )
        project_read = await seeding.adding(
            TestSeedRolePresetPermission(ProjectEntityType(), Permission.READ), preset
        )
        project_update = await seeding.adding(
            TestSeedRolePresetPermission(ProjectEntityType(), Permission.UPDATE), preset
        )
        other = await seeding.creating(TestSeedRolePreset())
        outside_preset = await seeding.adding(
            TestSeedRolePresetPermission(ProjectEntityType(), Permission.READ), other
        )
        caller = await _lay_caller(seeding, self.role, self.granted)
        return PresetEntriesToFind(
            preset=seeding.made(preset),
            matching=(seeding.made(domain_read), seeding.made(project_read)),
            filtered_out=seeding.made(project_update),
            outside_preset=seeding.made(outside_preset),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheMatchingEntryPage(Then[PresetEntriesToFind, SearchRolePermissionPresetsPayload]):
    """필터에 맞는 항목 가운데 정렬상 첫 하나만 한 페이지로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "필터에 맞는 항목 가운데 정렬상 첫 하나만 한 페이지로 오고, 나머지 맞는 항목, "
            "필터에 걸리는 항목, 다른 프리셋의 항목은 오지 않습니다",
            english=(
                "of the entries matching the filter, only the first in the order comes back as "
                "one page, and neither the other matching entry, the entry the filter excludes, "
                "nor the entry of the other preset comes back"
            ),
        )

    @override
    def look(
        self, laid: PresetEntriesToFind, answered: Answered[SearchRolePermissionPresetsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        first = sorted(laid.matching, key=lambda one: str(one.entity_type))[0]
        verdicts: list[Verdict] = [Same("items count", len(payload.items), 1)]
        verdicts += permission_read_verdicts("items[0].", payload.items[0], first, laid.preset)
        verdicts += [
            Same("total_count", payload.total_count, len(laid.matching)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        return verdicts
